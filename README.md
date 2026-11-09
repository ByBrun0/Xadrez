# Praça dos Dois Jogos

Xadrez e damas brasileiras para duas pessoas no mesmo computador.
Um tabuleiro reversível sobre uma mesa de pedra, com mapas diurno e noturno.

## Executar

Use Python 3.10 ou posterior e suporte a OpenGL 3.3, como nos exemplos das
aulas 15–17. Na pasta do projeto:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Mantenha a pasta `Aulas` junto ao jogo. A pedra e a madeira são as imagens
do professor. As malhas, os detalhes das peças, o céu e a interface são
gerados pelo programa com NumPy e Pillow e desenhados com PyOpenGL e GLFW.

## Jogar e virar o tabuleiro

Clique em uma peça da sua cor e depois em um destino marcado.
Nas damas, indique cada pouso de uma captura múltipla. A seleção fica
presa à sequência até completar todos os saltos.

Arraste uma das alças de bronze da moldura para cima. As peças saltam para
as bacias, o tabuleiro sobe e seu arraste controla a virada. Solte depois
da metade para trocar de jogo, ou antes da metade para voltar. O botão
do painel e a tecla V executam a virada completa.

Cada face guarda posição, turno, resultado, histórico, contadores e oferta
de empate enquanto o programa estiver aberto. Nova partida reinicia
somente o jogo visível, após confirmação.

## Menu e mapas

O menu se recolhe após um segundo sem o mouse sobre ele. Passe o mouse na
aba vertical MENU, na borda direita, para abri-lo. Promoção, ajuda e
confirmações mantêm o menu aberto. O painel desliza sobre a cena, mantendo
o enquadramento e a seleção das casas estáveis durante a abertura.

O mapa inicial é a Praça diurna. O botão Mapa ou a tecla M alterna para a
Praça noturna, com lua, estrelas, postes e lanternas acesos. Os dois mapas
usam a mesma disposição da praça. As posições do sol, lua, estrelas e
luzes estão definidas em coordenadas do mundo em `graficos/mapas.py`.
A órbita da câmera permite olhar para o céu e observar os astros.

Os bancos usam uma grade subdividida, arredondamento BEVEL e curvatura
BEND adaptados da aula 24. As normais são recalculadas após as deformações.
Essas malhas são preparadas na inicialização e reutilizadas pela GPU.

## Controles

| Comando | Ação |
|---|---|
| Clique esquerdo | Seleciona peça, destino ou botão do painel |
| Arraste uma alça para cima | Controla a virada entre os dois jogos |
| Botão direito e arraste | Orbita a câmera |
| Roda do mouse | Aproxima e afasta |
| V | Vira automaticamente |
| Home | Restaura a câmera para o jogador da vez |
| G | Liga ou desliga o giro automático por turno |
| Q | Alterna qualidade normal e leve |
| M | Alterna entre os mapas diurno e noturno |
| D, T, B, C | Escolhe a promoção no xadrez |
| E | Oferece ou aceita empate |
| R | Reivindica empate no xadrez, na posição atual ou com o próximo lance indicado |
| X | Solicita abandono |
| N | Solicita nova partida do jogo visível |
| Enter | Confirma abandono ou nova partida |
| Esc | Cancela seleção, promoção, confirmação ou virada manual ainda segurada |
| H | Mostra ou fecha a ajuda |

As partidas ficam bloqueadas durante movimentos e viradas. Uma captura
múltipla iniciada deve ser concluída antes de virar, reiniciar ou abandonar.
A câmera só gira depois da animação completa da jogada. O painel mostra
turno, resultado, ofertas, avisos e contagem de peças capturadas.

## Organização

