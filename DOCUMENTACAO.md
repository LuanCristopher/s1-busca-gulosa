# Documentação do Projeto: Pac-Man com IA (A* vs Busca Gulosa)

Guia pensado para quem **não tem experiência prévia** em programação ou IA. Leia na ordem.

---

## 1. O que é este projeto?

Um jogo estilo Pac-Man em que o jogador come bolinhas e um **fantasma o persegue**. O fantasma
não se move aleatoriamente: a cada passo ele **calcula o melhor caminho até o jogador** usando
um algoritmo de Inteligência Artificial. Dá para alternar entre dois algoritmos (tecla TAB) e
ver, ao vivo e em números, qual é melhor.

**Por que isto atende ao trabalho?** O enunciado pede um programa que use Busca Gulosa e A*,
com modelagem formal, interface visual, dois ou mais cenários de teste com métricas e um relatório.
Tudo isso está aqui.

---

## 2. Conceitos de IA (sem mistério)

### 2.1 O que é um "problema de busca"?
É qualquer situação em que você está num ponto de partida, quer chegar a um objetivo e precisa
escolher uma sequência de ações. Exemplo: o GPS achando a rota de casa até a faculdade.

Todo problema de busca é descrito por quatro peças. No nosso projeto:

| Peça | Significado | No nosso jogo |
|---|---|---|
| **Estado** | "Onde estou agora?" | Uma célula do mapa, por exemplo `(5, 3)` |
| **Ações** | O que posso fazer? | Andar 1 célula: cima, baixo, esquerda ou direita (se não for parede) |
| **Custo** | Quanto custa cada ação? | 1 por passo |
| **Objetivo** | Onde quero chegar? | A célula onde o jogador está |

Isto é a **modelagem formal** que o PDF exige no relatório.

### 2.2 Como uma busca funciona?
Imagine que você está num labirinto sem mapa. Você mantém uma lista de **lugares que ainda quero
explorar** (a **fronteira**). O ciclo é:

1. Escolha da fronteira o lugar mais promissor.
2. Se é o destino, terminou.
3. Senão, olhe os vizinhos dele e coloque-os na fronteira.
4. Volte ao passo 1.

A diferença entre os algoritmos é **só o critério do passo 1**: o que significa "mais promissor".

### 2.3 Heurística h(n)
É um **palpite** de quão longe você está do destino. No nosso caso usamos a **distância de
Manhattan**: quantos quarteirões horizontais + verticais faltam, ignorando paredes.

```
h((2,3) -> (6,5)) = |2-6| + |3-5| = 4 + 2 = 6
```

Ela é **admissível**: nunca promete um caminho mais curto do que o real (paredes só podem
aumentar a distância). Isso é essencial para o A* garantir o melhor caminho.

### 2.4 Busca Gulosa (Greedy Best-First)
Critério: `f(n) = h(n)`. Escolhe sempre o lugar que **parece mais perto do destino**.
- Vantagem: muito rápida, expande poucas células.
- Desvantagem: é "míope". Ignora quanto já andou, então pode escolher um caminho mais longo
  (cair numa armadilha em forma de "U", por exemplo).

### 2.5 A* (A-estrela)
Critério: `f(n) = g(n) + h(n)`, onde:
- `g(n)` = **quanto já andei** de verdade desde o início até aqui;
- `h(n)` = **quanto estimo que falta**.

Equilibra o passado e o futuro. Como h é admissível, **o A\* sempre acha o caminho mais curto**.
O preço: explora mais células que a Gulosa.

### 2.6 Resumo comparativo
| | Gulosa | A* |
|---|---|---|
| Critério | `h(n)` | `g(n) + h(n)` |
| Velocidade | Mais rápida | Mais lenta |
| Células exploradas | Poucas | Mais |
| Caminho | Pode não ser o melhor | **Sempre o melhor** |

---

## 3. Estrutura dos arquivos

```
pacman_ia/
├── maze.py        # O mapa (paredes, bolinhas, vizinhos)
├── search.py      # A IA: A* e Gulosa
├── game.py        # O jogo: teclado, movimento, desenho
├── benchmark.py   # Testes automáticos de desempenho
└── DOCUMENTACAO.md
```

Como se conectam:

```
game.py ──usa──> maze.py    (para saber onde são as paredes)
   │
   └─────usa──> search.py ──usa──> maze.py   (para achar o caminho do fantasma)

benchmark.py ──usa──> maze.py + search.py   (sem jogo, só medindo números)
```

Separar assim é uma boa prática: o `search.py` não sabe que existe um jogo, por isso o mesmo
código serve para jogar e para testar.

