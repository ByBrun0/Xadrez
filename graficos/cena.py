"""Reúne recursos de desenho sem conhecer as regras dos jogos."""
import math

import numpy as np
from PIL import Image
from OpenGL.GL import *

from configuracao import PLANO, CENTRO_TABULEIRO, CORES_PECAS, BRONZE, QUALIDADES
from . import cenario, pecas, pecas_damas, tabuleiro
from .malhas import Malha, revolucao, esfera, translacao, rotacao, escala
from .mapas import MAPAS, estrelas
from .renderizador import Renderizador
from .painel import dimensoes


class Cena:
    def __init__(self):
        self.gpu=Renderizador()
        self.qualidade=None
        self.grupos={}
        self.modelos={}
        self.imagens={nome:self.gpu.textura(imagem) for nome,imagem in cenario.carregar_imagens().items()}
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
        self.astro=self.gpu.malha(esfera(1,32))
        self.estrelas=self.gpu.malha(estrelas())
        self.painel=self.gpu.textura(Image.new("RGB",(276,800)),False)
        self.definir_qualidade("normal")
        self.definir_qualidade("leve")
        self.definir_qualidade("normal")

    def definir_qualidade(self,qualidade):
        if qualidade not in self.grupos:
            self.grupos[qualidade]={nome:self.gpu.malha(m) for nome,m in cenario.criar(qualidade=="leve").items()}
            segmentos=QUALIDADES[qualidade]
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

    def sombras_contato(self,tab):
        if self.sombras_chave!=tab:
            self.sombras_chave=tab
            conjunto=Malha()
            disco=revolucao(((0,0),(0.29,0)),24)
            for casa,p in enumerate(tab):
                if p!=".":
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
        self.gpu.configurar_mapa(mapa)
        self.gpu.desenhar(self.astro, translacao(*mapa.astro)@escala(mapa.raio_astro),
                         mapa.cor_astro, luz=False)
        if mapa.noite:
            self.gpu.desenhar(self.estrelas, cor=(0.80,0.87,1.0), luz=False)
        for nome,malha in self.grupos[self.qualidade].items():
            cor = (1,1,1)
            if nome=="lampadas" and not mapa.noite:
                cor = (0.54,0.61,0.70)
            self.gpu.desenhar(malha,cor=cor,textura=self.imagens.get(nome,0),
                             luz=nome!="lampadas")
        virada=s.virada
        angulo=s.lado*180
        altura_tab=0
        if virada:
            angulo=virada.lado*180+virada.angulo
            altura_tab=virada.altura
        modelo=translacao(0,CENTRO_TABULEIRO+altura_tab,0)@rotacao(angulo,"x")
        self.gpu.desenhar(self.corpo,modelo,(0.26,0.13,0.065),self.imagens["madeira"])
        self.gpu.desenhar(self.detalhes,modelo,BRONZE)
        self.gpu.desenhar(self.alca,modelo,(0.76,0.51,0.21))
        for lado in (0,1):
            self.gpu.desenhar(self.face,modelo@rotacao(lado*180,"x"),textura=self.faces[lado])

        if virada:
            lado=virada.lado_pecas
            instancias=virada.instancias(s.partidas[lado].posicao.tabuleiro)
        else:
            lado=s.lado
            self.sombras_contato(s.tabuleiro_visual())
            if s.animacao:
                instancias=s.animacao.instancias()
            else:
                instancias=[]
                for casa,p in enumerate(s.tabuleiro_visual()):
                    if p!=".":
                        x,z=tabuleiro.centro(casa)
                        selecionada=casa==(s.passos[-1] if s.passos else s.selecao)
                        y=0.07+0.025*math.sin(tempo*4) if selecionada else 0
                        instancias.append((p,x,y,z,1,0))
            for casa in s.destinos:
                x,z=tabuleiro.centro(casa)
                self.gpu.desenhar(self.disco,translacao(x,PLANO+0.009,z)@escala(0.115),
                                 (0.82,0.65,0.28),luz=False)
            if s.selecao is not None:
                x,z=tabuleiro.centro(s.passos[-1] if s.passos else s.selecao)
                self.gpu.desenhar(self.anel,translacao(x,PLANO+0.012,z),(0.94,0.73,0.29),luz=False)
            if interface.em_xeque:
                rei=s.partida.posicao.tabuleiro.index("R" if s.partida.posicao.turno==1 else "r")
                x,z=tabuleiro.centro(rei)
                self.gpu.desenhar(self.anel,translacao(x,PLANO+0.015,z),(0.92,0.30,0.16),luz=False)
        for p,x,y,z,tamanho,tombo in instancias:
            self.desenhar_peca(p,x,y,z,tamanho,tombo,bool(lado))

        imagem=interface.painel.gerar(interface)
        if imagem:
            self.gpu.atualizar_textura(self.painel,imagem)
        esquerda, painel = interface.painel.limites(janela_x)
        glViewport(round(esquerda*largura/janela_x),0,round(painel*largura/janela_x),altura)
        glDisable(GL_DEPTH_TEST)
        self.gpu.iniciar(np.eye(4),np.eye(4))
        self.gpu.desenhar(self.quad,translacao(-1,-1,0)@escala(2,2,1),textura=self.painel,luz=False)
        glEnable(GL_DEPTH_TEST)

    def liberar(self):
        self.gpu.liberar()


def glfw_window_size(janela):
    import glfw
    return glfw.get_window_size(janela)