| Módulo | Responsabilidade |
|---|---|
| `main.py` | Janela, laço principal e ciclo de vida dos recursos |
| `configuracao.py` | Dimensões, cores, tempos e níveis de qualidade |
| `sessao.py` | Duas partidas preservadas, seleção e coordenação de animações |
| `interface.py` | Eventos de mouse, teclado, confirmação e comandos |
| `animacao.py` | Trajetórias de peças, capturas, promoção e virada |
| `xadrez/` | Regras e estado do xadrez |
| `damas/` | Regras e estado das damas brasileiras |
| `graficos/camera.py` | Órbita, zoom, projeção e raio de seleção |
| `graficos/malhas.py` | Primitivas e transformações de malhas |
| `graficos/modificadores.py` | BEVEL e BEND da aula 24 aplicados aos bancos |
| `graficos/mapas.py` | Cores dos ambientes, astros e luzes em coordenadas 3D |
| `graficos/renderizador.py` | Shaders, texturas e buffers na GPU |
| `graficos/cena.py` | Composição da cena e recursos compartilhados |
| `graficos/tabuleiro.py` | Duas faces, alças, casas e coordenadas |
| `graficos/pecas.py` | Perfis e detalhes das seis peças de xadrez |
| `graficos/pecas_damas.py` | Pedras, damas e emblemas |
| `graficos/cenario.py` | Mesa, bancos, bacias, árvores, canteiros, postes e céu |
| `graficos/painel.py` | Texto, botões e textura do painel |

A sessão confirma o lance lógico uma vez. As animações usam a posição
anterior e a seguinte. Geometrias repetidas compartilham buffers. A praça é
agrupada por material. As duas qualidades são preparadas na inicialização,
permitindo alternar sem reconstruir a cena durante a partida. Texturas
estáticas usam mipmaps e a textura do painel muda somente com seu conteúdo.

## Damas brasileiras

Peões avançam uma diagonal e capturam nas quatro diagonais. Damas
percorrem diagonais. A captura é obrigatória e vale a lei da maioria.
Vítimas permanecem como obstáculos durante uma sequência e são retiradas
ao fim. A promoção depende da casa final.

| Condição | Tratamento no jogo |
|---|---|
| Adversário sem peças ou movimentos | Vitória |
| Mesma posição e turno pela terceira vez | Empate automático |
| 20 lances de cada lado só com damas, sem captura ou movimento de peão | Empate automático |
| Dama contra dama, duas damas contra dama, ou dama e peão contra dama | Contagem de 5 lances de cada lado |
| Três peças, incluindo dama, contra dama na grande diagonal | Contagem de 5 lances de cada lado enquanto esse final se mantém |
| Acordo | Oferta a partir de 20 lances de cada lado, aceita pelo adversário |
| Abandono | Vitória do adversário |

As contagens de finais começam quando a configuração surge. A derrota por
bloqueio ou eliminação tem prioridade sobre o empate. A interface executa
as contagens automaticamente. Uma nova oferta só pode partir do mesmo lado
depois que o outro também tiver oferecido.

Referências das regras de damas:
[FPD, regras brasileiras](https://www.fpdamas.pt/wp-content/uploads/2025/04/3Regras-das-damas-brasileiras.pdf)
e [texto de competição autorizado pela confederação, artigos 97–104](https://damasciencias.com.br/regras-competicao.html).

## Verificação

```powershell
python -B test_xadrez.py
python -B test_damas.py
python -B test_interface.py
python -B test_ambientes.py
```

Os dois primeiros testes verificam regras e sessão. O terceiro abre uma
janela oculta e exercita os callbacks de mouse/teclado, projeção das 64 casas,
redimensionamento, mate, uma partida completa de damas, painel, reinício,
arraste das alças e promoção.
O quarto verifica o menu retrátil, estabilidade da projeção, troca de
mapas, posição mundial do sol e modificadores da aula 24.

Para reproduzir as medições e gerar imagens das faces, virada, menu e mapas:

```powershell
python -B verificar_visual.py
```

Os resultados ficam em `validacao/`. A medição usa janela oculta em 1100×800,
sincronização vertical desativada e espera pelo término do desenho na GPU.
O indicador no painel é medido com o jogo em execução e inclui a espera
pela sincronização da tela. Esses dois números podem diferir.

## Limites conhecidos

No xadrez, a busca de posição morta é limitada a 20 mil posições e recebe
um orçamento de tempo entre etapas. Uma etapa indivisível pode ultrapassar
esse orçamento. Se a busca ficar inconclusiva, a partida segue. O abandono
ainda concede vitória ao adversário sem verificar se somente ele possui
alguma sequência possível de mate.

As partidas são preservadas durante a execução. Fechar o programa encerra
a sessão.

A validação visual foi feita com imagens renderizadas pelo jogo e os
comandos foram exercitados pelos callbacks. A checagem manual pelo controle
do computador ficou pendente porque a ferramenta retornou imagens de outro
aplicativo ao capturar a janela do jogo.
