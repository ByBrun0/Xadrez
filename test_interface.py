"""Integração em janela oculta, por callbacks reais e projeção da cena."""
import glfw
import numpy as np

from graficos.camera import Camera
from graficos.cena import Cena
from graficos.painel import dimensoes
from graficos.tabuleiro import PLANO, centro, casa_em
from interface import Interface
from main import criar_janela
from test_xadrez import casa
from test_damas import Partida, posicao


def avancar(ui):
    for _ in range(400):
        ui.atualizar(0.02)
        if not ui.sessao.bloqueada and not ui.camera.restante:
            return
    raise AssertionError("Transição não terminou")


def ponto_tela(ui,x,z):
    largura,altura=glfw.get_window_size(ui.janela)
    cena,_=dimensoes(largura)
    fb_x,fb_y=glfw.get_framebuffer_size(ui.janela)
    p,v=ui.camera.matrizes(round(fb_x*cena/largura)/fb_y,PLANO)
    clip=p@v@[x,PLANO,z,1]
    nx,ny=clip[:2]/clip[3]
    return (nx+1)*cena/2,(1-ny)*altura/2


def clicar(ui,x,y):
    ui.mover(ui.janela,x,y)
    ui.mouse(ui.janela,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
    ui.mouse(ui.janela,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)


def clicar_casa(ui,nome):
    indice=casa(nome) if isinstance(nome,str) else nome
    clicar(ui,*ponto_tela(ui,*centro(indice)))


def testar():
    janela=criar_janela(False)
    cena=None
    try:
        ui=Interface(janela,Camera())
        cena=Cena()
        # Todas as casas nos dois ângulos e em duas proporções de janela.
        for largura,altura in ((1100,800),(1000,650)):
            glfw.set_window_size(janela,largura,altura)
            glfw.poll_events()
            cena_x,_=dimensoes(largura)
            fb_x,fb_y=glfw.get_framebuffer_size(janela)
            for lado in (1,-1):
                ui.camera.restaurar(lado)
                for _ in range(50): ui.camera.atualizar(.02)
                for indice in range(64):
                    x,y=ponto_tela(ui,*centro(indice))
                    ponto=ui.camera.ponto_no_plano(x,y,cena_x,altura,
                                                   round(fb_x*cena_x/largura)/fb_y,PLANO)
                    assert casa_em(ponto[0],ponto[2])==indice
        glfw.set_window_size(janela,1100,800)
        glfw.poll_events()
        ui.camera.restaurar()
        ui.giro_automatico=True
        for origem,destino in (("f2","f3"),("e7","e5"),("g2","g4"),("d8","h4")):
            clicar_casa(ui,origem)
            assert ui.sessao.selecao==casa(origem)
            clicar_casa(ui,destino)
            assert ui.sessao.animacao
            # Uma tentativa de virar no meio do movimento deve ser ignorada.
            ui.tecla(janela,glfw.KEY_V,0,glfw.PRESS,0)
            assert ui.sessao.virada is None
            cena.desenhar(*glfw.get_framebuffer_size(janela),ui,0)
            avancar(ui)
        assert "xeque-mate" in ui.sessao.partida.resultado

        # Botão do painel passa para damas e preserva o mate do xadrez.
        ui.painel.gerar(ui)
        largura,altura=glfw.get_window_size(janela)
        cena_x,painel=dimensoes(largura)
        clicar(ui,cena_x+painel/2,298*altura/800)
        assert ui.sessao.virada
        avancar(ui)
        assert ui.sessao.lado==1
        assert "xeque-mate" in ui.sessao.partidas[0].resultado

        # Completar uma partida de damas, escolhendo as rotas pela interface.
        partidas=0
        while not ui.sessao.partida.resultado and partidas<300:
            lances=ui.sessao.partida.lances()
            lance=lances[(partidas*17)%len(lances)]
            clicar_casa(ui,lance.origem)
            for pouso in lance.pousos:
                clicar_casa(ui,pouso)
                cena.desenhar(*glfw.get_framebuffer_size(janela),ui,partidas)
                avancar(ui)
            partidas+=1
        assert ui.sessao.partida.resultado, "Partida de damas não terminou"
        print("Damas pela interface",partidas,ui.sessao.partida.resultado)

        estado_xadrez=ui.sessao.partidas[0].posicao
        ui.comando("novo")
        ui.tecla(janela,glfw.KEY_ENTER,0,glfw.PRESS,0)
        assert not ui.sessao.partida.historico
        assert ui.sessao.partidas[0].posicao==estado_xadrez

        # Alça, arraste e cancelamento antes da metade.
        clicar(ui,*ponto_tela(ui,4.99,-3))
        avancar(ui)
        assert ui.sessao.lado==1
        x,y=ponto_tela(ui,4.99,-3)
        ui.mover(janela,x,y)
        ui.mouse(janela,glfw.MOUSE_BUTTON_LEFT,glfw.PRESS,0)
        assert ui.sessao.virada and ui.sessao.virada.manual
        ui.mover(janela,x,y-220)
        ui.mouse(janela,glfw.MOUSE_BUTTON_LEFT,glfw.RELEASE,0)
        avancar(ui)
        assert ui.sessao.lado==0

        # Promoção via quatro opções visuais.
        from xadrez.partida import Partida as Xadrez
        from test_xadrez import posicao as posicao_xadrez
        ui.sessao.partidas[0]=Xadrez(posicao_xadrez({"e1":"R","a7":"P","e8":"r"}))
        ui.camera.restaurar()
        clicar_casa(ui,"a7")
        clicar_casa(ui,"a8")
        assert len(ui.sessao.promocao)==4
        ui.painel.gerar(ui)
        ui.comando("C")
        avancar(ui)
        assert ui.sessao.partida.posicao.tabuleiro[casa("a8")]=="C"
        assert not ui.sessao.promocao
        print("Seleção, painel, animações, virada, reinício e promoção passaram.")
    finally:
        if cena:
            cena.liberar()
        glfw.terminate()


if __name__=="__main__":
    testar()
