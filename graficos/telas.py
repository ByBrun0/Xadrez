"""Tela inicial e resultado desenhados com Pillow e texturas já usadas no jogo."""
import textwrap

from PIL import Image, ImageDraw

from .mapas import MAPAS
from .tabuleiro import fonte


class Telas:
    def __init__(self):
        self.chave = None
        self.imagem = None
        self.botoes = []

    def gerar(self, interface):
        modo = interface.apresentacao.modo
        partida = interface.sessao.partida
        chave = (modo, interface.mapa, interface.qualidade,
                 partida.resultado, len(partida.historico), interface.sessao.capturadas())
        if chave == self.chave:
            return None
        self.chave = chave
        self.botoes = []
        altura = 540 if modo == "menu" else 360
        imagem = Image.new("RGB", (720, altura), (29, 39, 35))
        desenho = ImageDraw.Draw(imagem)
        desenho.rectangle((0, 0, 4, altura), fill=(201, 163, 96))

        def botao(codigo, texto, retangulo):
            desenho.rounded_rectangle(retangulo, radius=8, fill=(54, 72, 56),
                                       outline=(139, 156, 107))
            a, b, c, d = retangulo
            desenho.text(((a+c)/2, (b+d)/2), texto, font=fonte(18),
                         fill=(239, 225, 193), anchor="mm")
            self.botoes.append((retangulo, codigo))

        if modo == "menu":
            desenho.text((36, 26), "Praça dos Dois Jogos", font=fonte(32), fill=(239, 225, 193))
            desenho.text((36, 72), "Escolha o ambiente e o jogo para começar",
                         font=fonte(16), fill=(178, 194, 174))
            for i, mapa in enumerate(("dia", "noite")):
                x = 36 + i*336
                retangulo = (x, 108, x+312, 288)
                ambiente = MAPAS[mapa]
                desenho.rounded_rectangle(retangulo, 10, fill=ambiente.ceu_superior,
                                           outline=(224, 181, 100) if interface.mapa == mapa else (91, 112, 89),
                                           width=4 if interface.mapa == mapa else 1)
                desenho.ellipse((x+245, 126, x+282, 163), fill=tuple(int(c*255) for c in ambiente.cor_astro))
                desenho.rectangle((x+6, 214, x+306, 280), fill=(54, 76, 49))
                for arvore_x in (x+45, x+264):
                    desenho.rectangle((arvore_x-4, 185, arvore_x+4, 230), fill=(95, 62, 35))
                    desenho.ellipse((arvore_x-24, 149, arvore_x+24, 199), fill=(73, 103, 53))
                desenho.rectangle((x+93, 214, x+220, 226), fill=(173, 153, 112))
                desenho.rectangle((x+105, 226, x+113, 254), fill=(133, 128, 110))
                desenho.rectangle((x+199, 226, x+207, 254), fill=(133, 128, 110))
                desenho.text((x+156, 267), ambiente.nome, font=fonte(17),
                             fill=(245, 230, 197), anchor="mm")
                self.botoes.append((retangulo, "escolher_"+mapa))
            botao("iniciar_xadrez", "Jogar xadrez", (36, 326, 348, 378))
            botao("iniciar_damas", "Jogar damas", (372, 326, 684, 378))
            botao("qualidade", "Qualidade "+interface.qualidade.capitalize(), (36, 408, 684, 450))
            desenho.text((36, 478), "X joga xadrez · D joga damas · M troca o mapa",
                         font=fonte(14), fill=(178, 194, 174))
            desenho.text((36, 503), "Dois jogadores no mesmo computador", font=fonte(14), fill=(201, 163, 96))
        else:
            desenho.text((36, 26), "Fim da partida", font=fonte(30), fill=(239, 225, 193))
            for i, linha in enumerate(textwrap.wrap(partida.resultado, 53)):
                desenho.text((36, 82+i*26), linha, font=fonte(21), fill=(222, 184, 112))
            desenho.text((36, 142), f"{len(partida.historico)} lances jogados",
                         font=fonte(15), fill=(178, 194, 174))
            botao("revanche", "Revanche", (36, 185, 348, 232))
            botao("outro_jogo", "Trocar de jogo", (372, 185, 684, 232))
            botao("observar", "Continuar observando", (36, 258, 684, 300))
            desenho.text((36, 325), "Enter joga revanche · V troca de jogo · Esc observa",
                         font=fonte(14), fill=(178, 194, 174))
        self.imagem = imagem
        return imagem

    def retangulo(self, largura, altura):
        largura_imagem, altura_imagem = self.imagem.size
        fator = min(1, (largura-48)/largura_imagem, (altura-40)/altura_imagem)
        w, h = largura_imagem*fator, altura_imagem*fator
        return (largura-w)/2, (altura-h)/2, w, h

    def clicar(self, x, y, largura, altura):
        a, b, w, h = self.retangulo(largura, altura)
        px = (x-a)*self.imagem.width/w
        py = (y-b)*self.imagem.height/h
        for (x1, y1, x2, y2), codigo in self.botoes:
            if x1 <= px <= x2 and y1 <= py <= y2:
                return codigo
        return None
