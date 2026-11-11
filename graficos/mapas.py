"""Ambientes da praça. Coordenadas celestes e luzes pertencem ao mundo 3D."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Mapa:
    nome: str
    ceu_superior: tuple
    ceu_inferior: tuple
    astro: tuple
    raio_astro: float
    cor_astro: tuple
    ambiente: tuple
    luz: tuple
    noite: bool = False


MAPAS = {
    "dia": Mapa(
        "Praça diurna", (92, 157, 207), (211, 229, 233),
        (-18, 12, 36), 2.1, (1.0, 0.89, 0.58),
        (0.54, 0.55, 0.54), (0.53, 0.48, 0.37),
    ),
    "noite": Mapa(
        "Praça noturna", (9, 15, 38), (30, 46, 71),
        (14, 14, 44), 1.7, (0.80, 0.86, 0.97),
        (0.30, 0.34, 0.46), (0.22, 0.27, 0.39), True,
    ),
}

LUZES_POSTES = ((-10, 5.52, 3), (10, 5.52, -3),
                (-5.8, 3.9, 3.2), (5.8, 3.9, 3.2))


def estrelas(quantidade=220):
    """Pontos pequenos sobre uma semiesfera fixa em torno da praça."""
    import math
    from random import Random
    from .malhas import Malha, translacao, escala

    gerador = Random(24)
    malha = Malha()
    estrela = Malha()
    for sinal_x in (-1, 1):
        for sinal_y in (-1, 1):
            for sinal_z in (-1, 1):
                estrela.triangulo(((sinal_x, 0, 0), (0, sinal_y, 0), (0, 0, sinal_z)))
    for _ in range(quantidade):
        angulo = gerador.uniform(0, math.tau)
        elevacao = gerador.uniform(0.02, 1.4)
        raio = 66 * math.cos(elevacao)
        posicao = (raio * math.sin(angulo), 66 * math.sin(elevacao),
                   raio * math.cos(angulo))
        malha.juntar(estrela, translacao(*posicao) @ escala(gerador.uniform(0.12, 0.20)))
    return malha
