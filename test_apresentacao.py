"""Entrada normal, contemplação, resultado, hover e qualidade de toda a cena."""
import glfw
import numpy as np
from OpenGL.GL import glGetError, GL_NO_ERROR, glGetTexLevelParameteriv, glBindTexture, GL_TEXTURE_2D, GL_TEXTURE_WIDTH

from configuracao import perfil_qualidade
from graficos.camera import Camera
from graficos.cena import Cena
from interface import Interface
from main import criar_janela
from test_interface import clicar, clicar_casa, ponto_tela, avancar
from test_xadrez import posicao, casa
from test_damas import posicao as posicao_damas
from xadrez.partida import Partida as Xadrez
from damas.partida import Partida as Damas
from graficos.tabuleiro import centro


def clicar_tela(ui, codigo):
    ui.telas.gerar(ui)
    ret = next(ret for ret, acao in ui.telas.botoes if acao == codigo)
    largura, altura = glfw.get_window_size(ui.janela)
    x, y, w, h = ui.telas.retangulo(largura, altura)
    clicar(ui, x + (ret[0]+ret[2])/2*w/ui.telas.imagem.width,
           y + (ret[1]+ret[3])/2*h/ui.telas.imagem.height)


def concluir_apresentacao(ui):
    for _ in range(180):
        ui.atualizar(.02)
        if ui.apresentacao.permite_jogar:
            return
    raise AssertionError("Apresentação não terminou")


def testar():
    janela = criar_janela(False)
    cena = None
    try:
        ui = Interface(janela, Camera(), apresentar=True)
        cena = Cena()
        assert ui.apresentacao.modal and ui.apresentacao.modo == "menu"
        cena.desenhar(1100, 800, ui, 0)
        clicar_tela(ui, "escolher_noite")
        clicar_tela(ui, "qualidade")
        assert ui.mapa == "noite" and ui.qualidade == "baixa"
        clicar_tela(ui, "iniciar_damas")
        assert ui.apresentacao.modo == "introducao"
        assert ui.sessao.lado == 1
        clicar_casa(ui, "a3")
        assert not ui.sessao.partida.historico and ui.sessao.selecao is None
        concluir_apresentacao(ui)
        assert abs(ui.camera.distancia-19.3) < 1e-6
        guardada = ui.camera.guardar()
        ui.tecla(janela, glfw.KEY_C, 0, glfw.PRESS, 0)
        for _ in range(40):
            ui.atualizar(.02)
        assert ui.apresentacao.modo == "contemplacao"
        assert ui.camera.angulo != guardada[0]
        clicar_casa(ui, "a3")
        assert not ui.sessao.partida.historico
        ui.tecla(janela, glfw.KEY_ESCAPE, 0, glfw.PRESS, 0)
        assert ui.apresentacao.permite_jogar
        assert ui.camera.guardar() == guardada

        damas_preservadas = ui.sessao.partidas[1]
        mate = posicao({"a8":"r", "c6":"R", "b7":"D"}, turno=-1)
        ui.sessao.lado = 0
        ui.sessao.partidas[0] = Xadrez(mate)
        for _ in range(60):
            ui.atualizar(.02)
        assert ui.apresentacao.modo == "resultado" and ui.apresentacao.modal
        assert ui.apresentacao.casa_resultado == casa("a8")
        assert not np.allclose(ui.camera.foco, 0)
        cena.desenhar(1100, 800, ui, 1.2)
        clicar_tela(ui, "outro_jogo")
        avancar(ui)
        assert ui.sessao.lado == 1 and ui.sessao.partida is damas_preservadas
        assert ui.sessao.partidas[0].resultado
        assert ui.virar()
        avancar(ui)
        assert ui.apresentacao.modo == "jogo"

        # Um novo resultado oferece revanche sem reiniciar a outra face.
        ui.sessao.partidas[0] = Xadrez(mate)
        for _ in range(60):
            ui.atualizar(.02)
        clicar_tela(ui, "revanche")
        concluir_apresentacao(ui)
        assert not ui.sessao.partida.historico and not ui.sessao.partida.resultado
        assert ui.sessao.partidas[1] is damas_preservadas

        x, y = ponto_tela(ui, *centro(casa("b1")))
        ui.mover(janela, x, y)
        ui.atualizar(.02)
        assert ui.descricao_sobre == "Cavalo · brancas"
        ui.sessao.lado = 1
        ui.sessao.limpar()
        ui.sessao.partidas[1] = Damas(posicao_damas({"a1":"P", "b2":"p", "d4":"p", "h8":"p"}))
        ui.camera.restaurar()
        clicar_casa(ui, "a1")
        assert ui.destino_captura(casa("c3"))
        ui.informacoes.gerar(ui, 1100)
        assert "2 peça" in ui.informacoes.chave[2]

        recursos = len(cena.gpu.recursos), len(cena.gpu.texturas)
        for _ in range(2):
            for qualidade in ("normal", "baixa"):
                ui.qualidade = qualidade
                perfil = perfil_qualidade(qualidade)
                for mapa in ("dia", "noite"):
                    ui.mapa = mapa
                    cena.desenhar(1100, 800, ui, 4)
                    assert glGetError() == GL_NO_ERROR
                textura = cena.imagens[qualidade]["madeira"]
                glBindTexture(GL_TEXTURE_2D, textura)
                largura = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH)
                assert largura <= perfil.limite_textura
        assert recursos == (len(cena.gpu.recursos), len(cena.gpu.texturas))
        assert perfil_qualidade("leve") is perfil_qualidade("baixa")
        assert cena.estrelas["baixa"][2] < cena.estrelas["normal"][2]
        assert sum(m[2] for m in cena.grupos["baixa"].values()) < sum(m[2] for m in cena.grupos["normal"].values())
        assert perfil_qualidade("normal").folhas > 0 and perfil_qualidade("baixa").folhas == 0
        print("Tela inicial, introdução, contemplação, resultado, hover e qualidade global passaram.")
    finally:
        if cena:
            cena.liberar()
        glfw.terminate()


if __name__ == "__main__":
    testar()
