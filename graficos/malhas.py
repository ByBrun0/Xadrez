"""Malhas trianguladas criadas na inicialização e reutilizadas pela GPU."""
import math

import numpy as np


def translacao(x=0, y=0, z=0):
    matriz = np.eye(4)
    matriz[:3, 3] = (x, y, z)
    return matriz


def escala(x=1, y=None, z=None):
    return np.diag((x, x if y is None else y, x if z is None else z, 1))


def rotacao(graus, eixo="y"):
    c, s = math.cos(math.radians(graus)), math.sin(math.radians(graus))
    matriz = np.eye(4)
    a, b = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[eixo]
    matriz[a, a] = matriz[b, b] = c
    matriz[a, b], matriz[b, a] = -s, s
    return matriz


class Malha:
    def __init__(self):
        self.vertices = []

    def triangulo(self, pontos, normal=None, cor=(1, 1, 1), uvs=None):
        if normal is None:
            normal = np.cross(np.subtract(pontos[1], pontos[0]),
                              np.subtract(pontos[2], pontos[0]))
            tamanho = np.linalg.norm(normal)
            if tamanho < 1e-10:
                return
            normal = normal / tamanho
        if uvs is None:
            uvs = ((0, 0), (1, 0), (1, 1))
        for ponto, uv in zip(pontos, uvs):
            self.vertices.append((*ponto, *normal, *uv, *cor))

    def quad(self, pontos, normal=None, cor=(1, 1, 1), uvs=None):
        uvs = uvs or ((0, 0), (1, 0), (1, 1), (0, 1))
        for indices in ((0, 1, 2), (0, 2, 3)):
            self.triangulo([pontos[i] for i in indices], normal, cor,
                            [uvs[i] for i in indices])

    def juntar(self, outra, matriz=None, cor=(1, 1, 1)):
        if not outra.vertices:
            return self
        dados = np.array(outra.vertices, dtype=float)
        matriz = np.eye(4) if matriz is None else matriz
        pontos = np.column_stack((dados[:, :3], np.ones(len(dados))))
        dados[:, :3] = (pontos @ matriz.T)[:, :3]
        dados[:, 3:6] = dados[:, 3:6] @ np.linalg.inv(matriz[:3, :3])
        dados[:, 8:11] *= cor
        self.vertices.extend(dados.tolist())
        return self


def caixa(largura=1, altura=1, profundidade=1):
    x, y, z = largura / 2, altura / 2, profundidade / 2
    malha = Malha()
    faces = (
        ((0,1,0), ((-x,y,-z),(-x,y,z),(x,y,z),(x,y,-z))),
        ((0,-1,0), ((-x,-y,-z),(x,-y,-z),(x,-y,z),(-x,-y,z))),
        ((0,0,1), ((-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z))),
        ((0,0,-1), ((x,-y,-z),(-x,-y,-z),(-x,y,-z),(x,y,-z))),
        ((1,0,0), ((x,-y,z),(x,-y,-z),(x,y,-z),(x,y,z))),
        ((-1,0,0), ((-x,-y,-z),(-x,-y,z),(-x,y,z),(-x,y,-z))),
    )
    for normal, pontos in faces:
        malha.quad(pontos, normal)
    return malha


def revolucao(perfil, segmentos=40, cor=(1, 1, 1)):
    malha = Malha()
    for (r1, y1), (r2, y2) in zip(perfil, perfil[1:]):
        dr, dy = r2 - r1, y2 - y1
        norma = math.hypot(dr, dy)
        if norma < 1e-9:
            continue
        for i in range(segmentos):
            angulos = (math.tau * i / segmentos, math.tau * (i + 1) / segmentos)
            pontos, normais, uvs = [], [], []
            for raio, y, angulo in ((r1,y1,angulos[0]), (r1,y1,angulos[1]),
                                   (r2,y2,angulos[1]), (r2,y2,angulos[0])):
                x, z = math.cos(angulo), math.sin(angulo)
                pontos.append((raio * x, y, raio * z))
                normais.append((dy * x / norma, -dr / norma, dy * z / norma))
                uvs.append((angulo / math.tau, y))
            for indices in ((0,1,2), (0,2,3)):
                for j in indices:
                    malha.vertices.append((*pontos[j], *normais[j], *uvs[j], *cor))
    return malha


def esfera(raio, segmentos=24):
    perfil = [(raio * math.sin(math.pi * i / 16),
               -raio * math.cos(math.pi * i / 16)) for i in range(17)]
    return revolucao(perfil, segmentos)


def superficie_parametrica(funcao, amostras_u, amostras_v):
    """Grade paramétrica da aula 22, com normais calculadas pelas tangentes."""
    valores_u = np.linspace(0, 1, amostras_u + 1)
    valores_v = np.linspace(0, 1, amostras_v + 1)
    pontos = np.array([[funcao(u, v) for v in valores_v] for u in valores_u])
    tangente_u, tangente_v = np.gradient(pontos, axis=(0, 1))
    normais = np.cross(tangente_u, tangente_v)
    tamanhos = np.linalg.norm(normais, axis=2, keepdims=True)
    normais /= np.maximum(tamanhos, 1e-10)
    normais[tamanhos[:, :, 0] < 1e-10] = (0, 1, 0)
    malha = Malha()
    for i in range(amostras_u):
        for j in range(amostras_v):
            indices = ((i,j), (i+1,j), (i+1,j+1), (i,j), (i+1,j+1), (i,j+1))
            for a,b in indices:
                malha.vertices.append((*pontos[a,b], *normais[a,b],
                                       valores_v[b], valores_u[a], 1, 1, 1))
    return malha


def chanfrada(largura, altura, profundidade, chanfro=0.12):
    """Prisma com quatro quinas cortadas e borda superior inclinada."""
    x, z = largura / 2, profundidade / 2
    contorno = ((-x+chanfro,-z), (x-chanfro,-z), (x,-z+chanfro),
                (x,z-chanfro), (x-chanfro,z), (-x+chanfro,z),
                (-x,z-chanfro), (-x,-z+chanfro))
    malha = Malha()
    superior = [(a * 0.98, altura / 2, b * 0.98) for a,b in contorno]
    inferior = [(a, -altura / 2, b) for a,b in contorno]
    borda = [(a, altura / 2 - min(chanfro, altura / 3), b) for a,b in contorno]
    for i in range(8):
        j = (i+1) % 8
        malha.triangulo(((0,altura/2,0), superior[i], superior[j]), (0,1,0))
        malha.quad((inferior[i], inferior[j], borda[j], borda[i]))
        malha.quad((borda[i], borda[j], superior[j], superior[i]))
        malha.triangulo(((0,-altura/2,0), inferior[j], inferior[i]), (0,-1,0))
    return malha
