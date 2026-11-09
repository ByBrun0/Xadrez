"""Eventos de mouse/teclado e comandos do painel."""
import math

import glfw

from configuracao import PLANO
from graficos.camera import Camera
from graficos.painel import Painel, dimensoes
from graficos import tabuleiro
from sessao import Sessao
from xadrez import regras


class Interface:
    def __init__(self,janela,camera):
        self.janela=janela
        self.camera=camera
        self.sessao=Sessao()
        self.painel=Painel()
        self.confirmacao=None
        self.ajuda=False
        self.giro_automatico=True
        self.qualidade="normal"
        self.metricas=""
        self.cursor=glfw.get_cursor_pos(janela)
        self.inicio_arraste=None
        self.vistas=[camera.guardar(),camera.guardar()]
        self._xeque_posicao=None
        self._xeque=False
        self.titulo=""
        glfw.set_mouse_button_callback(janela,self.mouse)
        glfw.set_cursor_pos_callback(janela,self.mover)
        glfw.set_scroll_callback(janela,self.rolar)
        glfw.set_key_callback(janela,self.tecla)

    @property
    def em_xeque(self):
        if self.sessao.lado:
            return False
        posicao=self.sessao.partida.posicao
        if posicao!=self._xeque_posicao:
            self._xeque_posicao=posicao
            self._xeque=regras.em_xeque(posicao)
        return self._xeque

    def atualizar(self,dt):
        virando=self.sessao.virada is not None
        if self.sessao.atualizar(dt) and self.giro_automatico:
            self.camera.girar_turno()
        if virando and not self.sessao.virada:
            self.camera.recuperar(self.vistas[self.sessao.lado])
        abertura=self.sessao.virada.abertura if self.sessao.virada else 0
        self.camera.abertura+=(abertura-self.camera.abertura)*(1-math.exp(-10*dt))
        self.camera.atualizar(dt)
        if not self.sessao.lado and not self.sessao.bloqueada:
            self.sessao.partida.verificar_posicao_morta()
        jogo="Damas" if self.sessao.lado else "Xadrez"
        titulo="Praça dos Dois Jogos · "+jogo
        if titulo!=self.titulo:
            glfw.set_window_title(self.janela,titulo)
            self.titulo=titulo

    def virar(self,manual=False):
        if self.camera.restante or self.confirmacao:
            return False
        self.vistas[self.sessao.lado]=self.camera.guardar()
        return self.sessao.virar(manual)

    def mover(self,janela,x,y):
        if self.inicio_arraste is not None and self.sessao.virada:
            self.sessao.virada.arrastar(y-self.inicio_arraste)
        elif not self.sessao.virada and glfw.get_mouse_button(janela,glfw.MOUSE_BUTTON_RIGHT)==glfw.PRESS:
            self.camera.orbitar(x-self.cursor[0],y-self.cursor[1])
        self.cursor=x,y

    def rolar(self,janela,x,y):
        if not self.sessao.virada:
            self.camera.zoom(y)

    def mouse(self,janela,botao,acao,mods):
        if botao!=glfw.MOUSE_BUTTON_LEFT:
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
        self.painel.gerar(self)
        comando=self.painel.clicar(x,y,largura,altura)
        if comando:
            self.comando(comando)
            return
        if self.sessao.bloqueada or self.camera.restante or self.confirmacao or self.sessao.promocao:
            return
        cena,_=dimensoes(largura)
        fb_x,fb_y=glfw.get_framebuffer_size(janela)
        if not fb_y:
            return
        aspecto=round(fb_x*cena/largura)/fb_y
        ponto=self.camera.ponto_no_plano(x,y,cena,altura,aspecto,PLANO)
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

    def comando(self,codigo):
        s=self.sessao
        if codigo=="ajuda":
            self.ajuda=not self.ajuda
            return
        if self.confirmacao or s.bloqueada or self.camera.restante:
            return
        if s.promocao:
            for lance in s.promocao:
                if lance.promocao==codigo:
                    s.executar(lance)
                    return
            return
        if codigo=="camera":
            self.camera.restaurar(s.partida.posicao.turno)
        elif codigo=="giro":
            self.giro_automatico=not self.giro_automatico
        elif codigo=="qualidade":
            self.qualidade="leve" if self.qualidade=="normal" else "normal"
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

    def tecla(self,janela,tecla,scancode,acao,mods):
        if acao!=glfw.PRESS:
            return
        s=self.sessao
        if tecla==glfw.KEY_ESCAPE:
            if s.virada and s.virada.manual and not s.virada.solta:
                s.virada.progresso_arraste=0
                s.virada.soltar()
                self.inicio_arraste=None
            elif not s.bloqueada:
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
                  glfw.KEY_HOME:"camera",glfw.KEY_G:"giro",glfw.KEY_Q:"qualidade"}
        if tecla in comandos:
            self.comando(comandos[tecla])
