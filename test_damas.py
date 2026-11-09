"""Casos de regras brasileiras e integração da sessão, sem janela."""
from dataclasses import replace

from damas import regras as r
from damas.partida import Partida
from sessao import Sessao
from test_xadrez import casa
from xadrez import regras as x


def posicao(pecas,turno=1,contador=0):
    tab=["."]*64
    for nome,peca in pecas.items():
        tab[casa(nome)]=peca
    return r.Posicao(tuple(tab),turno,contador)


def terminar_animacao(sessao):
    for _ in range(300):
        sessao.atualizar(0.02)
        if not sessao.bloqueada:
            return
    raise AssertionError("A animação não terminou")


def testar():
    assert len(r.legais(r.inicial()))==7
    assert sum(p!="." for p in r.inicial().tabuleiro)==24
    p=posicao({"c5":"P","d4":"p","h8":"p"})
    lances=r.legais(p)
    assert len(lances)==1 and lances[0].pousos==(casa("e3"),)
    assert lances[0].capturadas==(casa("d4"),)

    p=posicao({"a1":"P","b2":"p","d4":"p","h6":"P","g7":"p"})
    lances=r.legais(p)
    assert len(lances)==1
    assert lances[0].origem==casa("a1") and len(lances[0].capturadas)==2
    assert lances[0].pousos==(casa("c3"),casa("e5"))

    p=posicao({"a1":"D","c3":"p","h8":"p"})
    lances=r.legais(p)
    assert {l.destino for l in lances}=={casa(c) for c in ("d4","e5","f6","g7")}
    # A vítima permanece no caminho e impede retorno pela mesma diagonal.
    p=posicao({"d4":"D","e5":"p","c3":"p"})
    assert all(len(l.capturadas)==1 for l in r.legais(p))
    assert all(len(set(l.capturadas))==len(l.capturadas) for l in r.legais(p))

    p=posicao({"c6":"P","d7":"p","f7":"p","a8":"p"})
    lance=r.legais(p)[0]
    assert lance.pousos==(casa("e8"),casa("g6"))
    assert r.aplicar(p,lance).tabuleiro[casa("g6")]=="P"
    p=posicao({"c6":"P","d7":"p"})
    lance=r.legais(p)[0]
    assert r.aplicar(p,lance).tabuleiro[casa("e8")]=="D"

    assert "bloqueio" in Partida(posicao({"a1":"P","b2":"p","c3":"p"})).resultado
    partida=Partida(posicao({"a1":"P","b2":"p"}))
    assert partida.jogar(partida.lances()[0])
    assert "eliminação" in partida.resultado

    p=posicao({"a1":"D","h8":"d","h6":"p"},contador=39)
    partida=Partida(p)
    lance=next(l for l in partida.lances() if not l.capturadas)
    assert partida.jogar(lance)
    assert "20 lances" in partida.resultado
    partida=Partida(posicao({"a1":"D","h6":"d","f8":"p"}))
    chave=r.identidade(partida.posicao)
    partida.repeticoes[chave]=2
    partida._registrar()
    assert "tripla" in partida.resultado

    p=posicao({"a1":"D","h6":"d"})
    partida=Partida(p)
    partida.contagem_final=9
    assert partida.jogar(next(l for l in partida.lances() if l.destino==casa("b2")))
    assert "final limitado" in partida.resultado
    assert r.final_limitado(posicao({"a1":"D","b8":"d","d8":"d","f8":"p"}))[1]==5

    s=Sessao()
    lance=x.Lance(casa("e2"),casa("e4"))
    s.executar(lance)
    terminar_animacao(s)
    estado_xadrez=s.partida.posicao
    assert s.virar()
    terminar_animacao(s)
    assert s.lado==1
    lance=s.partida.lances()[0]
    s.selecionar(lance.origem)
    s.selecionar(lance.destino)
    terminar_animacao(s)
    estado_damas=s.partida.posicao
    assert s.virar()
    terminar_animacao(s)
    assert s.lado==0 and s.partida.posicao==estado_xadrez
    assert s.partidas[1].posicao==estado_damas

    s.reiniciar()
    assert s.partidas[1].posicao==estado_damas
    assert not s.partida.historico
    # Soltar antes da metade cancela, depois da metade troca de lado.
    for proporcao,lado in ((0.3,0),(0.8,1)):
        assert s.virar(True)
        s.virada.arrastar(-240*proporcao)
        s.virada.soltar()
        terminar_animacao(s)
        assert s.lado==lado

    s.partidas[1]=Partida(posicao({"a1":"P","b2":"p","d4":"p","h8":"p"}))
    s.selecionar(casa("a1"))
    s.selecionar(casa("c3"))
    assert s.passos==(casa("c3"),) and not s.partida.historico
    terminar_animacao(s)
    assert not s.virar()
    assert s.destinos=={casa("e5")}
    s.selecionar(casa("e5"))
    assert len(s.partida.historico)==1
    terminar_animacao(s)
    assert s.partida.posicao.tabuleiro[casa("b2")]=="."
    assert s.partida.posicao.tabuleiro[casa("d4")]=="."
    print("Testes de damas, capturas múltiplas e sessão passaram.")


if __name__=="__main__":
    testar()
