"""Eventos de mouse/teclado e comandos do painel."""
import math

import glfw

from configuracao import PLANO, NOMES_PECAS
from apresentacao import Apresentacao
from graficos.painel import Painel
from graficos import tabuleiro
from graficos.informacoes import Informacoes
from graficos.telas import Telas
from interacao import ArrastePeca
from sessao import Sessao
from xadrez import regras


class Interface:
    def __init__(self,janela,camera,apresentar=False):
        self.janela=janela
        self.camera=camera
        self.sessao=Sessao()
        self.painel=Painel()
        self.informacoes=Informacoes()
        self.arraste=None
        self.promocao_visual=None
        self.confirmacao=None
        self.ajuda=False
        self.giro_automatico=True
        self.qualidade="normal"
        self.mapa="dia"
        self.metricas=""
        self.cursor=glfw.get_cursor_pos(janela)
        self.inicio_arraste=None
        self.vistas=[camera.guardar(),camera.guardar()]
        self.apresentacao=Apresentacao(camera,apresentar)
        self.telas=Telas()
        self.casa_sobre=None
        self._xeque_posicao=None
        self._xeque=False
        self.titulo=""
        glfw.set_mouse_button_callback(janela,self.mouse)
        glfw.set_cursor_pos_callback(janela,self.mover)
        glfw.set_scroll_callback(janela,self.rolar)
        glfw.set_key_callback(janela,self.tecla)
        glfw.set_window_focus_callback(janela,self.foco)

    @property
    def ocupada(self):
        return (self.sessao.bloqueada or self.arraste is not None
                or self.apresentacao.modo in ("menu","introducao","resultado"))

    @property
    def em_xeque(self):
        if self.sessao.lado:
            return False
        posicao=self.sessao.partida.posicao
        if posicao!=self._xeque_posicao:
            self._xeque_posicao=posicao
            self._xeque=regras.em_xeque(posicao)
        return self._xeque

    @property
    def descricao_sobre(self):
        if self.casa_sobre is None:
            return ""
        peca=self.sessao.tabuleiro_visual()[self.casa_sobre]
        if peca==".":
            return ""
        nome="Pedra" if self.sessao.lado and peca.upper()=="P" else NOMES_PECAS[peca.upper()]
        return nome+" · "+("brancas" if peca.isupper() else "pretas")

    def destino_captura(self,casa):
        s=self.sessao
        if casa not in s.destinos:
            return False
        if s.lado:
            return any(l.capturadas and l.pousos[len(s.passos)]==casa for l in s.opcoes)
        posicao=s.partida.posicao
        return (posicao.tabuleiro[casa]!="." or
                (s.selecao is not None and posicao.tabuleiro[s.selecao].upper()=="P"
                 and posicao.passagem==casa))

    def atualizar(self,dt):
        largura, altura = glfw.get_window_size(self.janela)
        if self.arraste:
            self.arraste.mover(self.cursor,self.ponto_cursor())
            if self.arraste.atualizar(dt):
                self.arraste=None
        else:
            self.painel.atualizar(dt, self.cursor, largura, altura,
                                  bool(self.sessao.promocao or self.confirmacao or self.ajuda))
        virando=self.sessao.virada is not None
        if (self.sessao.atualizar(dt) and self.giro_automatico
                and not self.sessao.partida.resultado):
            self.camera.girar_turno()
        if virando and not self.sessao.virada:
            self.camera.recuperar(self.vistas[self.sessao.lado])
        abertura=self.sessao.virada.abertura if self.sessao.virada else 0
        self.camera.abertura+=(abertura-self.camera.abertura)*(1-math.exp(-10*dt))
        self.camera.atualizar(dt)
        modo_anterior=self.apresentacao.modo
        self.apresentacao.atualizar(dt,self)
        if modo_anterior=="introducao" and self.apresentacao.modo=="jogo":
            self.vistas[self.sessao.lado]=self.camera.guardar()
        self.casa_sobre=None
        if self.apresentacao.permite_jogar and not self.ocupada and not self.sobre_interface():
            ponto=self.ponto_cursor()
            if ponto is not None:
                self.casa_sobre=tabuleiro.casa_em(ponto[0],ponto[2])
        if not self.sessao.lado and not self.ocupada:
            self.sessao.partida.verificar_posicao_morta()
        if self.apresentacao.modo!="menu":
            self.informacoes.atualizar(dt, self)
        jogo="Damas" if self.sessao.lado else "Xadrez"
        titulo="Praça dos Dois Jogos · "+jogo
        if titulo!=self.titulo:
            glfw.set_window_title(self.janela,titulo)
            self.titulo=titulo

    def virar(self,manual=False):
        if (self.camera.restante or self.confirmacao or self.arraste
                or not self.apresentacao.permite_jogar):
            return False
        self.vistas[self.sessao.lado]=self.camera.guardar()
        return self.sessao.virar(manual)

    def mover(self,janela,x,y):
        if self.apresentacao.modo not in ("jogo","contemplacao"):
            self.cursor=x,y
            return
        if self.arraste:
            self.arraste.mover((x,y),self.ponto_cursor((x,y)))
        elif self.inicio_arraste is not None and self.sessao.virada:
            self.sessao.virada.arrastar(y-self.inicio_arraste)
        elif not self.sessao.virada and glfw.get_mouse_button(janela,glfw.MOUSE_BUTTON_RIGHT)==glfw.PRESS:
            self.camera.orbitar(x-self.cursor[0],y-self.cursor[1])
        self.cursor=x,y

    def rolar(self,janela,x,y):
        if (not self.sessao.virada and not self.arraste
                and self.apresentacao.modo in ("jogo","contemplacao")):
            self.camera.zoom(y)

    def ponto_cursor(self, cursor=None):
        largura, altura=glfw.get_window_size(self.janela)
        fb_x, fb_y=glfw.get_framebuffer_size(self.janela)
        x,y=self.cursor if cursor is None else cursor
        if min(largura,altura,fb_x,fb_y)<=0:
            return None
        if not (0<=x<largura and 0<=y<altura):
            return None
        return self.camera.ponto_no_plano(x,y,largura,altura,fb_x/fb_y,PLANO)

    def sobre_interface(self):
        largura,altura=glfw.get_window_size(self.janela)
        x,y=self.cursor
        if not self.apresentacao.permite_jogar:
            return True
        return (self.informacoes.contem(x,y,largura) or
                self.painel.clicar(x,y,largura,altura) is not None)

    def soltar_peca(self):
        arraste=self.arraste
        if arraste.retornando:
            return
        self.arraste=None
        if not arraste.ativo:
            return
        ponto=self.ponto_cursor()
        arraste.mover(self.cursor,ponto)
        casa=tabuleiro.casa_em(arraste.x,arraste.z)
        if (ponto is not None and not self.sobre_interface()
                and casa in self.sessao.destinos and not self.sessao.partida.resultado):
            reivindicando=self.sessao.reivindicacao
            self.sessao.selecionar(casa)
            if reivindicando:
                if not self.sessao.partida.resultado:
                    self.arraste=arraste
                    arraste.devolver()
                return
            if self.sessao.animacao:
                self.sessao.animacao.inicio_visual=arraste.posicao
                return
            if self.sessao.promocao:
                arraste.x,arraste.z=tabuleiro.centro(casa)
                self.promocao_visual=arraste
                return
            if self.sessao.partida.resultado:
                return
        self.arraste=arraste
        arraste.devolver()
        self.sessao.aviso="Destino inválido. Escolha uma casa marcada."

    def foco(self,janela,focada):
        if not focada and self.arraste:
            if self.arraste.visivel:
                self.arraste.devolver()
            else:
                self.arraste=None

    def mouse(self,janela,botao,acao,mods):
        if botao!=glfw.MOUSE_BUTTON_LEFT:
            return
        if acao==glfw.RELEASE and self.arraste:
            self.soltar_peca()
            return
        if acao==glfw.RELEASE and self.inicio_arraste is not None:
            if self.sessao.virada:
                self.sessao.virada.soltar()
            self.inicio_arraste=None
            return
        if acao!=glfw.PRESS:
            return
        largura,altura=glfw.get_window_size(janela)
        if not altura:
            return
        x,y=self.cursor
        if self.apresentacao.modal:
            self.telas.gerar(self)
            codigo=self.telas.clicar(x,y,largura,altura)
            if codigo:
                self.comando_tela(codigo)
            return
        if self.apresentacao.modo in ("introducao","resultado"):
            return
        self.painel.gerar(self)
        comando=self.painel.clicar(x,y,largura,altura)
        if comando:
            self.comando(comando)
            return
        if self.informacoes.contem(x,y,largura):
            return
        if not self.apresentacao.permite_jogar:
            return
        if self.ocupada or self.camera.restante or self.confirmacao or self.sessao.promocao:
            return
        ponto=self.ponto_cursor()
        if ponto is None:
            return
        # A margem é maior que a alça para tornar o gesto confortável.
        if 4.50<=ponto[0]<=5.45 and abs(abs(ponto[2])-3)<1.0:
            if self.virar(True):
                self.inicio_arraste=y
            return
        casa=tabuleiro.casa_em(ponto[0],ponto[2])
        if casa is not None:
            self.sessao.selecionar(casa)
            atual=self.sessao.passos[-1] if self.sessao.passos else self.sessao.selecao
            if (not self.sessao.bloqueada and casa==atual and not self.sessao.promocao
                    and not self.sessao.partida.resultado):
                peca=self.sessao.tabuleiro_visual()[casa]
                self.arraste=ArrastePeca(casa,peca,(x,y),ponto)

    def comando(self,codigo):
        s=self.sessao
        if self.apresentacao.modo=="menu":
            self.comando_tela(codigo)
            return
        if self.apresentacao.modo=="resultado":
            acao={"novo":"revanche","virar":"outro_jogo","contemplar":"observar"}.get(codigo)
            if acao and self.apresentacao.modal:
                self.comando_tela(acao)
            return
        if self.apresentacao.modo=="contemplacao" and codigo not in (
                "contemplar","camera","mapa","qualidade","ajuda"):
            return
        if self.arraste:
            return
        if codigo=="ajuda":
            self.ajuda=not self.ajuda
            return
        if self.confirmacao or s.bloqueada or self.camera.restante:
            return
        if s.promocao:
            for lance in s.promocao:
                if lance.promocao==codigo:
                    s.executar(lance)
                    if self.promocao_visual and s.animacao:
                        s.animacao.inicio_visual=self.promocao_visual.posicao
                    self.promocao_visual=None
                    return
            return
        if codigo=="camera":
            self.camera.restaurar(s.partida.posicao.turno)
        elif codigo=="giro":
            self.giro_automatico=not self.giro_automatico
        elif codigo=="qualidade":
            self.qualidade="baixa" if self.qualidade=="normal" else "normal"
        elif codigo=="mapa":
            self.mapa="noite" if self.mapa=="dia" else "dia"
        elif codigo=="contemplar" and not s.passos:
            self.apresentacao.contemplar(self)
        elif not s.passos:
            if codigo=="virar":
                self.virar()
            elif codigo=="novo":
                self.confirmacao="Nova partida"
            elif not s.partida.resultado:
                if codigo=="abandono":
                    self.confirmacao="Abandonar partida"
                elif codigo=="empate":
                    aceitou=s.partida.oferecer_ou_aceitar()
                    if aceitou is False:
                        s.aviso="Nas damas, a oferta exige 20 lances de cada lado e alternância entre ofertas."
                elif codigo=="reivindicar" and not s.lado:
                    s.reivindicacao=not s.partida.reivindicar()

    def comando_tela(self,codigo):
        if self.apresentacao.modo=="menu":
            if codigo in ("escolher_dia","escolher_noite"):
                self.mapa=codigo.removeprefix("escolher_")
            elif codigo=="mapa":
                self.mapa="noite" if self.mapa=="dia" else "dia"
            elif codigo=="qualidade":
                self.qualidade="baixa" if self.qualidade=="normal" else "normal"
            elif codigo in ("iniciar_xadrez","iniciar_damas"):
                self.apresentacao.iniciar(self,int(codigo=="iniciar_damas"))
        elif self.apresentacao.modo=="resultado":
            if codigo=="revanche":
                self.sessao.reiniciar()
                self.apresentacao.iniciar(self,self.sessao.lado)
            elif codigo=="outro_jogo":
                self.apresentacao.dispensar_resultado()
                self.virar()
            elif codigo=="observar":
                self.apresentacao.dispensar_resultado()

    def tecla(self,janela,tecla,scancode,acao,mods):
        if acao!=glfw.PRESS:
            return
        s=self.sessao
        if self.apresentacao.modo=="menu":
            codigos={glfw.KEY_X:"iniciar_xadrez",glfw.KEY_ENTER:"iniciar_xadrez",
                     glfw.KEY_D:"iniciar_damas",glfw.KEY_M:"mapa",glfw.KEY_Q:"qualidade"}
            if tecla in codigos:
                self.comando_tela(codigos[tecla])
            return
        if self.apresentacao.modo=="introducao":
            if tecla==glfw.KEY_ESCAPE:
                self.apresentacao.tempo=self.apresentacao.duracao
                self.apresentacao.atualizar(0,self)
            return
        if self.apresentacao.modo=="resultado":
            if self.apresentacao.modal:
                codigos={glfw.KEY_ENTER:"revanche",glfw.KEY_V:"outro_jogo",glfw.KEY_ESCAPE:"observar"}
                if tecla in codigos:
                    self.comando_tela(codigos[tecla])
            return
        if self.apresentacao.modo=="contemplacao" and tecla==glfw.KEY_ESCAPE:
            self.apresentacao.contemplar(self)
            return
        if tecla==glfw.KEY_ESCAPE:
            if self.arraste:
                self.foco(janela,False)
            elif s.virada and s.virada.manual and not s.virada.solta:
                s.virada.progresso_arraste=0
                s.virada.soltar()
                self.inicio_arraste=None
            elif not s.bloqueada:
                if self.promocao_visual:
                    self.arraste=self.promocao_visual
                    self.promocao_visual=None
                    self.arraste.devolver()
                self.confirmacao=None
                self.ajuda=False
                s.aviso=""
                if not s.passos:
                    s.limpar()
            return
        if self.confirmacao:
            if tecla==glfw.KEY_ENTER:
                if self.confirmacao=="Nova partida":
                    s.reiniciar()
                    self.camera.restaurar()
                else:
                    s.partida.abandonar()
                self.confirmacao=None
            return
        if s.promocao and 65<=tecla<=90:
            self.comando(chr(tecla))
            return
        comandos={glfw.KEY_V:"virar",glfw.KEY_N:"novo",glfw.KEY_E:"empate",
                  glfw.KEY_X:"abandono",glfw.KEY_R:"reivindicar",glfw.KEY_H:"ajuda",
                  glfw.KEY_HOME:"camera",glfw.KEY_G:"giro",glfw.KEY_Q:"qualidade",
                  glfw.KEY_M:"mapa",glfw.KEY_C:"contemplar"}
        if tecla in comandos:
            self.comando(comandos[tecla])
