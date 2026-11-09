from . import regras


class Partida:
    def __init__(self, posicao=None):
        self.posicao = posicao or regras.inicial()
        self.historico = []
        self.resultado = ""
        self.oferta = None
        self.ultima_oferta = None
        self.repeticoes = {}
        self.familia = None
        self.contagem_final = 0
        self._registrar()

    def lances(self, origem=None):
        if self.resultado:
            return []
        return [l for l in self._legais if origem is None or l.origem == origem]

    def _registrar(self):
        self._legais = regras.legais(self.posicao)
        chave = regras.identidade(self.posicao)
        total = self.repeticoes.get(chave, 0) + 1
        self.repeticoes[chave] = total
        familia, limite = regras.final_limitado(self.posicao)
        if familia != self.familia:
            self.familia = familia
            self.contagem_final = 0
        elif familia:
            self.contagem_final += 1
        if not self._legais:
            lado = "Pretas" if self.posicao.turno == 1 else "Brancas"
            self.resultado = f"{lado} vencem por eliminação ou bloqueio"
        elif total >= 3:
            self.resultado = "Empate por tripla repetição"
        elif self.posicao.meios_lances >= 40:
            self.resultado = "Empate por 20 lances de cada lado"
        elif familia and self.contagem_final >= limite * 2:
            self.resultado = "Empate por final limitado de 5 lances"

    def jogar(self, lance):
        if lance not in self.lances(lance.origem):
            return False
        if self.oferta != self.posicao.turno:
            self.oferta = None
        self.posicao = regras.aplicar(self.posicao, lance)
        self.historico.append(lance)
        self._registrar()
        return True

    def oferecer_ou_aceitar(self):
        if self.resultado:
            return False
        if self.oferta == -self.posicao.turno:
            self.resultado = "Empate por acordo"
            return True
        if len(self.historico) < 40 or self.ultima_oferta == self.posicao.turno:
            return False
        self.oferta = self.posicao.turno
        self.ultima_oferta = self.posicao.turno
        return True

    def abandonar(self):
        if not self.resultado:
            lado = "Pretas" if self.posicao.turno == 1 else "Brancas"
            self.resultado = f"{lado} vencem por abandono"
