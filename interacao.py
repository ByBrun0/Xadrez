"""Estado visual do arraste. Usa o plano selecionado pelas matrizes da câmera."""
from math import hypot

from animacao import suave
from graficos.tabuleiro import centro


class ArrastePeca:
    LIMIAR_PIXELS = 6
    DURACAO_RETORNO = 0.26

    def __init__(self, casa, peca, cursor, ponto):
        self.casa = casa
        self.peca = peca
        self.cursor_inicial = cursor
        self.x, self.z = centro(casa)
        self.deslocamento = (self.x - ponto[0], self.z - ponto[2])
        self.altura = 0.26
        self.ativo = False
        self.retornando = False
        self.tempo = 0

    def mover(self, cursor, ponto):
        if self.retornando:
            return
        distancia = hypot(cursor[0] - self.cursor_inicial[0],
                          cursor[1] - self.cursor_inicial[1])
        self.ativo = self.ativo or distancia >= self.LIMIAR_PIXELS
        if self.ativo and ponto is not None:
            self.x = max(-12, min(12, ponto[0] + self.deslocamento[0]))
            self.z = max(-12, min(12, ponto[2] + self.deslocamento[1]))

    def devolver(self):
        self.retornando = True
        self.inicio_retorno = (self.x, self.altura, self.z)
        self.tempo = 0

    def atualizar(self, dt):
        if not self.retornando:
            return False
        self.tempo += dt
        t = suave(self.tempo / self.DURACAO_RETORNO)
        x, z = centro(self.casa)
        self.x = self.inicio_retorno[0] * (1 - t) + x * t
        self.altura = self.inicio_retorno[1] * (1 - t)
        self.z = self.inicio_retorno[2] * (1 - t) + z * t
        return self.tempo >= self.DURACAO_RETORNO

    @property
    def visivel(self):
        return self.ativo or self.retornando

    @property
    def posicao(self):
        return self.x, self.altura, self.z
