"""Painel 2D desenhado com Pillow e enviado como textura só quando muda."""
import textwrap

from PIL import Image, ImageDraw

from configuracao import PAINEL_LARGURA
from .tabuleiro import fonte


def dimensoes(largura):
    """A cena ocupa toda a janela. O painel se sobrepõe à margem direita."""
    painel=min(PAINEL_LARGURA,max(210,int(largura*0.27)))
    return largura,painel


class Painel:
    def __init__(self):
        self.chave=None
        self.imagem=None
        self.botoes=[]
        self.abertura = 1.0
        self.ausencia = 0.0

    def limites(self, largura):
        _, painel = dimensoes(largura)
        aba = painel * 24 / 276
        visivel = aba + (painel - aba) * self.abertura
        return largura - visivel, painel

    def atualizar(self, dt, cursor, largura, altura, manter_aberto=False):
        esquerda, _ = self.limites(largura)
        sobre_menu = esquerda <= cursor[0] <= largura and 0 <= cursor[1] <= altura
        if sobre_menu or manter_aberto:
            self.ausencia = 0
        else:
            self.ausencia += dt
        alvo = 1.0 if sobre_menu or manter_aberto or self.ausencia < 1.0 else 0.0
        passo = min(abs(alvo - self.abertura), dt * 5)
        self.abertura += passo if alvo > self.abertura else -passo

    def gerar(self,interface):
        s=interface.sessao
        p=s.partida
        chave=(s.lado,p.posicao,p.resultado,p.oferta,s.aviso,bool(s.virada),
               bool(s.animacao),bool(interface.arraste),s.passos,tuple(s.promocao),s.reivindicacao,
               interface.confirmacao,interface.ajuda,interface.giro_automatico,
               interface.qualidade,interface.metricas,bool(interface.camera.restante),interface.mapa,
               interface.apresentacao.modo)
        if chave==self.chave:
            return None
        self.chave=chave
        imagem=Image.new("RGB",(276,800),(29,39,35))
        d=ImageDraw.Draw(imagem)
        creme=(232,220,191)
        ouro=(201,163,96)
        suave=(158,176,157)
        d.rectangle((0,0,3,800),fill=ouro)
        aba = Image.new("RGB", (90, 18), (29, 39, 35))
        ImageDraw.Draw(aba).text((6, 0), "≡ MENU", font=fonte(12), fill=ouro)
        imagem.paste(aba.rotate(90, expand=True), (4, 350))
        d.text((24,26),"PRAÇA",font=fonte(31),fill=creme)
        d.text((25,66),"DOS DOIS JOGOS",font=fonte(15),fill=ouro)
        d.line((24,102,252,102),fill=(73,88,72))
        nome="DAMAS BRASILEIRAS" if s.lado else "XADREZ"
        d.text((24,122),nome,font=fonte(18),fill=creme)
        lado="Brancas" if p.posicao.turno==1 else "Pretas"
        estado=p.resultado or ("Vez das "+lado.lower())
        if s.virada:
            estado="Virando o tabuleiro..."
        for i,linha in enumerate(textwrap.wrap(estado,24)):
            d.text((24,158+i*24),linha,font=fonte(17),fill=ouro)
        capturadas=s.capturadas()
        d.text((24,222),f"Capturadas   claras {capturadas[0]}  ·  escuras {capturadas[1]}",
               font=fonte(12),fill=suave)
        d.text((24,244),f"Lances jogados   {len(p.historico)}",font=fonte(12),fill=suave)
        self.botoes=[]

        def botao(codigo,texto,y,ativo=True,x=24,largura=228):
            ret=(x,y,x+largura,y+32)
            d.rounded_rectangle(ret,8,fill=(51,67,55) if ativo else (37,47,41),
                                outline=(98,116,84) if ativo else (52,65,54))
            d.text((x+12,y+9),texto,font=fonte(14),fill=creme if ativo else (100,113,101))
            if ativo:
                self.botoes.append((ret,codigo))

        ocupado=interface.ocupada or bool(interface.camera.restante)
        livre=(not ocupado and not s.passos and not s.promocao and not interface.confirmacao
               and interface.apresentacao.permite_jogar)
        if s.promocao:
            d.text((24,286),"Escolha a promoção",font=fonte(17),fill=ouro)
            for i,(codigo,nome,simbolo) in enumerate((("D","Dama","♕"),("T","Torre","♖"),
                                                   ("B","Bispo","♗"),("C","Cavalo","♘"))):
                x=24+(i%2)*118
                y=326+(i//2)*86
                d.text((x+38,y),simbolo,font=fonte(32),fill=creme)
                botao(codigo,codigo+" · "+nome,y+38,True,x,110)
        else:
            comandos=(
                ("virar","Virar para "+("xadrez" if s.lado else "damas"), livre),
                ("camera","Restaurar câmera",not ocupado),
                ("giro","Giro por turno   "+("ligado" if interface.giro_automatico else "desligado"),not ocupado),
                ("qualidade","Qualidade   "+interface.qualidade,not ocupado),
                ("mapa","Mapa   "+("Dia" if interface.mapa=="dia" else "Noite"),not ocupado),
                ("contemplar","Voltar ao jogo" if interface.apresentacao.modo=="contemplacao"
                 else "Contemplar a praça",not ocupado and not s.passos and not s.promocao),
                ("novo","Nova partida",livre),
                ("empate","Aceitar empate" if p.oferta==-p.posicao.turno else "Oferecer empate",
                 livre and not p.resultado),
                ("abandono","Abandonar",livre and not p.resultado),
                ("reivindicar","Reivindicar empate",livre and not p.resultado and not s.lado),
                ("ajuda","Ajuda e controles",True),
            )
            for i,(codigo,texto,ativo) in enumerate(comandos):
                botao(codigo,texto,280+i*35,ativo)

        mensagem=s.aviso
        if interface.confirmacao:
            mensagem=interface.confirmacao+"? Enter confirma · Esc cancela."
        elif s.passos:
            mensagem="Continue a captura na próxima casa marcada."
        elif s.reivindicacao:
            mensagem="Escolha o lance para reivindicar. Esc cancela."
        elif not mensagem and p.oferta is not None:
            mensagem="Empate oferecido. O adversário pode aceitar após seu lance."
        elif not mensagem and not s.lado and interface.em_xeque:
            mensagem="Xeque. Proteja seu rei."
        if interface.ajuda:
            mensagem="Clique ou arraste para jogar. V vira. C contempla. M troca mapa. Q troca qualidade. Passe o mouse na aba para abrir o menu."
        for i,linha in enumerate(textwrap.wrap(mensagem or "Dois jogos. Uma mesa. Seu tempo.",29)):
            d.text((24,687+i*17),linha,font=fonte(12),fill=ouro)
        d.text((24,775),interface.metricas,font=fonte(11),fill=suave)
        self.imagem=imagem
        return imagem

    def clicar(self,x,y,largura,altura):
        esquerda,painel=self.limites(largura)
        if x<esquerda or x>largura:
            return None
        px=(x-esquerda)*276/painel
        py=y*800/altura
        for (a,b,c,d),codigo in self.botoes:
            if a<=px<=c and b<=py<=d:
                return codigo
        return "painel"
