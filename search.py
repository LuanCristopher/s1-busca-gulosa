"""Busca Gulosa e A* sobre o labirinto.

Estado = célula (x, y). Ação = mover 1 célula (4 direções). Custo = 1 por passo.
Heurística h(n) = distância de Manhattan até o objetivo (admissível e consistente).
  - Gulosa: f(n) = h(n)
  - A*:     f(n) = g(n) + h(n)

Este é o "cérebro" do fantasma: dadas uma origem e um destino, descobre o caminho.
"""
import heapq
import time
from dataclasses import dataclass, field


@dataclass
class Resultado:
    """Tudo que uma busca devolve, para o jogo desenhar e para medirmos desempenho."""
    caminho: list = field(default_factory=list)  # células da origem ao destino (vazio = sem caminho)
    visitados: list = field(default_factory=list)  # células exploradas, na ordem (área verde na tela)
    tempo_ms: float = 0.0  # quanto tempo a busca levou

    @property
    def custo(self):
        """Número de passos do caminho (None se não existe caminho)."""
        return max(len(self.caminho) - 1, 0) if self.caminho else None

    @property
    def nos_expandidos(self):
        """Quantas células a busca precisou examinar. Menos = busca mais 'esperta'."""
        return len(self.visitados)


def manhattan(a, b):
    """HEURÍSTICA h(n): estimativa de quantos passos faltam de `a` até `b`.

    Soma a distância horizontal e vertical, como andar por quarteirões de uma cidade.
    Nunca superestima (ignora paredes, então o caminho real é >= esse valor),
    e é isso que garante que o A* ache o caminho ótimo ("admissível").
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _buscar(labirinto, origem, destino, usar_g):
    """Motor único das duas buscas; a ÚNICA diferença é o parâmetro `usar_g`.

    Ideia geral: manter uma FRONTEIRA (lista de células a explorar), sempre pegando a que
    parece mais promissora (menor pontuação f). Expandir = olhar seus vizinhos e colocá-los
    na fronteira. Repete até chegar no destino.

      usar_g=False -> Gulosa: pontuação f = h  (só "quão perto do destino estou?")
      usar_g=True  -> A*:     pontuação f = g + h  ("quanto já andei" + "quanto falta estimado")
    """
    t0 = time.perf_counter()  # cronômetro de alta precisão
    contador = 0  # desempate: se duas células têm mesma pontuação, vale a inserida primeiro
    # A fronteira é uma heap (fila de prioridade): o menor valor sempre sai primeiro.
    fronteira = [(manhattan(origem, destino), contador, origem)]
    pai = {origem: None}  # de qual célula cheguei em cada célula (serve para reconstruir o caminho)
    g = {origem: 0}  # g(n): custo real (passos) para chegar em cada célula
    fechados = set()  # células já expandidas, não precisam ser revisitadas
    visitados = []
    achou = False

    while fronteira:
        _, _, atual = heapq.heappop(fronteira)  # pega a célula mais promissora
        if atual in fechados:
            continue  # entrada repetida na heap; já foi tratada
        fechados.add(atual)
        visitados.append(atual)
        if atual == destino:
            achou = True
            break
        for viz in labirinto.vizinhos(atual):
            novo_g = g[atual] + 1  # chegar no vizinho custa 1 passo a mais
            if viz in fechados:
                continue
            if usar_g:
                # A*: só atualiza se achou um caminho MAIS CURTO até este vizinho
                if viz in g and novo_g >= g[viz]:
                    continue
            elif viz in pai:
                # Gulosa: não liga para o custo, basta ter sido descoberto uma vez
                continue
            g[viz] = novo_g
            pai[viz] = atual
            h = manhattan(viz, destino)
            contador += 1
            heapq.heappush(fronteira, ((novo_g + h) if usar_g else h, contador, viz))

    # Reconstrói o caminho andando do destino de volta à origem pelos "pais"
    caminho = []
    if achou:
        n = destino
        while n is not None:
            caminho.append(n)
            n = pai[n]
        caminho.reverse()
    return Resultado(caminho, visitados, (time.perf_counter() - t0) * 1000)


def astar(labirinto, origem, destino):
    """Busca A*: considera custo já percorrido + estimativa. Sempre acha o caminho MAIS CURTO."""
    return _buscar(labirinto, origem, destino, usar_g=True)


def gulosa(labirinto, origem, destino):
    """Busca Gulosa: só olha a estimativa até o destino. Rápida, mas pode achar caminho mais longo."""
    return _buscar(labirinto, origem, destino, usar_g=False)


# Dicionário usado pelo jogo e pelo benchmark para escolher o algoritmo pelo nome
ALGORITMOS = {"A*": astar, "Gulosa": gulosa}
