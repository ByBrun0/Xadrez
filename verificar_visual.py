"""Medição reproduzível e imagens do próprio framebuffer do jogo."""
import json
from pathlib import Path
from time import perf_counter

import glfw
from OpenGL.GL import glFinish, glReadPixels, GL_RGB, GL_UNSIGNED_BYTE, GL_RENDERER, glGetString
from PIL import Image

from graficos.camera import Camera
from graficos.cena import Cena
from interface import Interface
from main import criar_janela
from animacao import Jogada
from configuracao import DURACAO_PASSO


def salvar_imagem(caminho):
    glFinish()
    dados=glReadPixels(0,0,1100,800,GL_RGB,GL_UNSIGNED_BYTE)
    imagem=Image.frombytes("RGB",(1100,800),dados)
    imagem.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(caminho)


def executar():
    pasta=Path(__file__).resolve().parent/"validacao"
    pasta.mkdir(exist_ok=True)
    janela=criar_janela(False)
    cena=None
    try:
        glfw.swap_interval(0)
        cena=Cena()
        ui=Interface(janela,Camera())
        ui.cursor = (10, 100)
        for _ in range(80):
            ui.atualizar(.02)
        for mapa in ("dia", "noite"):
            ui.mapa = mapa
            cena.desenhar(1100,800,ui,0)
            salvar_imagem(pasta/(mapa+".png"))
        inclinacao = ui.camera.inclinacao
        distancia = ui.camera.distancia
        ui.camera.inclinacao = ui.camera.alvo_inclinacao = 0.18
        ui.camera.distancia = ui.camera.alvo_distancia = 28
        for mapa, arquivo in (("dia", "sol_mundo.png"), ("noite", "ceu_noturno.png")):
            ui.mapa = mapa
            cena.desenhar(1100,800,ui,0)
            salvar_imagem(pasta/arquivo)
        ui.camera.inclinacao = ui.camera.alvo_inclinacao = inclinacao
        ui.camera.distancia = ui.camera.alvo_distancia = distancia
        ui.mapa = "dia"
        ui.cursor = (1098, 400)
        for _ in range(20):
            ui.atualizar(.02)
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"menu_aberto.png")
        ui.cursor = (10, 100)
        for _ in range(80):
            ui.atualizar(.02)
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"menu_retraido.png")
        resultados={"gpu":glGetString(GL_RENDERER).decode(),"resolucao":[1100,800],"mapa":"dia",
                    "referencia_anterior_ms":77.57,"testes":{}}
        for qualidade in ("normal","baixa"):
            ui.qualidade=qualidade
            for _ in range(12):
                ui.atualizar(.016)
                cena.desenhar(1100,800,ui,0)
            tempos=[]
            for _ in range(120):
                inicio=perf_counter()
                ui.atualizar(.016)
                cena.desenhar(1100,800,ui,0)
                glFinish()
                tempos.append((perf_counter()-inicio)*1000)
            media=sum(tempos)/len(tempos)
            resultados["testes"][qualidade]={"media_ms":round(media,2),
                                             "fps":round(1000/media,1)}
        ui.qualidade="normal"
        # Mede uma captura desenhada no meio de seu salto para a bacia.
        from test_xadrez import posicao, lance
        from xadrez import regras
        anterior=regras.inicial()
        for abertura in (lance("e2","e4"),lance("d7","d5")):
            anterior=regras.aplicar(anterior,abertura)
        movimento=lance("e4","d5")
        seguinte=regras.aplicar(anterior,movimento)
        ui.sessao.animacao=Jogada(anterior.tabuleiro,seguinte.tabuleiro,movimento)
        ui.sessao.animacao.tempo=DURACAO_PASSO+0.20
        inicio=perf_counter()
        for _ in range(60):
            cena.desenhar(1100,800,ui,0)
            glFinish()
        resultados["testes"]["captura_ms"]=round((perf_counter()-inicio)*1000/60,2)
        ui.sessao.animacao=None
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"xadrez.png")
        ui.virar()
        for _ in range(70):
            ui.atualizar(.02)
        inicio=perf_counter()
        for _ in range(60):
            cena.desenhar(1100,800,ui,0)
            glFinish()
        resultados["testes"]["virada_ms"]=round((perf_counter()-inicio)*1000/60,2)
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"virada.png")
        for _ in range(130):
            ui.atualizar(.02)
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"damas.png")

        # Captura de uma peça de cada tipo em destaque, também da dama coroada.
        from xadrez.partida import Partida as Xadrez
        from test_xadrez import posicao
        ui.sessao.lado=0
        ui.sessao.partidas[0]=Xadrez(posicao({"a3":"T","b3":"C","c3":"B","d3":"D",
                                             "e3":"R","f3":"P","a6":"t","b6":"c",
                                             "c6":"b","d6":"d","e6":"r","f6":"p"}))
        ui.camera.alvo_distancia=ui.camera.distancia=13
        ui.camera.angulo=3.14
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"pecas.png")
        # Arraste em andamento, sem confirmar a posição lógica.
        from test_arraste import pressionar, mover_para
        ui.sessao.partidas[0]=Xadrez()
        ui.sessao.limpar()
        ui.camera.restaurar()
        for _ in range(70):
            ui.atualizar(.02)
        pressionar(ui,"e2")
        mover_para(ui,"e4")
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"arraste.png")
        ui.tecla(janela,glfw.KEY_ESCAPE,0,glfw.PRESS,0)
        for _ in range(20):
            ui.atualizar(.02)
        from damas.partida import Partida as Damas
        from test_damas import posicao as posicao_damas
        ui.sessao.limpar()
        ui.sessao.lado=1
        ui.sessao.partidas[1]=Damas(posicao_damas({"c3":"P","e3":"D","b6":"p","f6":"d"}))
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"damas_coroadas.png")

        # Exercita a entrada usada por main.py e os efeitos nos dois perfis.
        ui=Interface(janela,Camera(),apresentar=True)
        cena.desenhar(1100,800,ui,1)
        salvar_imagem(pasta/"tela_inicial.png")
        ui.comando_tela("escolher_noite")
        ui.comando_tela("iniciar_damas")
        for _ in range(120):
            ui.atualizar(.02)
        ui.comando("contemplar")
        for _ in range(120):
            ui.atualizar(.02)
        for qualidade in ("normal","baixa"):
            ui.qualidade=qualidade
            cena.desenhar(1100,800,ui,4)
            salvar_imagem(pasta/("contemplacao_"+qualidade+".png"))
            inicio=perf_counter()
            for quadro in range(90):
                cena.desenhar(1100,800,ui,4+quadro/60)
                glFinish()
            media=(perf_counter()-inicio)*1000/90
            resultados["testes"]["noite_"+qualidade]={"media_ms":round(media,2),
                                                       "fps":round(1000/media,1)}
        ui.comando("contemplar")
        ui.sessao.lado=0
        partida_resultado=Xadrez()
        for origem,destino in (("f2","f3"),("e7","e5"),("g2","g4"),("d8","h4")):
            partida_resultado.jogar(lance(origem,destino))
        ui.sessao.partidas[0]=partida_resultado
        for _ in range(60):
            ui.atualizar(.02)
        cena.desenhar(1100,800,ui,6)
        salvar_imagem(pasta/"resultado.png")
        resultados["observacao"]="Medição local sem limite de FPS. A conferência manual da janela ficou pendente."
        (pasta/"desempenho.json").write_text(json.dumps(resultados,indent=2,ensure_ascii=False),encoding="utf-8")
        print(json.dumps(resultados,indent=2,ensure_ascii=False))
    finally:
        if cena:
            cena.liberar()
        glfw.terminate()


if __name__=="__main__":
    executar()
