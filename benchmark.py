"""Avaliação de desempenho: A* vs Gulosa em vários cenários.

Gera resultados.csv e graficos.png (se matplotlib estiver instalado).
Uso: python benchmark.py

Cada cenário gera 30 mapas aleatórios; em cada um sorteia origem e destino e roda os DOIS
algoritmos no mesmo problema. As médias são o que vai para a tabela/gráficos do relatório.
"""
import csv
import random
import statistics

from maze import gerar_aleatorio
from search import ALGORITMOS

# (nome, largura, altura, densidade de paredes)
CENARIOS = [
    ("Pequeno / poucas paredes", 20, 20, 0.15),
    ("Pequeno / muitas paredes", 20, 20, 0.30),
    ("Medio / poucas paredes", 50, 50, 0.15),
    ("Medio / muitas paredes", 50, 50, 0.30),
    ("Grande / poucas paredes", 100, 100, 0.15),
    ("Grande / muitas paredes", 100, 100, 0.30),
]
REPETICOES = 30  # mais repetições = médias mais confiáveis


def rodar():
    """Executa todos os cenários e devolve uma lista de linhas (uma por cenário x algoritmo)."""
    linhas = []
    for nome, w, h, dens in CENARIOS:
        for alg_nome, alg in ALGORITMOS.items():
            tempos, nos, custos, falhas = [], [], [], 0
            for semente in range(REPETICOES):
                # mesma semente => A* e Gulosa recebem exatamente o mesmo mapa e os mesmos pontos
                lab = gerar_aleatorio(w, h, dens, semente)
                livres = [(x, y) for y in range(h) for x in range(w) if (x, y) not in lab.paredes]
                rng = random.Random(1000 + semente)
                a, b = rng.sample(livres, 2)
                r = alg(lab, a, b)
                if not r.caminho:
                    falhas += 1  # destino inalcançável: ignorado nas médias
                    continue
                tempos.append(r.tempo_ms)
                nos.append(r.nos_expandidos)
                custos.append(r.custo)
            linhas.append({
                "cenario": nome, "algoritmo": alg_nome,
                "tempo_ms": round(statistics.mean(tempos), 3),
                "nos_expandidos": round(statistics.mean(nos), 1),
                "custo_caminho": round(statistics.mean(custos), 2),
                "sem_caminho": falhas,
            })
    return linhas


def salvar_csv(linhas):
    """Grava os resultados em resultados.csv (abre no Excel/Sheets)."""
    with open("resultados.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=linhas[0].keys())
        w.writeheader()
        w.writerows(linhas)


def grafico(linhas):
    """Gera graficos.png com 3 gráficos de barras (tempo, nós expandidos, custo do caminho)."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # modo sem janela: só salva a imagem
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib não instalado; pulando gráficos.")
        return
    nomes = [c[0] for c in CENARIOS]
    metricas = [("tempo_ms", "Tempo médio (ms)"), ("nos_expandidos", "Nós expandidos"),
                ("custo_caminho", "Custo do caminho")]
    fig, eixos = plt.subplots(1, 3, figsize=(18, 5))
    for ax, (chave, titulo) in zip(eixos, metricas):
        for i, alg in enumerate(ALGORITMOS):
            vals = [l[chave] for l in linhas if l["algoritmo"] == alg]
            ax.bar([x + i * 0.4 for x in range(len(nomes))], vals, 0.4, label=alg)
        ax.set_xticks([x + 0.2 for x in range(len(nomes))])
        ax.set_xticklabels(nomes, rotation=45, ha="right", fontsize=8)
        ax.set_title(titulo)
        ax.legend()
    plt.tight_layout()
    plt.savefig("graficos.png", dpi=130)


if __name__ == "__main__":
    dados = rodar()
    salvar_csv(dados)
    grafico(dados)
    print(f"{'cenario':28} {'alg':7} {'tempo_ms':>9} {'nos':>9} {'custo':>8} {'sem_cam':>7}")
    for l in dados:
        print(f"{l['cenario']:28} {l['algoritmo']:7} {l['tempo_ms']:9} {l['nos_expandidos']:9} "
              f"{l['custo_caminho']:8} {l['sem_caminho']:7}")
