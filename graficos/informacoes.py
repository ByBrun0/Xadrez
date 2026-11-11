"""Faixa permanente e aviso de turno, com texto em textura como nas aulas 16–17."""
import textwrap

from PIL import Image, ImageDraw

from animacao import suave
from .painel import dimensoes
from .tabuleiro import fonte


class Informacoes:
    def __init__(self):
        self.chave = None
        self.chave_turno = None
        self.aviso = ""
        self.tempo_aviso = 0
        self.duracao_aviso = 2.0

    def atualizar(self, dt, interface):
        self.tempo_aviso = max(0, self.tempo_aviso - dt)
        sessao = interface.sessao
        if sessao.bloqueada or interface.apresentacao.modo in ("menu","introducao"):
            return
        partida = sessao.partida
        chave = (sessao.lado, len(partida.historico), partida.posicao.turno,
                 partida.resultado)
        if chave != self.chave_turno:
            self.chave_turno = chave
            lado = "brancas" if partida.posicao.turno == 1 else "pretas"
            self.aviso = partida.resultado or f"É a vez das {lado}"
            self.tempo_aviso = self.duracao_aviso

    def retangulo(self, largura):
        _, painel = dimensoes(largura)
        return 12, 12, min(740, largura - painel - 36), 78

    def contem(self, x, y, largura):
        a, b, comprimento, altura = self.retangulo(largura)
        faixa = a <= x <= a + comprimento and b <= y <= b + altura
        aviso = (self.tempo_aviso > 0 and a <= x <= a + min(comprimento, 440)
                 and 100 <= y <= 148)
        return faixa or aviso

    def gerar(self, interface, largura):
        sessao = interface.sessao
        partida = sessao.partida
        lado = "Brancas" if partida.posicao.turno == 1 else "Pretas"
        jogo = "DAMAS" if sessao.lado else "XADREZ"
        turno = partida.resultado or f"Vez das {lado.lower()}"
        if sessao.virada:
            turno = "Virando o tabuleiro"
        elif sessao.animacao:
            turno = "Jogada em andamento"
        detalhe = "Clique ou arraste uma peça · Menu na borda direita"
        if interface.confirmacao:
            detalhe = interface.confirmacao + "? Enter confirma · Esc cancela"
        elif sessao.promocao:
            detalhe = "Promoção · Escolha dama, torre, bispo ou cavalo no menu"
        elif sessao.passos:
            total=max(len(l.capturadas) for l in sessao.opcoes)
            detalhe = f"Captura múltipla {len(sessao.passos)}/{total} · Continue com a mesma peça"
        elif interface.em_xeque and not partida.resultado:
            detalhe = "XEQUE · Proteja seu rei"
        elif sessao.lado and not partida.resultado:
            total=max((len(l.capturadas) for l in partida.lances()),default=0)
            if total:
                unidade="peça" if total==1 else "peças"
                detalhe = f"Captura obrigatória · A sequência deve capturar {total} {unidade}"
        if sessao.aviso:
            detalhe = sessao.aviso
        if interface.apresentacao.modo=="introducao":
            turno="Preparando a partida"
            detalhe="Aproximando a câmera · Esc pula a apresentação"
        elif interface.apresentacao.modo=="contemplacao":
            detalhe="Contemplando a praça · C ou Esc volta ao jogo"
        sobre=interface.descricao_sobre if not partida.resultado else ""
        comprimento = self.retangulo(largura)[2]
        chave = (jogo, turno, detalhe, comprimento, sobre)
        if chave == self.chave:
            return None
        self.chave = chave
        imagem = Image.new("RGB", (comprimento, 78), (29, 39, 35))
        desenho = ImageDraw.Draw(imagem)
        desenho.rectangle((0, 0, 3, 78), fill=(201, 163, 96))
        desenho.text((16, 10), jogo, font=fonte(13), fill=(201, 163, 96))
        for i, linha in enumerate(textwrap.wrap(turno, max(20, (comprimento - 130) // 9))[:2]):
            desenho.text((112, 8 + i * 21), linha, font=fonte(17), fill=(238, 225, 195))
        desenho.text((16, 54), detalhe, font=fonte(12), fill=(179, 193, 175))
        if sobre:
            desenho.text((comprimento-16,22),sobre,font=fonte(12),
                         fill=(201,163,96),anchor="rm")
        return imagem

    def imagem_aviso(self):
        imagem = Image.new("RGB", (440, 38), (42, 55, 44))
        desenho = ImageDraw.Draw(imagem)
        desenho.text((220, 19), self.aviso, font=fonte(16),
                     fill=(231, 210, 163), anchor="mm")
        return imagem

    @property
    def abertura_aviso(self):
        entrada = suave((self.duracao_aviso - self.tempo_aviso) / 0.2)
        saida = suave(self.tempo_aviso / 0.25)
        return min(entrada, saida)

    @property
    def deslocamento_aviso(self):
        return 10 * (1 - self.abertura_aviso)
