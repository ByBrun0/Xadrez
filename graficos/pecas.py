"""Modelos de xadrez. Todos os perfis são gerados uma vez."""
import math
import numpy as np

from configuracao import BRONZE
from .malhas import Malha, revolucao, esfera, translacao, rotacao, escala, superficie_parametrica
from .modificadores import bloco_arredondado

BASE = ((0,0), (0.29,0), (0.34,0.035), (0.355,0.09),
        (0.34,0.15), (0.28,0.19), (0.265,0.22), (0.27,0.25))
PERFIS = {
    "P": ((0.22,0.29), (0.16,0.37), (0.12,0.54), (0.15,0.59),
          (0.19,0.62), (0.13,0.67)),
    "T": ((0.235,0.30), (0.21,0.42), (0.20,0.79), (0.26,0.85),
          (0.31,0.90), (0.31,1.03), (0,1.03)),
    "C": ((0.25,0.29), (0.24,0.35), (0.20,0.39), (0,0.39)),
    "B": ((0.22,0.29), (0.16,0.39), (0.115,0.78), (0.16,0.87),
          (0.23,0.91), (0.22,0.97), (0.12,1.01)),
    "D": ((0.23,0.29), (0.17,0.43), (0.13,0.92), (0.18,1.03),
          (0.25,1.07), (0.25,1.12), (0.18,1.18), (0.19,1.23), (0,1.23)),
    "R": ((0.23,0.29), (0.17,0.44), (0.145,0.99), (0.21,1.09),
          (0.25,1.13), (0.24,1.20), (0.17,1.28), (0.18,1.34), (0,1.34)),
}


def suavizar(perfil):
    pontos = []
    for i in range(len(perfil)-1):
        a, b = perfil[max(0,i-1)], perfil[i]
        c, d = perfil[i+1], perfil[min(len(perfil)-1,i+2)]
        for j in range(4):
            t = j / 4
            valor = []
            for k in range(2):
                v = 0.5*((2*b[k])+(-a[k]+c[k])*t+
                         (2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+
                         (-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t)
                valor.append(max(0, v) if k == 0 else v)
            pontos.append(tuple(valor))
    return pontos + [perfil[-1]]


def cavalo(segmentos):
    # Centro do pescoço por Bézier cúbica, conforme os pesos da aula 22.
    controles = np.array(((0.38,-0.05), (0.68,-0.24), (1.05,-0.20), (1.24,0.03)))

    def pescoco(u,v):
        pesos = np.array(((1-u)**3, 3*u*(1-u)**2, 3*u*u*(1-u), u**3))
        y,z = pesos @ controles
        angulo = math.tau*v
        largura = 0.18 - 0.065*u
        profundidade = 0.23 - 0.09*u
        return largura*math.cos(angulo), y, z+profundidade*math.sin(angulo)

    malha = superficie_parametrica(pescoco, 18, segmentos)
    malha.juntar(esfera(1,segmentos),
                 translacao(0,1.12,0.15)@rotacao(12,"x")@escala(0.14,0.16,0.24))
    malha.juntar(esfera(1,segmentos),
                 translacao(0,1.04,0.32)@escala(0.12,0.105,0.16))
    perfil_orelha = ((0,0), (0.055,0), (0.065,0.07), (0.03,0.22), (0,0.26))
    for x in (-0.075,0.075):
        malha.juntar(revolucao(perfil_orelha,16),translacao(x,1.23,-0.02))
    return malha


def mitra(segmentos):
    """Duas metades paramétricas, fechadas nas faces internas do recorte."""
    malha = Malha()
    perfil = ((0.11,0), (0.19,0.16), (0.21,0.36), (0.17,0.58), (0.09,0.85), (0,1))
    for sinal in (-1,1):
        def superficie(u,v):
            raio = np.interp(u, [p[1] for p in perfil], [p[0] for p in perfil])
            y = 1.04 + (0.47 if sinal==1 else 0.40)*u
            angulo = math.pi*v + (0 if sinal==1 else math.pi)
            corte = 0.40*(y-1.20) + sinal*0.025*u
            return raio*math.cos(angulo), y, corte+raio*math.sin(angulo)
        malha.juntar(superficie_parametrica(superficie,24,max(12,segmentos//2)))
        for i in range(24):
            u1,u2 = i/24,(i+1)/24
            pontos = (superficie(u1,0),superficie(u2,0),
                      superficie(u2,1),superficie(u1,1))
            malha.quad(pontos,(0,0.40*sinal,-sinal))
    return malha


def coroa(segmentos):
    def superficie(u,v):
        angulo = math.tau*v
        raio = 0.18+0.10*u
        altura = 1.20+0.12*u+0.10*u**3*(0.5+0.5*math.cos(8*angulo))
        return raio*math.cos(angulo),altura,raio*math.sin(angulo)
    return superficie_parametrica(superficie,8,max(48,segmentos*2))


def acabamento(malha):
    """Variação de cor nos vértices, usando o RGB da aula 15."""
    for indice,vertice in enumerate(malha.vertices):
        x,y,z = vertice[:3]
        veio = math.sin(32*x+14*z+2*math.sin(6*y))
        tom = 0.96+0.035*veio+0.025*min(1,y)
        malha.vertices[indice] = (*vertice[:8], tom, tom*0.99, tom*0.97)


def criar_modelos(segmentos):
    modelos = {}
    for tipo, perfil in PERFIS.items():
        corpo = revolucao(suavizar(BASE + perfil), segmentos)
        detalhe = revolucao(((0.29,0.19),(0.295,0.21),(0.28,0.235)), segmentos)
        escuro = revolucao(((0.29,0.005),(0.31,0.012),(0.31,0.026),(0.32,0.033)),segmentos)
        if tipo == "P":
            corpo.juntar(esfera(0.205,segmentos), translacao(0,0.81,0))
        elif tipo == "C":
            corpo.juntar(cavalo(segmentos))
            for x in (-0.133,0.133):
                escuro.juntar(esfera(0.024,12), translacao(x,1.18,0.18))
                escuro.juntar(esfera(0.015,10), translacao(x*0.75,1.08,0.43))
        elif tipo == "T":
            for i in range(6):
                matriz = rotacao(i*60) @ translacao(0,1.10,0.25)
                corpo.juntar(bloco_arredondado(0.19,0.16,0.16), matriz)
        elif tipo == "B":
            corpo.juntar(mitra(segmentos))
        elif tipo == "D":
            corpo.juntar(coroa(segmentos))
            for i in range(8):
                angulo = math.tau*i/8
                detalhe.juntar(esfera(0.035,12),
                               translacao(0.28*math.cos(angulo),1.42,0.28*math.sin(angulo)))
            corpo.juntar(esfera(0.065,16),translacao(0,1.40,0))
        elif tipo == "R":
            detalhe.juntar(bloco_arredondado(0.085,0.32,0.085),translacao(0,1.49,0))
            detalhe.juntar(bloco_arredondado(0.26,0.085,0.085),translacao(0,1.52,0))
        acabamento(corpo)
        modelos[tipo] = (corpo, detalhe, escuro)
    return modelos
