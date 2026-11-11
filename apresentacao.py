"""Câmera de entrada, contemplação e resultado. Transformações das aulas 9–19."""
import math

import numpy as np

from animacao import suave
from configuracao import perfil_qualidade
from graficos.tabuleiro import centro


class Apresentacao:
    def __init__(self, camera, ativa=False):
        self.ativa = ativa
        self.modo = "menu" if ativa else "jogo"
        self.tempo = 0
        self.casa_resultado = None
        self.lado_resultado = None
        self.resultados_vistos = {}
        self.vista_guardada = None
        self.inicio = None
        if ativa:
            camera.angulo = math.pi + 0.55
            camera.inclinacao = camera.alvo_inclinacao = 0.48
            camera.distancia = camera.alvo_distancia = 28

    @property
    def modal(self):
        return self.modo == "menu" or (self.modo == "resultado" and self.inicio is None)

    @property
    def permite_jogar(self):
        return self.modo == "jogo"

    def iniciar(self, interface, lado):
        interface.sessao.limpar()
        interface.sessao.lado = lado
        self.casa_resultado = None
        self.modo = "introducao"
        self.tempo = 0
        self.duracao = perfil_qualidade(interface.qualidade).duracao_apresentacao
        camera = interface.camera
        camera.restante = 0
        self.inicio = (camera.angulo, camera.inclinacao, camera.distancia, camera.foco.copy())
        turno = interface.sessao.partida.posicao.turno
        self.alvo = ((math.pi if turno == 1 else 0) + 0.23, 0.78, 19.3, np.zeros(3))
        # Escolhe o giro mais curto para chegar à perspectiva inicial.
        diferenca = (self.alvo[0] - self.inicio[0] + math.pi) % math.tau - math.pi
        self.alvo = (self.inicio[0] + diferenca, *self.alvo[1:])

    def contemplar(self, interface):
        camera = interface.camera
        if self.modo == "contemplacao":
            camera.recuperar(self.vista_guardada)
            self.modo = "jogo"
            return
        if self.modo != "jogo":
            return
        self.vista_guardada = camera.guardar()
        camera.foco = np.zeros(3)
        camera.alvo_inclinacao = 0.48
        camera.alvo_distancia = 26
        self.modo = "contemplacao"

    def dispensar_resultado(self):
        self.modo = "jogo"
        self.inicio = None

    def observar_resultado(self, interface):
        sessao = interface.sessao
        partida = sessao.partida
        if (not self.ativa or self.modo != "jogo" or interface.ocupada
                or interface.camera.restante or not partida.resultado
                or self.resultados_vistos.get(sessao.lado) is partida):
            return
        self.resultados_vistos[sessao.lado] = partida
        self.lado_resultado = sessao.lado
        self.casa_resultado = None
        if sessao.lado == 0 and "xeque-mate" in partida.resultado:
            rei = "R" if partida.posicao.turno == 1 else "r"
            self.casa_resultado = partida.posicao.tabuleiro.index(rei)
        elif partida.historico:
            self.casa_resultado = partida.historico[-1].destino
        camera = interface.camera
        self.inicio = (camera.angulo, camera.inclinacao, camera.distancia, camera.foco.copy())
        foco = np.zeros(3)
        if self.casa_resultado is not None:
            x, z = centro(self.casa_resultado)
            foco = np.array((x * 0.55, 0, z * 0.55))
        self.alvo = (camera.angulo, 0.75, 16.5, foco)
        self.tempo = 0
        self.duracao = 0.8 if interface.qualidade == "normal" else 0.45
        self.modo = "resultado"

    def atualizar(self, dt, interface):
        camera = interface.camera
        self.tempo += dt
        if self.modo == "menu":
            camera.angulo = (camera.angulo + dt * 0.035) % math.tau
        elif self.modo == "contemplacao":
            camera.angulo = (camera.angulo + dt * 0.10) % math.tau
        elif self.modo in ("introducao", "resultado") and self.inicio is not None:
            t = suave(self.tempo / self.duracao)
            camera.angulo = self.inicio[0] + (self.alvo[0] - self.inicio[0]) * t
            camera.inclinacao = camera.alvo_inclinacao = self.inicio[1] + (self.alvo[1] - self.inicio[1]) * t
            camera.distancia = camera.alvo_distancia = self.inicio[2] + (self.alvo[2] - self.inicio[2]) * t
            camera.foco = self.inicio[3] + (self.alvo[3] - self.inicio[3]) * t
            if self.tempo >= self.duracao:
                self.inicio = None
                if self.modo == "introducao":
                    self.modo = "jogo"
        self.observar_resultado(interface)
