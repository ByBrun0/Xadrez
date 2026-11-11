"""Arraste pelos callbacks reais, incluindo retorno, promoção e capturas em cadeia."""
import glfw
import numpy as np

from graficos.camera import Camera
from graficos.pecas import criar_modelos
from graficos.tabuleiro import centro
from interface import Interface
from main import criar_janela
from test_interface import ponto_tela, clicar_casa, avancar
from test_xadrez import casa, posicao
from test_damas import posicao as posicao_damas
from xadrez.partida import Partida as Xadrez
from damas.partida import Partida as Damas


def pressionar(ui, nome):
    x, y = ponto_tela(ui, *centro(casa(nome)))
    ui.mover(ui.janela, x, y)
    ui.mouse(ui.janela, glfw.MOUSE_BUTTON_LEFT, glfw.PRESS, 0)
    assert ui.arraste is not None


def mover_para(ui, nome):
    x, y = ponto_tela(ui, *centro(casa(nome)))
    ui.mover(ui.janela, x, y)
    assert ui.arraste.ativo


def soltar(ui):
    ui.mouse(ui.janela, glfw.MOUSE_BUTTON_LEFT, glfw.RELEASE, 0)


def terminar(ui):
    for _ in range(400):
        ui.atualizar(.02)
        if not ui.ocupada and not ui.camera.restante:
            return
    raise AssertionError("Arraste ou animação não terminou")


def testar():
    janela = criar_janela(False)
    try:
        ui = Interface(janela, Camera())
        ui.giro_automatico = False
        inicial = ui.sessao.partida.posicao

        # O limiar evita interpretar o clique tradicional como arraste.
        clicar_casa(ui, "e2")
        assert ui.arraste is None and ui.sessao.selecao == casa("e2")
        pressionar(ui, "e2")
        mover_para(ui, "e5")
        ui.tecla(janela, glfw.KEY_N, 0, glfw.PRESS, 0)
        assert ui.confirmacao is None
        soltar(ui)
        assert ui.arraste.retornando and ui.sessao.partida.posicao == inicial
        terminar(ui)
        assert ui.arraste is None and ui.sessao.partida.posicao == inicial
        pressionar(ui, "e2")
        mover_para(ui, "e4")
        posicao_soltar = ui.arraste.posicao
        soltar(ui)
        assert ui.sessao.animacao.inicio_visual == posicao_soltar
        assert len(ui.sessao.partida.historico) == 1
        terminar(ui)
        assert ui.sessao.partida.posicao.tabuleiro[casa("e4")] == "P"

        # Sair da janela depois de apontar um destino legal deve cancelar.
        pressionar(ui, "e7")
        mover_para(ui, "e5")
        anterior = ui.sessao.partida.posicao
        ui.mover(janela, -30, -30)
        soltar(ui)
        terminar(ui)
        assert ui.sessao.partida.posicao == anterior
        pressionar(ui, "e7")
        mover_para(ui, "e5")
        ui.foco(janela, False)
        assert ui.arraste.retornando
        soltar(ui)
        terminar(ui)
        assert ui.sessao.partida.posicao == anterior

        # Escape e soltura sobre o menu também devolvem sem alterar a partida.
        pressionar(ui, "e7")
        mover_para(ui, "e5")
        ui.tecla(janela, glfw.KEY_ESCAPE, 0, glfw.PRESS, 0)
        soltar(ui)
        terminar(ui)
        pressionar(ui, "e7")
        ui.mover(janela, 1098, 400)
        soltar(ui)
        terminar(ui)
        assert ui.sessao.partida.posicao == anterior

        # A seleção acompanha a projeção depois de redimensionar a janela.
        pressionar(ui, "e7")
        mover_para(ui, "e5")
        glfw.set_window_size(janela, 1000, 650)
        mover_para(ui, "e5")
        ui.atualizar(.02)
        soltar(ui)
        terminar(ui)
        assert ui.sessao.partida.posicao.tabuleiro[casa("e5")] == "p"
        glfw.set_window_size(janela, 1100, 800)

        # Arrastar cada pouso respeita a lei da maioria e a atomicidade.
        ui.sessao.lado = 1
        ui.sessao.limpar()
        ui.sessao.partidas[1] = Damas(posicao_damas({"a1":"P", "b2":"p", "d4":"p", "h8":"p"}))
        pressionar(ui, "a1")
        mover_para(ui, "c3")
        soltar(ui)
        terminar(ui)
        assert ui.sessao.passos == (casa("c3"),)
        assert not ui.sessao.partida.historico
        assert not ui.virar()
        pressionar(ui, "c3")
        mover_para(ui, "e5")
        soltar(ui)
        terminar(ui)
        assert len(ui.sessao.partida.historico) == 1
        assert ui.sessao.partida.posicao.tabuleiro[casa("b2")] == "."

        # A promoção só confirma o lance depois de escolher a peça.
        ui.sessao.lado = 0
        ui.sessao.limpar()
        ui.sessao.partidas[0] = Xadrez(posicao({"e1":"R", "a7":"P", "e8":"r"}))
        ui.camera.restaurar()
        pressionar(ui, "a7")
        mover_para(ui, "a8")
        soltar(ui)
        assert ui.promocao_visual and len(ui.sessao.promocao) == 4
        assert not ui.sessao.partida.historico
        ui.tecla(janela, glfw.KEY_ESCAPE, 0, glfw.PRESS, 0)
        terminar(ui)
        assert not ui.sessao.partida.historico
        pressionar(ui, "a7")
        mover_para(ui, "a8")
        soltar(ui)
        ui.comando("T")
        terminar(ui)
        assert ui.promocao_visual is None
        assert ui.sessao.partida.posicao.tabuleiro[casa("a8")] == "T"

        ui.informacoes.gerar(ui, 1100)
        assert ui.informacoes.chave[0] == "XADREZ"
        assert ui.informacoes.chave[1] == "Vez das pretas"
        ui.sessao.partida.resultado = "Brancas vencem por xeque-mate"
        ui.informacoes.gerar(ui, 800)
        assert ui.informacoes.chave[1] == ui.sessao.partida.resultado

        for segmentos in (20, 32):
            modelos = criar_modelos(segmentos)
            for tipo, malhas in modelos.items():
                dados = np.array([vertice for malha in malhas for vertice in malha.vertices])
                assert np.isfinite(dados).all(), tipo
                assert dados[:, 1].min() > -0.03, tipo
                assert dados[:, 1].max() < 1.8, tipo
        print("Arraste, retorno, promoção, capturas em cadeia, faixa fixa e modelos passaram.")
    finally:
        glfw.terminate()


if __name__ == "__main__":
    testar()
