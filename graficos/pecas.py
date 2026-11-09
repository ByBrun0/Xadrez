"""Modelos de xadrez. Todos os perfis são gerados uma vez."""
import math

from configuracao import BRONZE
from .malhas import Malha, caixa, revolucao, esfera, translacao, rotacao

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
          (0.25,1.07), (0.25,1.12), (0.18,1.18), (0.28,1.40), (0,1.40)),
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


def cavalo():
    perfil = ((-0.24,0.35), (-0.26,0.58), (-0.22,0.92), (-0.12,1.21),
              (0,1.37), (0.075,1.29), (0.15,1.19), (0.31,1.05),
              (0.40,0.99), (0.37,0.85), (0.25,0.85), (0.13,0.96),
              (0.06,0.76), (0.15,0.51), (0.23,0.36))
    # Leque em torno de um ponto interior, com recorte independente do focinho.
    triangulos = ((0,1,13), (0,13,14), (1,2,12), (1,12,13),
                  (2,3,12), (3,4,5), (3,5,6), (3,6,11), (3,11,12),
                  (6,7,11), (7,8,9), (7,9,10), (7,10,11))
    malha = Malha()
    for lado in (-1,1):
        for indices in triangulos:
            malha.triangulo([(0.145*lado, perfil[i][1], perfil[i][0]) for i in indices],
                            (lado,0,0))
    for a,b in zip(perfil, perfil[1:]+perfil[:1]):
        malha.quad(((-0.145,a[1],a[0]), (0.145,a[1],a[0]),
                    (0.145,b[1],b[0]), (-0.145,b[1],b[0])))
    # Orelhas com volume.
    for x in (-0.09,0.09):
        malha.juntar(esfera(0.09,16), translacao(x,1.31,-0.045))
    return malha


def criar_modelos(segmentos):
    modelos = {}
    for tipo, perfil in PERFIS.items():
        corpo = revolucao(suavizar(BASE + perfil), segmentos)
        detalhe = revolucao(((0.29,0.19),(0.295,0.21),(0.28,0.235)), segmentos)
        escuro = Malha()
        if tipo == "P":
            corpo.juntar(esfera(0.205,segmentos), translacao(0,0.81,0))
        elif tipo == "C":
            corpo.juntar(cavalo())
            for x in (-0.15,0.15):
                escuro.juntar(esfera(0.029,12), translacao(x,1.13,0.12))
        elif tipo == "T":
            for i in range(6):
                matriz = rotacao(i*60) @ translacao(0,1.10,0.25)
                corpo.juntar(caixa(0.16,0.18,0.16), matriz)
        elif tipo == "B":
            cabeca = revolucao(suavizar(((0.10,1.0),(0.22,1.10),(0.19,1.23),
                                         (0.07,1.39),(0,1.44))), segmentos)
            # A faixa diagonal aberta deixa o recorte característico da mitra.
            for i in range(0,len(cabeca.vertices),3):
                triangulo = cabeca.vertices[i:i+3]
                centro_y = sum(v[1] for v in triangulo)/3
                centro_z = sum(v[2] for v in triangulo)/3
                if centro_y < 1.16 or abs(centro_z-(centro_y-1.24)*0.65) > 0.035:
                    corpo.vertices.extend(triangulo)
            corpo.juntar(esfera(0.055,16), translacao(0,1.44,0))
        elif tipo == "D":
            for i in range(8):
                angulo = math.tau*i/8
                detalhe.juntar(esfera(0.052,12),
                               translacao(0.25*math.cos(angulo),1.43,0.25*math.sin(angulo)))
            corpo.juntar(esfera(0.075,16),translacao(0,1.48,0))
        elif tipo == "R":
            detalhe.juntar(caixa(0.085,0.32,0.085),translacao(0,1.49,0))
            detalhe.juntar(caixa(0.26,0.085,0.085),translacao(0,1.52,0))
        modelos[tipo] = (corpo, detalhe, escuro)
    return modelos
