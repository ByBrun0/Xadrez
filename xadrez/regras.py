from dataclasses import dataclass
from dataclasses import replace

RETAS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGONAIS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
CAVALO = ((1, 2), (2, 1), (-1, 2), (-2, 1),
          (1, -2), (2, -1), (-1, -2), (-2, -1))
PROMOCOES = "DTBC"


@dataclass(frozen=True)
class Lance:
    origem: int
    destino: int
    promocao: str = ""


@dataclass(frozen=True)
class Posicao:
    tabuleiro: tuple
    turno: int = 1
    roques: frozenset = frozenset((0, 7, 56, 63))
    passagem: int | None = None
    meios_lances: int = 0


def inicial():
    fila = "TCBDRBCT"
    return Posicao(tuple(fila + "P" * 8 + "." * 32 + "p" * 8 + fila.lower()))


def cor(peca):
    if peca == ".":
        return 0
    return 1 if peca.isupper() else -1


def deslocar(casa, dx, dy):
    x, y = casa % 8 + dx, casa // 8 + dy
    if 0 <= x < 8 and 0 <= y < 8:
        return y * 8 + x
    return None


def ataques(tabuleiro, origem):
    peca = tabuleiro[origem]
    tipo = peca.upper()
    if tipo == "P":
        direcoes = ((-1, cor(peca)), (1, cor(peca)))
    else:
        direcoes = {"T": RETAS, "B": DIAGONAIS, "D": RETAS + DIAGONAIS,
                    "R": RETAS + DIAGONAIS, "C": CAVALO}[tipo]
    for dx, dy in direcoes:
        destino = deslocar(origem, dx, dy)
        while destino is not None:
            yield destino
            if tipo in "PRC" or tabuleiro[destino] != ".":
                break
            destino = deslocar(destino, dx, dy)


def atacada(tabuleiro, casa, atacante):
    return any(casa in ataques(tabuleiro, i)
               for i, peca in enumerate(tabuleiro) if cor(peca) == atacante)


def em_xeque(posicao, lado=None):
    lado = posicao.turno if lado is None else lado
    rei = posicao.tabuleiro.index("R" if lado == 1 else "r")
    return atacada(posicao.tabuleiro, rei, -lado)


def candidatos(posicao, origem):
    tab = posicao.tabuleiro
    tipo = tab[origem].upper()
    lado = posicao.turno
    if tipo == "P":
        destinos = [d for d in ataques(tab, origem)
                    if (cor(tab[d]) == -lado and tab[d].upper() != "R")
                    or d == posicao.passagem]
        frente = deslocar(origem, 0, lado)
        if frente is not None and tab[frente] == ".":
            destinos.append(frente)
            if origem // 8 == (1 if lado == 1 else 6) and tab[frente + 8 * lado] == ".":
                destinos.append(frente + 8 * lado)
        for destino in destinos:
            promocoes = PROMOCOES if destino // 8 in (0, 7) else ("",)
            for promocao in promocoes:
                yield Lance(origem, destino, promocao)
        return

    for destino in ataques(tab, origem):
        if cor(tab[destino]) != lado and tab[destino].upper() != "R":
            yield Lance(origem, destino)

    base = 0 if lado == 1 else 56
    if tipo == "R" and origem == base + 4 and not em_xeque(posicao):
        for torre, passo in ((base, -1), (base + 7, 1)):
            if torre not in posicao.roques or tab[torre] != ("T" if lado == 1 else "t"):
                continue
            if any(tab[i] != "." for i in range(min(torre, origem) + 1, max(torre, origem))):
                continue
            passagem = Lance(origem, origem + passo)
            if not em_xeque(aplicar(posicao, passagem), lado):
                yield Lance(origem, origem + 2 * passo)


def aplicar(posicao, lance):
    origem, destino = lance.origem, lance.destino
    tab = list(posicao.tabuleiro)
    peca, capturada = tab[origem], tab[destino]
    lado = posicao.turno
    peao = peca.upper() == "P"
    roques = set(posicao.roques)
    roques.difference_update((origem, destino))
    tab[origem] = "."
    tab[destino] = peca
    if peao and destino == posicao.passagem:
        tab[destino - 8 * lado] = "."
        capturada = "P"
    if lance.promocao:
        tab[destino] = lance.promocao if lado == 1 else lance.promocao.lower()
    if peca.upper() == "R":
        base = 0 if lado == 1 else 56
        roques.difference_update((base, base + 7))
        if abs(destino - origem) == 2:
            torre = base if destino < origem else base + 7
            meio = (origem + destino) // 2
            tab[meio], tab[torre] = tab[torre], "."
    passagem = (origem + destino) // 2 if peao and abs(destino - origem) == 16 else None
    contador = 0 if peao or capturada != "." else posicao.meios_lances + 1
    return Posicao(tuple(tab), -lado, frozenset(roques), passagem, contador)


def legais(posicao, origem=None):
    origens = range(64) if origem is None else (origem,)
    for casa in origens:
        if cor(posicao.tabuleiro[casa]) == posicao.turno:
            for lance in candidatos(posicao, casa):
                if not em_xeque(aplicar(posicao, lance), posicao.turno):
                    yield lance


def identidade(posicao):
    passagem = posicao.passagem
    if passagem is not None:
        tab = posicao.tabuleiro
        peao = "P" if posicao.turno == 1 else "p"
        if not any(casa is not None and tab[casa] == peao
                   and any(l.destino == passagem for l in legais(posicao, casa))
                   for casa in (deslocar(passagem, dx, -posicao.turno) for dx in (-1, 1))):
            passagem = None
    return replace(posicao, passagem=passagem, meios_lances=0)
