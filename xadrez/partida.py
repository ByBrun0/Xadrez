from time import perf_counter

from . import regras

LIMITE_BUSCA_MATE = 20_000


def material_morto(posicao):
    pecas = [(i, p.upper()) for i, p in enumerate(posicao.tabuleiro)
             if p not in ".Rr"]
    if not pecas:
        return True
    if len(pecas) == 1 and pecas[0][1] in "BC":
        return True
    return all(p == "B" for _, p in pecas) and len({
        (i // 8 + i % 8) % 2 for i, _ in pecas
    }) == 1


def busca_mate(posicao, lado=None):
    # Busca cooperativa. O resultado positivo exige uma sequência até o mate.
    inicial = regras.identidade(posicao)
    pendentes = [inicial]
    visitadas = {inicial}
    while pendentes:
        atual = pendentes.pop()
        lances = list(regras.legais(atual))
        if not lances and regras.em_xeque(atual) and lado in (None, -atual.turno):
            return True
        for lance in lances:
            seguinte = regras.identidade(regras.aplicar(atual, lance))
            if seguinte not in visitadas and not material_morto(seguinte):
                if len(visitadas) >= LIMITE_BUSCA_MATE:
                    return None
                visitadas.add(seguinte)
                pendentes.append(seguinte)
        yield
    return False


class Partida:
    def __init__(self, posicao=None):
        self.posicao = regras.inicial() if posicao is None else posicao
        self.historico = []
        self.repeticoes = {}
        self.resultado = ""
        self.oferta = None
        self.busca = None
        self._registrar()

    def lances(self, origem=None):
        if self.resultado:
            return []
        return [l for l in self._legais if origem is None or l.origem == origem]

    def jogar(self, lance):
        if lance not in self.lances(lance.origem):
            return False
        if self.oferta != self.posicao.turno:
            self.oferta = None
        self.posicao = regras.aplicar(self.posicao, lance)
        self.historico.append(lance)
        self._registrar()
        return True

    def _registrar(self):
        atual = self.posicao
        chave = regras.identidade(atual)
        repeticoes = self.repeticoes.get(chave, 0) + 1
        self.repeticoes[chave] = repeticoes
        self.busca = None
        self._legais = list(regras.legais(atual))
        if not self.lances():
            if regras.em_xeque(atual):
                vencedor = "Pretas" if atual.turno == 1 else "Brancas"
                self.resultado = f"{vencedor} vencem por xeque-mate"
            else:
                self.resultado = "Empate por afogamento"
        elif material_morto(atual):
            self.resultado = "Empate por posição morta"
        elif repeticoes >= 5:
            self.resultado = "Empate por quíntupla repetição"
        elif atual.meios_lances >= 150:
            self.resultado = "Empate por 75 lances"
        else:
            self.busca = busca_mate(atual)

    def verificar_posicao_morta(self, lote=1, orcamento=0.001):
        if self.busca is None or self.resultado:
            return
        try:
            inicio = perf_counter()
            for _ in range(lote):
                next(self.busca)
                if perf_counter() - inicio >= orcamento:
                    break
        except StopIteration as fim:
            self.busca = None
            if fim.value is False:
                self.resultado = "Empate por posição morta"

    def reivindicar(self, lance=None):
        if self.resultado:
            return False
        atual = self.posicao
        if lance is not None:
            if lance not in self.lances(lance.origem):
                return False
            atual = regras.aplicar(atual, lance)
        total = self.repeticoes.get(regras.identidade(atual), 0) + (lance is not None)
        if total >= 3:
            self.resultado = "Empate por tripla repetição"
        elif atual.meios_lances >= 100:
            self.resultado = "Empate por 50 lances"
        return bool(self.resultado)

    def oferecer_ou_aceitar(self):
        if self.resultado or len(self.historico) < 2:
            return
        if self.oferta == -self.posicao.turno:
            self.resultado = "Empate por acordo"
        else:
            self.oferta = self.posicao.turno

    def abandonar(self):
        if not self.resultado:
            vencedor = "Pretas" if self.posicao.turno == 1 else "Brancas"
            self.resultado = f"{vencedor} vencem por abandono"
