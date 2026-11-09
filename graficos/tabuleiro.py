from math import floor

from PIL import Image, ImageDraw, ImageFont

from configuracao import PLANO, CENTRO_TABULEIRO, BRONZE
from .malhas import Malha, caixa, chanfrada, translacao, rotacao


def centro(casa):
    return 3.5-casa%8, casa//8-3.5


def casa_em(x,z):
    coluna, linha = floor(4-x), floor(z+4)
    if 0 <= linha < 8 and 0 <= coluna < 8:
        return linha*8+coluna
    return None


def fonte(tamanho):
    for nome in ("C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nome,tamanho)
        except OSError:
            pass
    return ImageFont.load_default(size=tamanho)


def textura_face(damas=False):
    imagem = Image.new("RGB",(1024,1024),(53,32,21))
    desenho = ImageDraw.Draw(imagem)
    desenho.rounded_rectangle((8,8,1016,1016),radius=32,outline=(174,125,65),width=4)
    cores = ((39,84,66),(221,217,187)) if damas else ((95,57,35),(225,207,170))
    # UV da face corresponde ao eixo x/z do mundo.
    for linha in range(8):
        for coluna in range(8):
            x, y = 64+coluna*112,64+linha*112
            cor = cores[(linha+coluna)%2]
            desenho.rectangle((x,y,x+112,y+112), fill=cor)
            # Traços sutis de madeira, sem substituir a leitura das casas.
            for faixa in range(8):
                yy = y+faixa*14
                tom = tuple(max(0,c-4) for c in cor)
                desenho.line((x,yy,x+112,yy+2),fill=tom,width=1)
    letra = fonte(23)
    for i in range(8):
        # x do mundo cresce para a esquerda do jogador branco.
        desenho.text((120+i*112,32),"hgfedcba"[i],font=letra,fill=(219,180,118),anchor="mm")
        desenho.text((32,120+i*112),str(8-i),font=letra,fill=(219,180,118),anchor="mm")
    return imagem


def criar():
    corpo = chanfrada(9.15,0.32,9.15,0.20)
    detalhes = Malha()
    for x in (-4.50,4.50):
        detalhes.juntar(caixa(0.035,0.22,8.6),translacao(x,0,0))
    for z in (-4.50,4.50):
        detalhes.juntar(caixa(8.6,0.22,0.035),translacao(0,0,z))
    face = Malha()
    # A área interna de 8x8 ocupa 896/1024 da textura.
    tamanho = 4*1024/896
    face.quad(((-tamanho,0.18,-tamanho),(-tamanho,0.18,tamanho),
               (tamanho,0.18,tamanho),(tamanho,0.18,-tamanho)),
              (0,1,0),uvs=((0,0),(0,1),(1,1),(1,0)))
    alca = Malha()
    for centro_z in (-3,3):
        for z in (-0.62,0.62):
            alca.juntar(caixa(0.48,0.13,0.12),translacao(4.76,0,z+centro_z))
        alca.juntar(caixa(0.13,0.13,1.35),translacao(4.99,0,centro_z))
    return corpo, detalhes, face, alca
