"""Regressões do menu retrátil, ambientes e modificadores da aula 24."""
import glfw
import numpy as np
from OpenGL.GL import glGetError, GL_NO_ERROR

from graficos.camera import Camera
from graficos.cena import Cena
from graficos.mapas import MAPAS
from graficos.modificadores import cubo_subdividido, bevel, bend, banco_curvo
from graficos.painel import Painel, dimensoes
from interface import Interface
from main import criar_janela
from test_interface import ponto_tela, clicar_casa, avancar
from test_xadrez import casa


def testar():
    vertices, faces = cubo_subdividido(4)
    original = vertices.copy()
    assert len(vertices) < len(faces) * 4
    assert np.allclose(bend(vertices, 0), vertices)
    arredondados = bevel(vertices, 0.22)
    assert np.array_equal(vertices, original)
    assert np.isfinite(arredondados).all()
    assert np.max(np.abs(arredondados)) <= 1
    cantos = np.all(np.abs(vertices) == 1, axis=1)
    assert np.all(np.abs(arredondados[cantos]) < 1)
    curvados = bend(vertices, 0.2)
    assert np.all(curvados[:, 1] >= vertices[:, 1])
    banco = np.array(banco_curvo(8.45, 0.12, 0.42).vertices)
    assert np.isfinite(banco).all()
    assert np.allclose(np.linalg.norm(banco[:, 3:6], axis=1), 1)

    painel = Painel()
    for _ in range(70):
        painel.atualizar(.02, (10, 100), 1100, 800)
    assert painel.abertura == 0
    assert dimensoes(1100)[0] == 1100
    assert painel.clicar(1098, 400, 1100, 800) == "painel"
    for _ in range(20):
        painel.atualizar(.02, (1098, 400), 1100, 800)
    assert painel.abertura == 1
    for _ in range(100):
        painel.atualizar(.02, (10, 100), 1100, 800, manter_aberto=True)
    assert painel.abertura == 1

    janela = criar_janela(False)
    cena = None
    try:
        ui = Interface(janela, Camera())
        cena = Cena()
        posicoes = tuple(p.posicao for p in ui.sessao.partidas)
        ui.cursor = (10, 100)
        for _ in range(80):
            ui.atualizar(.02)
        assert ui.painel.abertura == 0
        tela_fechado = ponto_tela(ui, 1.5, -2.5)
        ui.cursor = (1098, 400)
        for _ in range(20):
            ui.atualizar(.02)
        assert ui.painel.abertura == 1
        assert np.allclose(tela_fechado, ponto_tela(ui, 1.5, -2.5))
        ui.painel.gerar(ui)
        esquerda, largura = ui.painel.limites(1100)
        # Mapa é o quinto botão. O clique usa a mesma transformação do desenho.
        codigo = ui.painel.clicar(esquerda + largura / 2, 458, 1100, 800)
        assert codigo == "mapa"
        ui.comando(codigo)
        assert ui.mapa == "noite"
        cena.desenhar(1100, 800, ui, 0)
        assert glGetError() == GL_NO_ERROR
        ui.tecla(janela, glfw.KEY_M, 0, glfw.PRESS, 0)
        assert ui.mapa == "dia"
        assert tuple(p.posicao for p in ui.sessao.partidas) == posicoes
        cena.desenhar(1100, 800, ui, 0)
        assert glGetError() == GL_NO_ERROR

        sol = np.array((*MAPAS["dia"].astro, 1))
        p, v = ui.camera.matrizes(1100 / 800, 3.24)
        anterior = p @ v @ sol
        ui.camera.angulo += 0.5
        p, v = ui.camera.matrizes(1100 / 800, 3.24)
        seguinte = p @ v @ sol
        assert not np.allclose(anterior[:2] / anterior[3], seguinte[:2] / seguinte[3])
        assert np.allclose(np.linalg.inv(p @ v) @ seguinte, sol)

        ui.camera.restaurar()
        clicar_casa(ui, "e2")
        assert ui.sessao.selecao == casa("e2")
        clicar_casa(ui, "e4")
        avancar(ui)
        assert len(ui.sessao.partida.historico) == 1
        print("Menu, mapas, sol no mundo 3D e modificadores da aula 24 passaram.")
    finally:
        if cena:
            cena.liberar()
        glfw.terminate()


if __name__ == "__main__":
    testar()
