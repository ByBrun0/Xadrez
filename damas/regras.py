"""Damas brasileiras. Peões P/p e damas D/d, brancas positivas."""
from dataclasses import dataclass

from xadrez.regras import cor, deslocar, DIAGONAIS


@dataclass(frozen=True)
class Posicao:
    tabuleiro: tuple
    turno: int = 1
    meios_lances: int = 0


@dataclass(frozen=True)
class Lance:
    origem: int
    pousos: tuple
    capturadas: tuple = ()

    @property
    def destino(self):
        return self.pousos[-1]


def inicial():
    tab = ["."] * 64
    for casa in range(64):
        if (casa % 8 + casa // 8) % 2 == 0:
            if casa < 24:
                tab[casa] = "P"
            elif casa >= 40:
                tab[casa] = "p"
    return Posicao(tuple(tab))


def saltos(tab, casa, peca, capturadas):
    for dx, dy in DIAGONAIS:
        vitima = deslocar(casa, dx, dy)
        if peca.upper() == "D":
            while vitima is not None and tab[vitima] == ".":
                vitima = deslocar(vitima, dx, dy)
        if (vitima is None or cor(tab[vitima]) != -cor(peca)
                or vitima in capturadas):
            continue
        destino = deslocar(vitima, dx, dy)
        while destino is not None and tab[destino] == ".":
            yield destino, vitima
            if peca.upper() != "D":
                break
            destino = deslocar(destino, dx, dy)


def sequencias(tab, origem, casa, peca, pousos=(), capturadas=()):
    opcoes = list(saltos(tab, casa, peca, capturadas))
    if not opcoes and capturadas:
        yield Lance(origem, pousos, capturadas)
    for destino, vitima in opcoes:
        seguinte = list(tab)
        seguinte[casa] = "."
        seguinte[destino] = peca
        # As vítimas continuam bloqueando a diagonal até o fim do lance.
        yield from sequencias(seguinte, origem, destino, peca,
                              pousos + (destino,), capturadas + (vitima,))


def legais(posicao):
    tab = posicao.tabuleiro
    capturas = []
    for casa, peca in enumerate(tab):
        if cor(peca) == posicao.turno:
            capturas.extend(sequencias(tab, casa, casa, peca))
    if capturas:
        maioria = max(len(l.capturadas) for l in capturas)
        return [l for l in capturas if len(l.capturadas) == maioria]
    lances = []
    for casa, peca in enumerate(tab):
        if cor(peca) != posicao.turno:
            continue
        direcoes = DIAGONAIS if peca.upper() == "D" else ((1, posicao.turno), (-1, posicao.turno))
        for dx, dy in direcoes:
            destino = deslocar(casa, dx, dy)
            while destino is not None and tab[destino] == ".":
                lances.append(Lance(casa, (destino,)))
                if peca.upper() != "D":
                    break
                destino = deslocar(destino, dx, dy)
    return lances


def aplicar(posicao, lance):
    tab = list(posicao.tabuleiro)
    peca = tab[lance.origem]
    tab[lance.origem] = "."
    for casa in lance.capturadas:
        tab[casa] = "."
    promovida = peca
    if peca.upper() == "P" and lance.destino // 8 == (7 if posicao.turno == 1 else 0):
        promovida = "D" if posicao.turno == 1 else "d"
    tab[lance.destino] = promovida
    contador = posicao.meios_lances + 1 if peca.upper() == "D" and not lance.capturadas else 0
    return Posicao(tuple(tab), -posicao.turno, contador)


def identidade(posicao):
    return posicao.tabuleiro, posicao.turno


def final_limitado(posicao):
    """Família do final e limite em pares de lances, artigos 99 e 100."""
    lados = {lado: [(i, p.upper()) for i, p in enumerate(posicao.tabuleiro)
                    if cor(p) == lado] for lado in (1, -1)}
    for lado in (1, -1):
        solitaria = lados[lado]
        outras = lados[-lado]
        if len(solitaria) != 1 or solitaria[0][1] != "D":
            continue
        damas = sum(p == "D" for _, p in outras)
        if len(outras) in (1, 2) and damas >= 1:
            return ("reduzido", lado), 5
        casa = solitaria[0][0]
        if len(outras) == 3 and damas >= 1 and casa % 8 == casa // 8:
            return ("grande_diagonal", lado), 5
    return None, 0
