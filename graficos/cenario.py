"""Praça estática agrupada em malhas por material."""
import math
from pathlib import Path

from PIL import Image, ImageDraw

from configuracao import TOPO_MESA, BRONZE
from .malhas import Malha, caixa, chanfrada, revolucao, esfera, translacao, escala


def carregar_imagens():
    pasta = Path(__file__).resolve().parents[1] / "Aulas" / "computacao-grafica-python"
    imagens = {}
    for nome, arquivo in (("pedra","pedras.jpg"),("madeira","madeira.jpeg")):
        with Image.open(pasta/arquivo) as imagem:
            imagens[nome] = imagem.convert("RGB")
    return imagens


def criar(leve=False):
    lisos, pedra, madeira = Malha(), Malha(), Malha()

    def bloco(destino,x,y,z,l,a,p,cor,chanfro=False):
        forma = chanfrada(l,a,p) if chanfro else caixa(l,a,p)
        destino.juntar(forma,translacao(x,y,z),cor)

    # Terra e praça em degraus.
    bloco(lisos,0,-0.28,0,42,0.2,42,(0.37,0.41,0.28))
    bloco(lisos,0,-0.11,0,24,0.22,24,(0.57,0.53,0.43),True)
    for x in range(-10,11,2):
        for z in range(-10,11,2):
            bloco(lisos,x,0.015,z,1.94,0.025,1.94,(0.67,0.61,0.50))
    # Tampo e suportes de pedra clara.
    bloco(pedra,0,2.72,0,12.9,0.56,10.0,(0.93,0.89,0.79),True)
    bloco(lisos,0,2.38,0,11.8,0.13,8.8,(0.47,0.43,0.35),True)
    for x in (-3.9,3.9):
        bloco(pedra,x,1.17,0,0.9,2.34,6.7,(0.88,0.85,0.76),True)
    for z in (-6.5,6.5):
        bloco(pedra,0,1.36,z,8.9,0.35,1.6,(0.93,0.89,0.79),True)
        for x in (-3.1,3.1):
            bloco(pedra,x,0.61,z,0.8,1.22,1.20,(0.86,0.83,0.74),True)
        for deslocamento in (-0.48,0,0.48):
            bloco(madeira,0,1.565,z+deslocamento,8.45,0.07,0.42,(0.74,0.53,0.31),True)

    # Bacias laterais por onde as peças entram e saem.
    perfil = ((0.69,0),(0.80,0.07),(0.83,0.18),(0.80,0.26),
              (0.72,0.27),(0.67,0.16),(0.56,0.05),(0,0.05))
    for x in (-5.55,5.55):
        lisos.juntar(revolucao(perfil,32),translacao(x,3,0),BRONZE)
        lisos.juntar(revolucao(((0,0),(0.57,0)),32),
                     translacao(x,3.08,0),(0.065,0.045,0.03))

    # Jardins mantêm a mesa como foco.
    for x,z in ((-9,-9),(9,-9),(-9,9),(9,9)):
        bloco(pedra,x,0.27,z,3.8,0.55,3.8,(0.81,0.77,0.65),True)
        bloco(lisos,x,0.57,z,3.45,0.05,3.45,(0.25,0.31,0.15),True)
        lisos.juntar(revolucao(((0.35,0),(0.27,2.9),(0.15,4.1),(0,4.1)),20),
                     translacao(x,0.6,z),(0.31,0.20,0.12))
        copas = ((0,4.3,0,1.8),) if leve else ((0,4.3,0,1.8),(-0.8,4.7,0.4,1.45),(0.8,5.1,-0.3,1.5))
        for dx,y,dz,raio in copas:
            lisos.juntar(esfera(raio,16 if leve else 24),
                         translacao(x+dx,y,z+dz) @ escala(1,0.85,1),
                         (0.39+dx*0.04,0.43+y*0.015,0.19))
        if not leve:
            for i in range(8):
                angulo = i*math.tau/8
                lisos.juntar(esfera(0.11,12),translacao(x+1.3*math.cos(angulo),0.68,z+1.3*math.sin(angulo)),
                             (0.77,0.40,0.20))
    for x,z in ((-10,3),(10,-3)):
        lisos.juntar(revolucao(((0.32,0),(0.32,0.16),(0.12,0.25),(0.095,5.4),(0,5.4)),20),
                     translacao(x,0,z),(0.19,0.20,0.17))
        bloco(lisos,x,5.52,z,0.52,0.8,0.52,(0.95,0.77,0.42),True)
        bloco(lisos,x,6.0,z,0.75,0.16,0.75,(0.22,0.24,0.19),True)
    for vertice in pedra.vertices:
        vertice[6] *= 2
        vertice[7] *= 2
    return {"liso":lisos,"pedra":pedra,"madeira":madeira}


def ceu():
    imagem = Image.new("RGB",(1024,512))
    desenho=ImageDraw.Draw(imagem)
    for y in range(512):
        t=y/511
        cor=tuple(round(a+(b-a)*t) for a,b in zip((174,140,145),(241,187,135)))
        desenho.line((0,y,1024,y),fill=cor)
    desenho.ellipse((730,5,810,45),fill=(252,218,160))
    return imagem
