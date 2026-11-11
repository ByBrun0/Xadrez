"""Curvatura e bevel adaptados de AULA24/modificadores.py do professor.

A grade compartilha vértices nas bordas. As deformações são aplicadas uma
vez e as normais são reconstruídas depois, antes do envio à GPU.
"""
import numpy as np

from .malhas import Malha


def cubo_subdividido(subdivisoes):
    vertices, faces, indices = [], [], {}
    valores = np.linspace(-1, 1, subdivisoes + 1)
    for eixo in range(3):
        outros = [i for i in range(3) if i != eixo]
        for sinal in (-1, 1):
            for i in range(subdivisoes):
                for j in range(subdivisoes):
                    face = []
                    for a, b in ((valores[i], valores[j]),
                                 (valores[i + 1], valores[j]),
                                 (valores[i + 1], valores[j + 1]),
                                 (valores[i], valores[j + 1])):
                        ponto = [0.0, 0.0, 0.0]
                        ponto[eixo] = sinal
                        ponto[outros[0]], ponto[outros[1]] = a, b
                        chave = tuple(np.round(ponto, 6))
                        if chave not in indices:
                            indices[chave] = len(vertices)
                            vertices.append(ponto)
                        face.append(indices[chave])
                    pontos = np.array([vertices[k] for k in face])
                    normal = np.cross(pontos[1] - pontos[0], pontos[2] - pontos[0])
                    if normal[eixo] * sinal < 0:
                        face.reverse()
                    faces.append(face)
    return np.array(vertices), faces


def bevel(vertices, raio):
    """Arredonda as arestas da grade, seguindo a construção da aula 24."""
    raio = np.clip(raio, 0.02, 0.45)
    interior = np.clip(vertices, -1 + raio, 1 - raio)
    direcoes = vertices - interior
    normas = np.linalg.norm(direcoes, axis=1, keepdims=True)
    return interior + raio * direcoes / np.maximum(normas, 1e-12)


def bend(vertices, intensidade):
    """Curva no plano XY. Intensidade zero preserva a geometria original."""
    resultado = vertices.copy()
    if abs(intensidade) < 1e-5:
        return resultado
    x = vertices[:, 0]
    resultado[:, 0] = np.sin(intensidade * x) / intensidade
    resultado[:, 1] += (1 - np.cos(intensidade * x)) / intensidade
    return resultado


def malha_suave(vertices, faces):
    normais = np.zeros_like(vertices)
    triangulos = []
    for a, b, c, d in faces:
        for triangulo in ((a, b, c), (a, c, d)):
            pontos = vertices[list(triangulo)]
            normal = np.cross(pontos[1] - pontos[0], pontos[2] - pontos[0])
            for indice in triangulo:
                normais[indice] += normal
            triangulos.append(triangulo)
    normais /= np.maximum(np.linalg.norm(normais, axis=1, keepdims=True), 1e-12)
    malha = Malha()
    for triangulo in triangulos:
        for indice in triangulo:
            ponto = vertices[indice]
            malha.vertices.append((*ponto, *normais[indice], ponto[0], ponto[2], 1, 1, 1))
    return malha


def banco_curvo(largura, altura, profundidade, leve=False):
    vertices, faces = cubo_subdividido(4 if leve else 8)
    vertices = bevel(vertices, 0.22)
    vertices *= (largura / 2, altura / 2, profundidade / 2)
    vertices = bend(vertices, 0.045)
    return malha_suave(vertices, faces)


def bloco_arredondado(largura, altura, profundidade):
    vertices, faces = cubo_subdividido(4)
    vertices = bevel(vertices, 0.23)
    vertices *= (largura / 2, altura / 2, profundidade / 2)
    return malha_suave(vertices, faces)
