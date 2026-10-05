"""Pac-Man com fantasma perseguidor (A* ou Busca Gulosa).

Controles: setas = mover | TAB = trocar algoritmo | V = mostrar/ocultar área explorada
           +/- = velocidade do fantasma | R = reiniciar | ESC = sair

Este arquivo junta tudo: recebe teclado, move jogador e fantasma, chama a IA (search.py)
e desenha a tela. Usa a biblioteca Pygame para janela, desenho e teclado.
"""
import sys

import pygame

from maze import Labirinto
from search import ALGORITMOS

# ---- Configurações visuais e de ritmo ----
CELULA = 32  # tamanho de cada célula em pixels
HUD_H = 110  # altura da faixa de informações embaixo do mapa
PASSO_JOGADOR_MS = 170  # o jogador anda 1 célula a cada 170 ms

COR_FUNDO = (10, 10, 25)
COR_PAREDE = (33, 33, 222)
COR_PELLET = (255, 220, 170)
COR_JOGADOR = (255, 230, 0)
COR_FANTASMA = (255, 60, 60)
COR_VISITADO = (60, 200, 120, 70)  # o 4º número é a transparência
COR_CAMINHO = (255, 140, 0, 150)
COR_TEXTO = (235, 235, 235)


class Jogo:
    """Controla o estado do jogo e o loop principal."""

    def __init__(self):
        """Abre a janela e prepara fontes, relógio e configurações iniciais."""
        pygame.init()
        self.lab = Labirinto()
        self.tela = pygame.display.set_mode(
            (self.lab.largura * CELULA, self.lab.altura * CELULA + HUD_H)
        )
        pygame.display.set_caption("Pac-Man IA - A* vs Busca Gulosa")
        self.fonte = pygame.font.SysFont("monospace", 16)
        self.fonte_grande = pygame.font.SysFont("monospace", 36, bold=True)
        self.relogio = pygame.time.Clock()
        self.nomes = list(ALGORITMOS)  # ["A*", "Gulosa"]
        self.algoritmo = 0  # índice do algoritmo atual na lista acima
        self.passo_fantasma_ms = 260  # o fantasma anda 1 célula a cada 260 ms (maior = mais lento)
        self.mostrar_visitados = True
        self.reiniciar()

    def reiniciar(self):
        """Volta tudo ao início: posições, bolinhas, pontos e estatísticas."""
        self.jogador = self.lab.inicio_jogador
        self.fantasma = self.lab.inicio_fantasma
        self.pellets = set(self.lab.pellets)  # cópia, porque as bolinhas serão comidas
        self.pontos = 0
        self.dir_atual = (0, 0)  # direção em que o jogador está andando
        self.dir_pedida = (0, 0)  # última direção apertada (vira assim que houver espaço livre)
        self.t_jogador = 0  # acumuladores de tempo para saber quando cada um deve andar
        self.t_fantasma = 0
        self.estado = "jogando"  # jogando | perdeu | ganhou
        self.resultado = None
        self.tempos = []  # tempo de cada busca (ms), para a média no painel
        self.expandidos = []  # nós expandidos em cada busca
        self.recalcular()

    @property
    def nome_algoritmo(self):
        """Nome do algoritmo em uso ('A*' ou 'Gulosa')."""
        return self.nomes[self.algoritmo]

    def recalcular(self):
        """Roda a IA: busca o caminho do fantasma até o jogador e guarda as estatísticas."""
        self.resultado = ALGORITMOS[self.nome_algoritmo](self.lab, self.fantasma, self.jogador)
        self.tempos.append(self.resultado.tempo_ms)
        self.expandidos.append(self.resultado.nos_expandidos)

    # ---------- lógica ----------
    def mover_jogador(self):
        """Anda 1 célula, come a bolinha (se houver) e verifica vitória.

        Tenta primeiro a direção pedida; se tiver parede, continua na direção atual.
        Isso deixa o controle suave: dá para apertar a seta antes da curva.
        """
        for d in (self.dir_pedida, self.dir_atual):
            alvo = (self.jogador[0] + d[0], self.jogador[1] + d[1])
            if d != (0, 0) and self.lab.livre(alvo):
                self.dir_atual = d
                self.jogador = alvo
                break
        if self.jogador in self.pellets:
            self.pellets.remove(self.jogador)
            self.pontos += 10
        if not self.pellets:
            self.estado = "ganhou"

    def mover_fantasma(self):
        """Recalcula o caminho até o jogador (que se mexeu) e dá UM passo por ele."""
        self.recalcular()
        caminho = self.resultado.caminho
        if len(caminho) > 1:
            self.fantasma = caminho[1]  # caminho[0] é a posição atual; [1] é o próximo passo

    def checar_colisao(self):
        """Se fantasma e jogador estão na mesma célula, o jogador perde."""
        if self.fantasma == self.jogador:
            self.estado = "perdeu"

    def atualizar(self, dt):
        """Avança o jogo `dt` milissegundos: decide se é hora de jogador/fantasma andarem."""
        if self.estado != "jogando":
            return
        self.t_jogador += dt
        self.t_fantasma += dt
        if self.t_jogador >= PASSO_JOGADOR_MS:
            self.t_jogador = 0
            self.mover_jogador()
            self.checar_colisao()
        if self.estado == "jogando" and self.t_fantasma >= self.passo_fantasma_ms:
            self.t_fantasma = 0
            self.mover_fantasma()
            self.checar_colisao()

    # ---------- desenho ----------
    def rect(self, pos):
        """Converte uma célula (x, y) em um retângulo de pixels na tela."""
        return pygame.Rect(pos[0] * CELULA, pos[1] * CELULA, CELULA, CELULA)

    def desenhar(self):
        """Desenha um quadro completo: mapa, busca (verde/laranja), personagens e painel."""
        self.tela.fill(COR_FUNDO)
        # Camada transparente onde pintamos a área explorada (verde) e o caminho (laranja)
        overlay = pygame.Surface((self.lab.largura * CELULA, self.lab.altura * CELULA), pygame.SRCALPHA)
        if self.mostrar_visitados and self.resultado:
            for p in self.resultado.visitados:
                pygame.draw.rect(overlay, COR_VISITADO, self.rect(p))
            for p in self.resultado.caminho:
                pygame.draw.rect(overlay, COR_CAMINHO, self.rect(p))
        for p in self.lab.paredes:
            pygame.draw.rect(self.tela, COR_PAREDE, self.rect(p).inflate(-4, -4), border_radius=6)
        self.tela.blit(overlay, (0, 0))
        for p in self.pellets:
            pygame.draw.circle(self.tela, COR_PELLET, self.rect(p).center, 3)
        pygame.draw.circle(self.tela, COR_JOGADOR, self.rect(self.jogador).center, CELULA // 2 - 3)
        pygame.draw.circle(self.tela, COR_FANTASMA, self.rect(self.fantasma).center, CELULA // 2 - 3)
        self.desenhar_hud()
        if self.estado != "jogando":
            msg = "VOCE PERDEU!" if self.estado == "perdeu" else "VOCE GANHOU!"
            txt = self.fonte_grande.render(msg + "  (R)", True, (255, 255, 255), (0, 0, 0))
            self.tela.blit(txt, txt.get_rect(center=(self.tela.get_width() // 2, self.lab.altura * CELULA // 2)))
        pygame.display.flip()  # mostra o quadro pronto na janela

    def desenhar_hud(self):
        """Escreve o painel de informações (algoritmo, métricas da busca) embaixo do mapa."""
        y0 = self.lab.altura * CELULA + 8
        r = self.resultado
        media_t = sum(self.tempos) / len(self.tempos)
        media_n = sum(self.expandidos) / len(self.expandidos)
        linhas = [
            f"Algoritmo: {self.nome_algoritmo}   Pontos: {self.pontos}   Pellets: {len(self.pellets)}",
            f"Ultima busca: {r.nos_expandidos} nos, caminho {r.custo}, {r.tempo_ms:.3f} ms",
            f"Media: {media_n:.1f} nos, {media_t:.3f} ms ({len(self.tempos)} buscas)",
            f"Fantasma: {self.passo_fantasma_ms} ms/passo  [TAB] alg [V] area [+/-] [R]",
        ]
        for i, l in enumerate(linhas):
            self.tela.blit(self.fonte.render(l, True, COR_TEXTO), (8, y0 + i * 22))

    # ---------- loop ----------
    def tratar_evento(self, ev):
        """Reage a um evento (tecla ou fechar janela). Retorna False se o jogo deve encerrar."""
        if ev.type == pygame.QUIT:
            return False
        if ev.type != pygame.KEYDOWN:
            return True
        setas = {
            pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
        }
        if ev.key == pygame.K_ESCAPE:
            return False
        elif ev.key in setas:
            self.dir_pedida = setas[ev.key]
        elif ev.key == pygame.K_TAB:
            # troca de algoritmo e zera as médias para comparar de forma justa
            self.algoritmo = (self.algoritmo + 1) % len(self.nomes)
            self.tempos, self.expandidos = [], []
            self.recalcular()
        elif ev.key == pygame.K_v:
            self.mostrar_visitados = not self.mostrar_visitados
        elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.passo_fantasma_ms = max(60, self.passo_fantasma_ms - 40)  # mais rápido
        elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.passo_fantasma_ms = min(600, self.passo_fantasma_ms + 40)  # mais lento
        elif ev.key == pygame.K_r:
            self.reiniciar()
        return True

    def rodar(self):
        """LOOP PRINCIPAL: a cada quadro (60 por segundo) lê teclas, atualiza e desenha."""
        rodando = True
        while rodando:
            dt = self.relogio.tick(60)  # limita a 60 FPS e devolve ms desde o último quadro
            for ev in pygame.event.get():
                rodando = self.tratar_evento(ev) and rodando
            self.atualizar(dt)
            self.desenhar()
        pygame.quit()


if __name__ == "__main__":
    Jogo().rodar()
    sys.exit(0)
