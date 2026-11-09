"""Animações puramente visuais, independentes das regras dos dois jogos."""
import math

from configuracao import DURACAO_PASSO, DURACAO_CAPTURA, ALTURA_VIRADA
from graficos.tabuleiro import centro


def suave(t):
    t = max(0,min(1,t))
    return t*t*(3-2*t)


def bacia(peca):
    return (-5.55 if peca.isupper() else 5.55), 0


def caminho(a,b,t,altura=0):
    s=suave(t)
    return (a[0]+(b[0]-a[0])*s, altura*math.sin(math.pi*t),
            a[1]+(b[1]-a[1])*s)


class Jogada:
    def __init__(self, anterior, seguinte, lance, damas=False, inicio_pousos=0):
        self.anterior = anterior
        self.seguinte = seguinte
        self.lance = lance
        self.damas = damas
        self.tempo = 0
        self.pousos = lance.pousos if damas else (lance.destino,)
        self.capturadas = list(lance.capturadas) if damas else []
        peca = anterior[lance.origem]
        if not damas:
            if anterior[lance.destino] != ".":
                self.capturadas.append(lance.destino)
            elif peca.upper()=="P" and lance.origem%8 != lance.destino%8:
                self.capturadas.append(lance.destino-8*(1 if peca.isupper() else -1))
        self.inicio_pousos = inicio_pousos
        self.duracao = DURACAO_PASSO*max(1,len(self.pousos)-inicio_pousos)+(
            DURACAO_CAPTURA if self.capturadas else 0)+(
            0.28 if anterior[lance.origem] != seguinte[lance.destino] else 0)

    def atualizar(self,dt):
        self.tempo += dt
        return self.tempo >= self.duracao

    def instancias(self):
        origem = self.lance.origem
        peca = self.anterior[origem]
        excluidas = {origem,*self.capturadas}
        roque = not self.damas and peca.upper()=="R" and abs(self.lance.destino-origem)==2
        torre_origem = origem//8*8+(0 if self.lance.destino<origem else 7)
        if roque:
            excluidas.add(torre_origem)
        for casa,p in enumerate(self.anterior):
            if p!="." and casa not in excluidas:
                x,z=centro(casa)
                yield p,x,0,z,1,0
        passos=max(1,len(self.pousos)-self.inicio_pousos)
        fase = min(passos,self.tempo/DURACAO_PASSO)
        indice=min(passos-1,int(fase))+self.inicio_pousos
        t=min(1,fase-int(fase)) if fase<passos else 1
        anterior=origem if indice==0 else self.pousos[indice-1]
        destino=self.pousos[indice]
        salto=0.65 if self.damas or peca.upper()=="C" else 0.10
        x,y,z=caminho(centro(anterior),centro(destino),t,salto)
        fim_movimento=DURACAO_PASSO*passos
        if self.tempo>=fim_movimento:
            x,z=centro(self.lance.destino)
            y=0
            if peca!=self.seguinte[self.lance.destino]:
                promo=max(0,min(1,(self.tempo-fim_movimento-(DURACAO_CAPTURA if self.capturadas else 0))/0.28))
                y=0.22*math.sin(math.pi*promo)
                if promo>=0.5:
                    peca=self.seguinte[self.lance.destino]
        yield peca,x,y,z,1,0
        if roque:
            torre_destino=(origem+self.lance.destino)//2
            x,y,z=caminho(centro(torre_origem),centro(torre_destino),min(1,self.tempo/DURACAO_PASSO),0.10)
            yield self.anterior[torre_origem],x,y,z,1,0
        for casa in self.capturadas:
            vitima=self.anterior[casa]
            t=max(0,min(1,(self.tempo-fim_movimento)/DURACAO_CAPTURA))
            if t<1:
                x,y,z=caminho(centro(casa),bacia(vitima),t,1.15)
                yield vitima,x,y-0.20*suave(t),z,1-suave(t)**3,90*suave(t)


class Virada:
    def __init__(self,lado,manual=False):
        self.lado=lado
        self.destino=1-lado
        self.manual=manual
        self.solta=not manual
        self.progresso_arraste=0
        self.fase="recolher"
        self.tempo=0
        self.angulo=0
        self.altura=0
        self.pecas=0
        self.abertura=0
        self.concluida=False

    def arrastar(self,dy):
        if self.manual and not self.solta:
            self.progresso_arraste=max(0,min(1,-dy/240))

    def soltar(self):
        self.solta=True
        self.destino=1-self.lado if self.progresso_arraste>=0.5 else self.lado

    def atualizar(self,dt):
        self.tempo+=dt
        t=self.tempo
        if self.fase=="recolher":
            self.pecas=suave(t/0.55)
            self.abertura=self.pecas
            if t>=0.55:
                self.fase,self.tempo="erguer",0
        elif self.fase=="erguer":
            self.altura=ALTURA_VIRADA*suave(t/0.4)
            if t>=0.4:
                self.fase,self.tempo="girar",0
                self.inicio_angulo=self.angulo
        elif self.fase=="girar":
            if self.manual and not self.solta:
                self.angulo=self.progresso_arraste*180
                self.inicio_angulo=self.angulo
                self.tempo=0
            else:
                alvo=180 if self.destino!=self.lado else 0
                self.angulo=self.inicio_angulo+(alvo-self.inicio_angulo)*suave(t/0.8)
                if t>=0.8:
                    self.fase,self.tempo="baixar",0
        elif self.fase=="baixar":
            self.altura=ALTURA_VIRADA*(1-suave(t/0.4))
            if t>=0.4:
                self.fase,self.tempo="repor",0
        elif self.fase=="repor":
            self.pecas=1-suave(t/0.6)
            self.abertura=self.pecas
            if t>=0.6:
                self.concluida=True

    @property
    def lado_pecas(self):
        return self.destino if self.fase=="repor" else self.lado

    def instancias(self,tab):
        t=self.pecas
        for casa,p in enumerate(tab):
            if p==".":
                continue
            if self.fase not in ("recolher","repor"):
                continue
            # Cada peça ganha um pequeno atraso para formar uma cascata.
            fase=max(0,min(1,(t-0.15*(casa%8)/7)/0.85))
            x,y,z=caminho(centro(casa),bacia(p),fase,1.35)
            yield p,x,y-0.2*suave(fase),z,max(0.001,1-suave(fase)**3),50*suave(fase)
