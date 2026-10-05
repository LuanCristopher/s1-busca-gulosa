"""Labirinto em grade: '#' parede, '.' pellet, ' ' vazio, 'P' jogador, 'G' fantasma.

Este arquivo só descreve o MAPA. Ele não sabe nada de IA nem de desenho na tela:
apenas responde perguntas como "essa célula é parede?" e "quais células vizinhas posso pisar?".
"""
import random

# O mapa é uma lista de textos. Cada caractere é uma célula do grid:
#   '#' parede | '.' bolinha (pellet) | ' ' chão vazio | 'P' início do jogador | 'G' início do fantasma
MAPA_PADRAO = [
    "#####################",
    "#.........#.........#",
    "#.###.###.#.###.###.#",
    "#...................#",
    "#.###.#.#####.#.###.#",
    "#.....#...#...#.....#",
    "#####.### # ###.#####",
    "    #.#   G   #.#    ",
    "#####.# ##### #.#####",
    "#.......  P  .......#",
    "#.###.### # ###.###.#",
    "#...#...........#...#",
    "###.#.#.#####.#.#.###",
    "#.....#...#...#.....#",
    "#.#######.#.#######.#",
    "#...................#",
    "#####################",
]

# As 4 direções possíveis de movimento, como (dx, dy): cima, baixo, esquerda, direita.
# Obs.: no computador o eixo y cresce PARA BAIXO, por isso "cima" é y-1.
DIRECOES = [(0, -1), (0, 1), (-1, 0), (1, 0)]


class Labirinto:
    """Guarda o mapa e responde perguntas sobre ele."""

    def __init__(self, linhas=None):
        """Lê o mapa em texto e separa em: paredes, bolinhas e posições iniciais.

        Cada posição é uma tupla (x, y): x = coluna, y = linha.
        Usamos `set` (conjunto) porque perguntar "esta posição está no conjunto?" é muito rápido.
        """
        linhas = linhas or MAPA_PADRAO
        self.altura = len(linhas)
        self.largura = max(len(l) for l in linhas)
        self.paredes = set()
        self.pellets = set()
        self.inicio_jogador = (1, 1)
        self.inicio_fantasma = (1, 1)
        for y, linha in enumerate(linhas):
            # ljust completa linhas curtas com espaços para o mapa ficar retangular
            for x, c in enumerate(linha.ljust(self.largura)):
                if c == "#":
                    self.paredes.add((x, y))
                elif c == ".":
                    self.pellets.add((x, y))
                elif c == "P":
                    self.inicio_jogador = (x, y)
                elif c == "G":
                    self.inicio_fantasma = (x, y)

    def livre(self, pos):
        """Retorna True se `pos` está dentro do mapa E não é parede (ou seja, dá para pisar)."""
        x, y = pos
        return 0 <= x < self.largura and 0 <= y < self.altura and pos not in self.paredes

    def vizinhos(self, pos):
        """Gera as células vizinhas (4 direções) onde é possível andar a partir de `pos`.

        Na linguagem da IA isto é a função de SUCESSORES: dado um estado, quais estados
        posso alcançar com uma ação? É o que as buscas (search.py) usam para "andar" pelo mapa.
        """
        x, y = pos
        for dx, dy in DIRECOES:
            p = (x + dx, y + dy)
            if self.livre(p):
                yield p  # `yield` devolve um vizinho por vez, sem montar uma lista inteira


def gerar_aleatorio(largura, altura, densidade=0.25, semente=None):
    """Cria um mapa com paredes sorteadas (usado só nos benchmarks, não no jogo).

    densidade: chance de cada célula virar parede (0.15 = 15%).
    semente: número que fixa o sorteio, assim o mesmo mapa pode ser gerado de novo
             (essencial para comparar A* e Gulosa no MESMO mapa, de forma justa).
    """
    rng = random.Random(semente)
    m = Labirinto(["." * largura for _ in range(altura)])
    for y in range(altura):
        for x in range(largura):
            if rng.random() < densidade:
                m.paredes.add((x, y))
    # garante que os cantos não são parede
    m.paredes.discard((0, 0))
    m.paredes.discard((largura - 1, altura - 1))
    m.pellets = set()
    return m