---

## 4. Explicação do código, arquivo por arquivo

### 4.1 `maze.py` (o mapa)

**`MAPA_PADRAO`**: lista de textos; cada caractere é uma célula. `#` é parede, `.` é
bolinha, `P` é onde o jogador começa, `G` é onde o fantasma começa. Para mudar o mapa, basta
editar esses textos.

**`DIRECOES`**: as 4 direções como pares `(dx, dy)`. `(0, -1)` é cima (o eixo y cresce para
baixo na tela do computador).

**`class Labirinto`**: guarda o mapa e responde perguntas.
- `__init__`: lê o texto e separa paredes, bolinhas e posições iniciais em *conjuntos*
  (`set`). Conjunto é uma coleção em que perguntar "tal item está aqui?" é instantâneo.
- `livre(pos)`: responde "posso pisar aqui?" (dentro do mapa e não é parede).
- `vizinhos(pos)`: devolve as células vizinhas pisáveis. É a função de **sucessores** da IA
  (dado um estado, quais estados posso alcançar).

**`gerar_aleatorio(...)`**: cria mapas com paredes sorteadas, usados só no benchmark. A
*semente* faz o sorteio ser repetível, e assim os dois algoritmos são testados no mesmo mapa.

### 4.2 `search.py` (a IA)

**`class Resultado`**: um "pacote" com a resposta de uma busca:
- `caminho`: lista de células da origem ao destino;
- `visitados`: células que a busca examinou (a área verde na tela);
- `tempo_ms`: tempo gasto;
- `custo` e `nos_expandidos` calculados a partir dos anteriores.

**`manhattan(a, b)`**: a heurística h(n), uma conta de soma e módulo.

**`_buscar(labirinto, origem, destino, usar_g)`**: o coração do projeto. Vamos por partes:

| Variável | O que é |
|---|---|
| `fronteira` | Fila de prioridade (*heap*) com as células a explorar. A de **menor pontuação sempre sai primeiro** |
| `g` | Dicionário: custo real para chegar em cada célula |
| `pai` | Dicionário: "cheguei na célula X vindo da célula Y". Serve para reconstruir o caminho no final |
| `fechados` | Células já expandidas, para não repetir trabalho |
| `visitados` | Lista na ordem de expansão, para desenhar e contar |

Passo a passo do laço `while`:
1. Tira da fronteira a célula com menor pontuação (`heappop`).
2. Se já foi tratada, pula. Se é o destino, para.
3. Para cada vizinho, calcula `novo_g = g[atual] + 1`.
4. Guarda o vizinho na fronteira com a pontuação:
   - **A\***: `novo_g + h`
   - **Gulosa**: só `h`
5. Ao achar o destino, **reconstrói o caminho** seguindo `pai` de trás para frente, e depois
   inverte a lista.

O parâmetro `usar_g` é o único interruptor entre os dois algoritmos. No A*, um vizinho só é
atualizado se encontramos um caminho **mais barato** até ele. Na Gulosa, basta ter sido
descoberto uma vez.

O `contador` serve só de desempate: quando duas células têm a mesma pontuação, a heap compara o
próximo item da tupla, e o contador garante uma ordem consistente.

**`astar(...)` e `gulosa(...)`**: apenas chamam `_buscar` com `usar_g` verdadeiro ou falso.

**`ALGORITMOS`**: dicionário `{"A*": astar, "Gulosa": gulosa}`, que permite escolher o algoritmo
pelo nome (o jogo troca com TAB; o benchmark percorre os dois).

### 4.3 `game.py` (o jogo)

Usa **Pygame**, biblioteca que cria janela, desenha formas e lê o teclado.

**Ideia central: o loop de jogo.** Todo jogo repete, ~60 vezes por segundo:
`ler teclas → atualizar o estado → desenhar`. Está em `rodar()`.

**`class Jogo`** tem estes métodos:

| Método | Função |
|---|---|
| `__init__` | Abre a janela e configura fontes e velocidades |
| `reiniciar` | Zera posições, bolinhas, pontos e estatísticas (tecla R) |
| `recalcular` | **Chama a IA**: acha o caminho do fantasma ao jogador e guarda as métricas |
| `mover_jogador` | Anda 1 célula, come a bolinha, verifica vitória |
| `mover_fantasma` | Recalcula o caminho e dá **um passo** por ele |
| `checar_colisao` | Mesma célula = jogador perde |
| `atualizar(dt)` | Soma o tempo decorrido e decide quem deve andar agora |
| `rect(pos)` | Converte célula `(x, y)` em pixels |
| `desenhar` | Pinta paredes, bolinhas, personagens, a área explorada e o painel |
| `desenhar_hud` | Escreve as métricas (nós, custo, tempo, médias) |
| `tratar_evento` | Reage às teclas (setas, TAB, V, +/-, R, ESC) |
| `rodar` | O loop principal |

