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
        resultados={"gpu":glGetString(GL_RENDERER).decode(),"resolucao":[1100,800],
                    "referencia_anterior_ms":77.57,"testes":{}}
        for qualidade in ("normal","leve"):
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
        ui.sessao.partidas[0]=Xadrez(posicao({"a4":"T","b4":"C","c4":"B","d4":"D",
                                             "e4":"R","f4":"P","h8":"r"}))
        ui.camera.alvo_distancia=ui.camera.distancia=13
        ui.camera.angulo=3.14
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"pecas.png")
        from damas.partida import Partida as Damas
        from test_damas import posicao as posicao_damas
        ui.sessao.lado=1
        ui.sessao.partidas[1]=Damas(posicao_damas({"c3":"P","e3":"D","b6":"p","f6":"d"}))
        cena.desenhar(1100,800,ui,0)
        salvar_imagem(pasta/"damas_coroadas.png")
        resultados["observacao"]="Medição local sem limite de FPS. A conferência manual da janela ficou pendente."
        (pasta/"desempenho.json").write_text(json.dumps(resultados,indent=2,ensure_ascii=False),encoding="utf-8")
        print(json.dumps(resultados,indent=2,ensure_ascii=False))
    finally:
        if cena:
            cena.liberar()
        glfw.terminate()


if __name__=="__main__":
    executar()
