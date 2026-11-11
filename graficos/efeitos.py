"""Movimentos decorativos por funções paramétricas, aulas 20–22 e BEND da 24."""
import math

from animacao import suave
from .malhas import Malha, translacao, rotacao, escala


def folha():
    malha = Malha()
    pontos = ((0, 0.035, -0.22), (-0.09, 0, 0), (0, 0.035, 0.22), (0.09, 0, 0))
    malha.quad(pontos, (0, 1, 0))
    return malha


def folhas_em_movimento(tempo, quantidade):
    arvores = ((-9, -9), (9, -9), (-9, 9), (9, 9))
    for i in range(quantidade):
        x, z = arvores[i % 4]
        fase = (tempo * 0.42 + i * 0.71) % 5.3
        x += 1.0 * math.sin(tempo * 0.65 + i * 1.7)
        z += 0.8 * math.cos(tempo * 0.45 + i)
        y = 5.9 - fase
        tamanho = suave(min(1, fase/0.3, (5.3-fase)/0.3))
        yield translacao(x, y, z) @ rotacao(tempo * 30 + i * 45) @ rotacao(25, "x") @ escala(max(0.001,tamanho))
