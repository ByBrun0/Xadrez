"""Reúne recursos de desenho sem conhecer as regras dos jogos."""
import math

import numpy as np
from PIL import Image
from OpenGL.GL import *

from configuracao import PLANO, CENTRO_TABULEIRO, CORES_PECAS, BRONZE, perfil_qualidade, nome_qualidade
from . import cenario, pecas, pecas_damas, tabuleiro
from .malhas import Malha, revolucao, esfera, translacao, rotacao, escala
from .mapas import MAPAS, estrelas
from .renderizador import Renderizador
from .painel import dimensoes
from .efeitos import folha, folhas_em_movimento


class Cena:
    def __init__(self):
        self.gpu=Renderizador()
        self.qualidade=None
        self.grupos={}
        self.modelos={}
        self.imagens_originais=cenario.carregar_imagens()
        self.imagens={}
        self.astros={}
        self.estrelas={}
        self.faces=[self.gpu.textura(tabuleiro.textura_face(bool(lado))) for lado in (0,1)]
        corpo,detalhes,face,alca=tabuleiro.criar()
        self.corpo,self.detalhes,self.face,self.alca=[self.gpu.malha(m) for m in (corpo,detalhes,face,alca)]
        self.disco=self.gpu.malha(revolucao(((0,0),(1,0)),32))
        anel=revolucao(((0.40,0),(0.43,0.01),(0.46,0)),32)
        self.anel=self.gpu.malha(anel)
        self.sombras=self.gpu.malha(Malha())
        self.sombras_chave=None
        self.quad=Malha()
        self.quad.quad(((0,0,0),(1,0,0),(1,1,0),(0,1,0)),(0,0,1))
        self.quad=self.gpu.malha(self.quad)
        self.ceus={nome:self.gpu.textura(cenario.ceu(nome),False) for nome in MAPAS}
        self.folha=self.gpu.malha(folha())
        self.tela=self.gpu.textura(Image.new("RGB",(720,540)),False)
        self.painel=self.gpu.textura(Image.new("RGB",(276,800)),False)
        self.faixa=self.gpu.textura(Image.new("RGB",(740,78)),False)
        self.aviso_turno=self.gpu.textura(Image.new("RGB",(440,38)),False)
        self.aviso_chave=None
        self.definir_qualidade("normal")
        self.definir_qualidade("baixa")
        self.definir_qualidade("normal")
        for imagem in self.imagens_originais.values():
            imagem.close()
        self.imagens_originais.clear()

    def definir_qualidade(self,qualidade):
        qualidade=nome_qualidade(qualidade)
        perfil=perfil_qualidade(qualidade)
        if qualidade not in self.grupos:
            self.grupos[qualidade]={nome:self.gpu.malha(m) for nome,m in cenario.criar(qualidade=="baixa").items()}
            self.astros[qualidade]=self.gpu.malha(esfera(1,perfil.segmentos_astro))
            self.estrelas[qualidade]=self.gpu.malha(estrelas(perfil.estrelas))
            self.imagens[qualidade]={}
            for nome,imagem in self.imagens_originais.items():
                reduzida=imagem.copy()
                reduzida.thumbnail((perfil.limite_textura,perfil.limite_textura),Image.Resampling.LANCZOS)
                self.imagens[qualidade][nome]=self.gpu.textura(reduzida)
            segmentos=perfil.segmentos_pecas
            self.modelos[qualidade]=[]
            for gerador in (pecas.criar_modelos,pecas_damas.criar_modelos):
                modelos={}
                for tipo,malhas in gerador(segmentos).items():
                    for lado in (0,1):
                        unida=Malha()
                        for malha,cor in zip(malhas,(CORES_PECAS[lado],BRONZE,(0.045,0.035,0.02))):
                            unida.juntar(malha,cor=cor)
                        modelos[tipo.lower() if lado else tipo]=self.gpu.malha(unida)
                self.modelos[qualidade].append(modelos)
        self.qualidade=qualidade

    def desenhar_peca(self,p,x,y,z,tamanho=1,tombo=0,damas=False):
        if tamanho<0.005:
            return
        base=translacao(x,PLANO+y,z) @ escala(tamanho) @ rotacao(tombo,"z")
        if p.islower():
            base=base@rotacao(180)
        if not damas and p.upper() in "CB":
            base=base@rotacao(90)
        modelo=self.modelos[self.qualidade][int(damas)][p]
        self.gpu.desenhar(modelo,base)

    def sombras_contato(self,tab,omitida=None):
        chave=(tab,omitida)
        if self.sombras_chave!=chave:
            self.sombras_chave=chave
            conjunto=Malha()
            disco=revolucao(((0,0),(0.29,0)),24)
            for casa,p in enumerate(tab):
                if p!="." and casa!=omitida:
                    x,z=tabuleiro.centro(casa)
                    conjunto.juntar(disco,translacao(x,PLANO+0.004,z))
            self.sombras=self.gpu.substituir_malha(self.sombras,conjunto)
        self.gpu.desenhar(self.sombras,cor=(0.19,0.15,0.11),luz=False)

    def desenhar(self,largura,altura,interface,tempo):
        janela_x,janela_y=glfw_window_size(interface.janela)
        cena_logica,_=dimensoes(janela_x)
        cena_x=round(largura*cena_logica/janela_x)
        s=interface.sessao
        camera=interface.camera
        self.definir_qualidade(interface.qualidade)
        perfil=perfil_qualidade(interface.qualidade)
        pulsacao=1+0.035*math.sin(tempo*0.8) if perfil.pulsacao_luzes else 1
        glViewport(0,0,cena_x,altura)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)
        self.gpu.iniciar(np.eye(4),np.eye(4))
        mapa = MAPAS[interface.mapa]
        self.gpu.desenhar(self.quad,translacao(-1,-1,0)@escala(2,2,1),
                         textura=self.ceus[interface.mapa],luz=False)
        glEnable(GL_DEPTH_TEST)
        glViewport(0,0,cena_x,altura)
        self.gpu.iniciar(*camera.matrizes(cena_x/altura,PLANO))
        self.gpu.configurar_mapa(mapa,perfil,pulsacao)
        self.gpu.desenhar(self.astros[self.qualidade], translacao(*mapa.astro)@escala(mapa.raio_astro),
                         mapa.cor_astro, luz=False)
        if mapa.noite:
            self.gpu.desenhar(self.estrelas[self.qualidade], cor=(0.80,0.87,1.0), luz=False)
        for nome,malha in self.grupos[self.qualidade].items():
            cor = (1,1,1)
            if nome=="lampadas" and not mapa.noite:
                cor = (0.54,0.61,0.70)
            elif nome=="lampadas":
                cor=(pulsacao,pulsacao,pulsacao)
            vento=0.055*math.sin(tempo*0.75) if perfil.vento and nome=="copas" else 0
            self.gpu.desenhar(malha,cor=cor,textura=self.imagens[self.qualidade].get(nome,0),
                             luz=nome!="lampadas",vento=vento)
        for matriz in folhas_em_movimento(tempo,perfil.folhas):
            self.gpu.desenhar(self.folha,matriz,(0.63,0.38,0.13))
        virada=s.virada
        angulo=s.lado*180
        altura_tab=0
        if virada:
            angulo=virada.lado*180+virada.angulo
            altura_tab=virada.altura
        modelo=translacao(0,CENTRO_TABULEIRO+altura_tab,0)@rotacao(angulo,"x")
        self.gpu.desenhar(self.corpo,modelo,(0.26,0.13,0.065),self.imagens[self.qualidade]["madeira"])
        self.gpu.desenhar(self.detalhes,modelo,BRONZE)
        self.gpu.desenhar(self.alca,modelo,(0.76,0.51,0.21))
        for lado in (0,1):
            self.gpu.desenhar(self.face,modelo@rotacao(lado*180,"x"),textura=self.faces[lado])

        if virada:
            lado=virada.lado_pecas
            instancias=virada.instancias(s.partidas[lado].posicao.tabuleiro)
        else:
            lado=s.lado
            arraste=interface.arraste
            visual=arraste if arraste and arraste.visivel else interface.promocao_visual
            if perfil.sombras_contato:
                self.sombras_contato(s.tabuleiro_visual(),visual.casa if visual else None)
            if s.animacao:
                instancias=s.animacao.instancias()
            else:
                instancias=[]
                for casa,p in enumerate(s.tabuleiro_visual()):
                    if p!="." and (visual is None or casa!=visual.casa):
                        x,z=tabuleiro.centro(casa)
                        selecionada=casa==(s.passos[-1] if s.passos else s.selecao)
                        y=0
                        if selecionada:
                            y=0.07+(0.025*math.sin(tempo*4) if perfil.levitacao else 0)
                        instancias.append((p,x,y,z,1,0))
                if visual:
                    instancias.append((visual.peca,visual.x,visual.altura,visual.z,1,0))
                    if perfil.sombras_contato:
                        self.gpu.desenhar(self.disco,
                                         translacao(visual.x,PLANO+0.006,visual.z)@escala(0.32),
                                         (0.15,0.13,0.10),luz=False)
                    casa=tabuleiro.casa_em(visual.x,visual.z)
                    if casa is not None and not visual.retornando:
                        x,z=tabuleiro.centro(casa)
                        cor=(0.37,0.81,0.48) if casa in s.destinos else (0.88,0.32,0.23)
                        self.gpu.desenhar(self.anel,translacao(x,PLANO+0.016,z),cor,luz=False)
            for casa in s.destinos:
                x,z=tabuleiro.centro(casa)
                if interface.destino_captura(casa):
                    self.gpu.desenhar(self.anel,translacao(x,PLANO+0.009,z)@escala(0.57),
                                     (0.91,0.43,0.25),luz=False)
                else:
                    self.gpu.desenhar(self.disco,translacao(x,PLANO+0.009,z)@escala(0.115),
                                     (0.82,0.65,0.28),luz=False)
            if interface.casa_sobre is not None and not visual:
                x,z=tabuleiro.centro(interface.casa_sobre)
                self.gpu.desenhar(self.anel,translacao(x,PLANO+0.011,z),
                                 (0.65,0.72,0.64),luz=False)
            if s.selecao is not None:
                x,z=tabuleiro.centro(s.passos[-1] if s.passos else s.selecao)
                self.gpu.desenhar(self.anel,translacao(x,PLANO+0.012,z),(0.94,0.73,0.29),luz=False)
            if interface.em_xeque:
                rei=s.partida.posicao.tabuleiro.index("R" if s.partida.posicao.turno==1 else "r")
                x,z=tabuleiro.centro(rei)
                self.gpu.desenhar(self.anel,translacao(x,PLANO+0.015,z),(0.92,0.30,0.16),luz=False)
            apresentacao=interface.apresentacao
            if (s.partida.resultado and apresentacao.casa_resultado is not None
                    and apresentacao.lado_resultado==s.lado):
                x,z=tabuleiro.centro(apresentacao.casa_resultado)
                tamanho=1+0.08*math.sin(tempo*3) if perfil.levitacao else 1
                self.gpu.desenhar(self.anel,translacao(x,PLANO+0.022,z)@escala(tamanho),
                                 (0.96,0.66,0.24),luz=False)
        for p,x,y,z,tamanho,tombo in instancias:
            self.desenhar_peca(p,x,y,z,tamanho,tombo,bool(lado))

        if interface.apresentacao.modal:
            self.desenhar_tela(largura,altura,janela_x,janela_y,interface)
            return
        self.desenhar_informacoes(largura,altura,janela_x,janela_y,interface)
        if interface.apresentacao.modo in ("introducao","resultado"):
            return
        imagem=interface.painel.gerar(interface)
        if imagem:
            self.gpu.atualizar_textura(self.painel,imagem)
        esquerda, painel = interface.painel.limites(janela_x)
        glViewport(round(esquerda*largura/janela_x),0,round(painel*largura/janela_x),altura)
        glDisable(GL_DEPTH_TEST)
        self.gpu.iniciar(np.eye(4),np.eye(4))
        self.gpu.desenhar(self.quad,translacao(-1,-1,0)@escala(2,2,1),textura=self.painel,luz=False)
        glEnable(GL_DEPTH_TEST)

    def desenhar_tela(self,largura,altura,janela_x,janela_y,interface):
        imagem=interface.telas.gerar(interface)
        if imagem is not None:
            self.gpu.atualizar_textura(self.tela,imagem)
        x,y,w,h=interface.telas.retangulo(janela_x,janela_y)
        glViewport(round(x*largura/janela_x),round((janela_y-y-h)*altura/janela_y),
                   round(w*largura/janela_x),round(h*altura/janela_y))
        glDisable(GL_DEPTH_TEST)
        self.gpu.iniciar(np.eye(4),np.eye(4))
        self.gpu.desenhar(self.quad,translacao(-1,-1,0)@escala(2,2,1),textura=self.tela,luz=False)
        glEnable(GL_DEPTH_TEST)

    def desenhar_informacoes(self,largura,altura,janela_x,janela_y,interface):
        info=interface.informacoes
        imagem=info.gerar(interface,janela_x)
        if imagem is not None:
            self.gpu.atualizar_textura(self.faixa,imagem)
        x,y,comprimento,altura_faixa=info.retangulo(janela_x)
        fator_x,fator_y=largura/janela_x,altura/janela_y
        glDisable(GL_DEPTH_TEST)
        self.gpu.iniciar(np.eye(4),np.eye(4))
        glViewport(round(x*fator_x),round((janela_y-y-altura_faixa)*fator_y),
                   round(comprimento*fator_x),round(altura_faixa*fator_y))
        modelo=translacao(-1,-1,0)@escala(2,2,1)
        self.gpu.desenhar(self.quad,modelo,textura=self.faixa,luz=False)
        if info.tempo_aviso>0:
            if self.aviso_chave!=info.aviso:
                self.aviso_chave=info.aviso
                self.gpu.atualizar_textura(self.aviso_turno,info.imagem_aviso())
            topo=100+info.deslocamento_aviso
            glViewport(round(x*fator_x),round((janela_y-topo-38)*fator_y),
                       round(min(comprimento,440)*fator_x),round(38*fator_y))
            abertura=info.abertura_aviso
            modelo_aviso=translacao(-1,1-2*abertura,0)@escala(2,2*abertura,1)
            self.gpu.desenhar(self.quad,modelo_aviso,textura=self.aviso_turno,luz=False)
        glEnable(GL_DEPTH_TEST)

    def liberar(self):
        self.gpu.liberar()


def glfw_window_size(janela):
    import glfw
    return glfw.get_window_size(janela)
