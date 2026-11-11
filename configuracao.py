"""Dimensões, cores e tempos compartilhados pela cena."""
from dataclasses import dataclass
TOPO_MESA = 3.0
PLANO = 3.24
CENTRO_TABULEIRO = PLANO - 0.18
DURACAO_PASSO = 0.42
DURACAO_CAPTURA = 0.48
ALTURA_VIRADA = 4.9
PAINEL_LARGURA = 276
CORES_PECAS = ((0.91, 0.77, 0.55), (0.34, 0.185, 0.105))
BRONZE = (0.61, 0.36, 0.13)

@dataclass(frozen=True)
class Qualidade:
    segmentos_pecas: int
    limite_textura: int
    segmentos_astro: int
    estrelas: int
    folhas: int
    vento: bool
    pulsacao_luzes: bool
    luzes_locais: int
    sombras_contato: bool
    levitacao: bool
    duracao_apresentacao: float


QUALIDADES = {
    "normal": Qualidade(32, 1024, 32, 220, 8, True, True, 4, True, True, 2.2),
    "baixa": Qualidade(16, 512, 16, 64, 0, False, False, 2, False, False, 1.2),
}


def nome_qualidade(nome):
    # Compatibilidade com chamadas feitas antes da mudança do nome no menu.
    return "baixa" if nome == "leve" else nome


def perfil_qualidade(nome):
    return QUALIDADES[nome_qualidade(nome)]


NOMES_PECAS = {"P": "Peão", "T": "Torre", "C": "Cavalo",
              "B": "Bispo", "D": "Dama", "R": "Rei"}
