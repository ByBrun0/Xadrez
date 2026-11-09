from xadrez import regras as r
from xadrez.partida import Partida, busca_mate


def casa(nome):
    return ord(nome[0]) - ord("a") + 8 * (int(nome[1]) - 1)


def lance(origem, destino, promocao=""):
    return r.Lance(casa(origem), casa(destino), promocao)


def posicao(pecas, **kwargs):
    tabuleiro = ["."] * 64
    for nome, peca in pecas.items():
        tabuleiro[casa(nome)] = peca
    return r.Posicao(tuple(tabuleiro), **kwargs)


def perft(p, profundidade):
    if profundidade == 0:
        return 1
    return sum(perft(r.aplicar(p, l), profundidade - 1) for l in r.legais(p))


def testar():
    assert [perft(r.inicial(), n) for n in (1, 2, 3)] == [20, 400, 8902]
    partida = Partida()
    for par in (("f2", "f3"), ("e7", "e5"), ("g2", "g4"), ("d8", "h4")):
        assert partida.jogar(lance(*par))
    assert partida.resultado == "Pretas vencem por xeque-mate"
    assert not partida.jogar(lance("e2", "e4"))

    p = posicao({"e1": "R", "h1": "T", "a1": "T", "a8": "r", "f8": "t"})
    assert lance("e1", "g1") not in r.legais(p)
    assert lance("e1", "c1") in r.legais(p)
    assert r.aplicar(p, lance("e1", "c1")).tabuleiro[casa("d1")] == "T"
    assert r.identidade(p) != r.identidade(r.replace(p, roques=frozenset()))

    p = posicao({"e5": "R", "f5": "P", "g5": "p", "h5": "t", "a8": "r"},
                passagem=casa("g6"))
    assert lance("f5", "g6") not in r.legais(p)
    assert r.identidade(p).passagem is None
    p = posicao({"e5": "R", "f5": "P", "g5": "p", "a8": "r"}, passagem=casa("g6"))
    assert r.identidade(p).passagem == casa("g6")
    assert r.aplicar(p, lance("f5", "g6")).tabuleiro[casa("g5")] == "."

    p = posicao({"e1": "R", "a7": "P", "e8": "r"})
    assert {l.promocao for l in r.legais(p, casa("a7"))} == set("DTBC")
    p = posicao({"e1": "R", "e2": "T", "e8": "t", "a8": "r"})
    assert lance("e2", "d2") not in r.legais(p)

    assert "afogamento" in Partida(posicao({"a8": "r", "c6": "R", "c7": "D"}, turno=-1)).resultado
    assert "posição morta" in Partida(posicao({"a1": "R", "c3": "B", "h8": "r"})).resultado
    busca = busca_mate(posicao({"a8": "r", "c6": "R", "c7": "D"}, turno=-1))
    next(busca)
    try:
        next(busca)
    except StopIteration as fim:
        assert fim.value is False
    else:
        raise AssertionError("Busca deveria ter terminado")

    ciclo = (("g1", "f3"), ("g8", "f6"), ("f3", "g1"), ("f6", "g8"))
    partida = Partida()
    for par in (ciclo * 2)[:-1]:
        assert partida.jogar(lance(*par))
    assert partida.reivindicar(lance(*ciclo[-1]))
    assert "tripla" in partida.resultado and len(partida.historico) == 7
    partida = Partida()
    for par in ciclo * 4:
        assert partida.jogar(lance(*par))
    assert "quíntupla" in partida.resultado

    p = posicao({"a1": "R", "b1": "T", "h8": "r"}, meios_lances=99)
    assert Partida(p).reivindicar(lance("b1", "b2"))
    partida = Partida(r.replace(p, meios_lances=149))
    assert partida.jogar(lance("b1", "b2"))
    assert "75" in partida.resultado

    partida = Partida()
    for par in (("e2", "e4"), ("e7", "e5")):
        assert partida.jogar(lance(*par))
    partida.oferecer_ou_aceitar()
    assert partida.jogar(lance("g1", "f3"))
    partida.oferecer_ou_aceitar()
    assert "acordo" in partida.resultado
    partida = Partida()
    partida.abandonar()
    assert "Pretas" in partida.resultado


if __name__ == "__main__":
    testar()
    print("Testes de xadrez passaram.")