**Detalhes que merecem atenção:**
- **Velocidades diferentes.** Jogador e fantasma têm relógios próprios (`t_jogador`,
  `t_fantasma`). Cada um acumula o tempo e só anda ao passar do limite. Assim o fantasma pode
  ser mais lento ou rápido sem travar o jogo.
- **Fantasma recalcula a cada passo.** Como o jogador se move, o melhor caminho muda; por isso
  `mover_fantasma` chama a IA toda vez.
- **Direção "pedida".** Se você aperta uma seta antes de chegar na curva, o jogo lembra e vira
  assim que for possível.
- **Camada transparente (`overlay`).** O verde (explorado) e o laranja (caminho) são pintados
  numa camada translúcida, para não esconder o mapa.

### 4.4 `benchmark.py` (a avaliação de desempenho)

Roda os algoritmos **sem jogo**, só medindo. É o que gera os dados do relatório.

- `CENARIOS`: 6 combinações de tamanho (20x20, 50x50, 100x100) e densidade de paredes (15% e 30%).
- `rodar()`: para cada cenário e algoritmo, repete 30 vezes: gera mapa aleatório, sorteia origem
  e destino, roda a busca e anota tempo, nós expandidos e custo do caminho. No final tira a
  **média**. Se não existe caminho (paredes isolaram uma região), a repetição é ignorada e contada
  em `sem_caminho`.
- `salvar_csv()`: grava `resultados.csv`.
- `grafico()`: gera `graficos.png` com barras comparando A* e Gulosa.

**Por que 30 repetições com semente?** Um único teste pode ser sorte. A média de muitos é mais
confiável, e a semente garante que A* e Gulosa enfrentem **exatamente o mesmo problema**
(comparação justa).

---

## 5. Como rodar

```bash
cd pacman_ia
pip install pygame matplotlib

python3 game.py        # abre o jogo
python3 benchmark.py   # roda os testes, gera resultados.csv e graficos.png
```

**Controles do jogo:** setas (mover), **TAB** (trocar A*/Gulosa), **V** (mostrar/ocultar
a área explorada), **+/-** (velocidade do fantasma), **R** (reiniciar), **ESC** (sair).

---

## 6. O que observar na demonstração

1. Jogue com **A\*** e aperte **V**: veja a área verde (o que o fantasma explorou) e a linha
   laranja (o caminho escolhido).
2. Aperte **TAB** para a **Gulosa**. A área verde fica menor (menos nós) e o caminho às vezes
   faz voltas desnecessárias.
3. Compare no painel: **nós expandidos** (A* maior) e **custo** (A* menor ou igual).

## 7. Resultados do benchmark (resumo)

Veja `resultados.csv` e `graficos.png` para os valores completos. Padrão encontrado:

- A* expande de 2 a 10 vezes mais nós que a Gulosa, mas **sempre acha o caminho mais curto**.
- A Gulosa é mais rápida em tempo, mas gera caminhos até ~20% mais longos em mapas com muitas paredes.
- A diferença cresce com o tamanho do mapa.

## 8. Limitações e melhorias (para a conclusão do relatório)

- O fantasma é "perfeito": sempre acha o caminho ótimo, o que torna o jogo difícil. Poderia
  errar de propósito ou ter vários fantasmas com comportamentos diferentes.
- Só há um fantasma e um mapa fixo no jogo. Poderia haver mapas selecionáveis.
- O mapa do benchmark é aleatório e pode ter regiões isoladas (testes ignorados).
- Poderia comparar outras heurísticas (Euclidiana, Chebyshev) ou o algoritmo de Dijkstra.

## 9. Glossário rápido

| Termo | Significado |
|---|---|
| **Algoritmo** | Receita passo a passo para resolver um problema |
| **Heurística** | Palpite/estimativa que ajuda a busca a decidir |
| **Admissível** | Heurística que nunca superestima o custo real |
| **Fronteira** | Lista de lugares descobertos e ainda não explorados |
| **Nó expandido** | Célula cujos vizinhos já foram examinados |
| **Heap** | Estrutura que sempre entrega primeiro o menor valor |
| **Tupla** | Grupo fixo de valores, como `(x, y)` |
| **Dicionário** | Coleção de pares chave → valor |
| **Benchmark** | Teste que mede desempenho |
| **Semente** | Número que torna um sorteio repetível |
