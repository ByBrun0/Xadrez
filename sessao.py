"""Controla dois jogos preservados e coordena animações sem alterar regras."""
from animacao import Jogada, Virada
from damas import regras as regras_damas
from damas.partida import Partida as Damas
from xadrez import regras as regras_xadrez
from xadrez.partida import Partida as Xadrez


class Sessao:
    def __init__(self):
        self.partidas=[Xadrez(),Damas()]
        self.lado=0
        self.selecao=None
        self.opcoes=[]
        self.passos=()
        self.promocao=[]
        self.animacao=None
        self.virada=None
        self.reivindicacao=False
        self.aviso=""
        self.girar_depois=False

    @property
    def partida(self):
        return self.partidas[self.lado]

    @property
    def regras(self):
        return regras_damas if self.lado else regras_xadrez

    @property
    def bloqueada(self):
        return self.animacao is not None or self.virada is not None

    @property
    def destinos(self):
        if self.lado:
            return {l.pousos[len(self.passos)] for l in self.opcoes
                    if len(l.pousos)>len(self.passos)}
        return {l.destino for l in self.opcoes}

    def tabuleiro_visual(self):
        tab=list(self.partida.posicao.tabuleiro)
        if self.passos:
            peca=tab[self.selecao]
            tab[self.selecao]="."
            tab[self.passos[-1]]=peca
        return tuple(tab)

    def limpar(self):
        self.selecao=None
        self.opcoes=[]
        self.promocao=[]
        self.passos=()
        self.reivindicacao=False

    def selecionar(self,casa):
        if self.bloqueada or self.partida.resultado or self.promocao:
            return
        self.aviso=""
        if casa in self.destinos:
            if self.lado:
                indice=len(self.passos)
                opcoes=[l for l in self.opcoes if l.pousos[indice]==casa]
                passos=self.passos+(casa,)
                if len(passos)==len(opcoes[0].pousos):
                    self.executar(opcoes[0],ultimo_passo=True)
                else:
                    anterior=self.tabuleiro_visual()
                    origem=self.passos[-1] if self.passos else self.selecao
                    temporario=regras_damas.Lance(origem,(casa,))
                    seguinte=list(anterior)
                    seguinte[casa],seguinte[origem]=seguinte[origem],"."
                    self.animacao=Jogada(anterior,seguinte,temporario,True)
                    self.opcoes,self.passos=opcoes,passos
                return
            opcoes=[l for l in self.opcoes if l.destino==casa]
            if opcoes[0].promocao:
                self.promocao=opcoes
            else:
                self.executar(opcoes[0])
        elif not self.passos:
            if self.regras.cor(self.partida.posicao.tabuleiro[casa])==self.partida.posicao.turno:
                self.selecao=casa
                self.opcoes=self.partida.lances(casa)

    def executar(self,lance,ultimo_passo=False):
        if self.reivindicacao:
            if not self.partida.reivindicar(lance):
                self.aviso="Empate indisponível para esse lance."
            self.limpar()
            return
        anterior=self.partida.posicao.tabuleiro
        if self.partida.jogar(lance):
            inicio=len(self.passos) if ultimo_passo else 0
            self.animacao=Jogada(anterior,self.partida.posicao.tabuleiro,lance,bool(self.lado),inicio)
            self.girar_depois=True
            self.limpar()

    def virar(self,manual=False):
        if self.bloqueada or self.passos or self.promocao:
            self.aviso="Conclua a jogada antes de virar."
            return False
        self.limpar()
        self.virada=Virada(self.lado,manual)
        return True

    def atualizar(self,dt):
        girar=False
        if self.animacao and self.animacao.atualizar(dt):
            self.animacao=None
            girar=self.girar_depois
            self.girar_depois=False
        if self.virada:
            self.virada.atualizar(dt)
            if self.virada.concluida:
                self.lado=self.virada.destino
                self.virada=None
        return girar

    def reiniciar(self):
        self.partidas[self.lado]=Damas() if self.lado else Xadrez()
        self.limpar()
        self.aviso=""

    def capturadas(self):
        inicial=12 if self.lado else 16
        tab=self.partida.posicao.tabuleiro
        return tuple(inicial-sum(self.regras.cor(p)==lado for p in tab) for lado in (1,-1))
