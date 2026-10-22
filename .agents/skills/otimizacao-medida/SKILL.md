---
name: otimizacao-medida
description: Otimiza o tempo por processo da rodada do FaturamentoLegalOne (busca, checagem de duplicata, formulário, Salvar) com medição antes e depois, o ledger e o placar da rodada como oráculo e um orçamento de acessos que não martela o servidor do Legal One — pausas fixas (config.DEBOUNCE_DELAY, PAUSA_ENTRE_PROCESSOS) versus esperas explícitas, esperas que estouram em silêncio, caches. Use quando a rodada estiver lenta ou antes de mexer em esperas, pausas e timeouts de src/legalone.py. Pule para a velocidade da suíte ou da CI (auditoria-testes) e para bug de correção sem ângulo de desempenho.
metadata:
  version: "1"
---

# Otimização medida

> Adapted from morluto/rea `rea-analysis-optimization` (MIT, © 2026 morluto).

Achar uma fonte concreta de trabalho desnecessário por processo, corrigir no
dono e provar com rodadas equivalentes. "Deixar como está" também é resultado,
quando medido. Esta skill não autoriza `--executar`, commit nem PR.

## Dados de cliente (classe C)

- Medições, cópias e scripts de medição ficam em `/tmp/<tarefa>/`, fora da
  árvore; apague a cópia do ledger ao terminar.
- Ledger e logs trazem CNJ e nome de cliente. Só abra com pedido do usuário, e
  só para agregados (contagens, durações); a saída nunca lista CNJ.
- Número de processo, nome de parte ou de cliente, CPF/CNPJ e capturas nunca
  entram em commit, issue, PR ou relatório — lá vão números agregados.
- Nunca mande código, ledger, logs ou planilhas deste projeto para modelos
  gratuitos (OpenCode free tier, Nous `:free`).

## Fixe a tarefa e o oráculo

- A tarefa completa é uma rodada sobre uma carga fixa: mesma planilha, aba,
  `--limite`, perfil e flags. A simulação (sem `--executar`) não pula nada do
  ledger, então repetir a mesma simulação é carga equivalente.
- Oráculo do que a rodada decide: o `Resumo desta rodada: {...}` do log, a
  lista `data/nao_encontrados_simulacao.csv` (compare com `cmp` ou pela
  contagem, sem listar) e, numa rodada real, a `situacao` de cada par
  (processo, tarefa) no ledger. Antes e depois têm de dar o mesmo.
- O ledger não é independente do código: até a 1.8 ele dizia `ok` para 6,9% de
  tarefas que não existiam (README). Mexeu no Salvar ou na confirmação? O
  oráculo de "gravou" é a grade do processo, via `scripts/auditar.py` — que usa
  `contar_tarefas` e `_esperar_carregar`; se a mudança tocar neles, confira à
  mão na pasta de teste.
- Registre commit, máquina, versão do Chrome, horário e o comando.

## Reaproveite antes de medir de novo

- README "Desempenho medido": ~2,3 s por processo só buscando, ~9,6 s no fluxo
  completo; MANUAL: `auditar.py` ~2,5 s por processo.
- A linha de progresso a cada 25 processos traz a média acumulada e o placar,
  sem CNJ; `grep 's/processo | decorrido'` no log pega só ela (um padrão mais
  solto casa URLs `/processos/processos/` de mensagens de erro, com CNJ).
- O `quando` do ledger dá a duração aproximada por linha de rodadas reais já
  feitas — consulta em [medição](references/medicao.md#duração-por-linha-pelo-ledger).

## Onde vai o tempo de um processo

Fluxo completo (`Rodada._um_processo` → `AutomadorLegalOne`): página de busca;
página de compromissos para `contar_tarefas` (pulada com `--rapido`, perdendo a
distinção recadastro × novo); página do formulário; lookups de status e
responsável; Salvar e resposta. Por cima disso:

- **Pausas fixas**: `DEBOUNCE_DELAY` (0,4 s) depois de digitar a descrição (até
  `TENTATIVAS_DESCRICAO` vezes) e antes do ENTER do responsável;
  `PAUSA_ENTRE_PROCESSOS` (0,5 s) em todo processo. Piso de ~1,3 s por cadastro
  — inferência pelo código; meça.
- **Esperas explícitas**: `WebDriverWait(driver, TIMEOUT_PADRAO)` com o
  intervalo de consulta padrão do Selenium (`POLL_FREQUENCY`, 0,5 s em
  `selenium/webdriver/support/wait.py` da versão instalada): uma condição que
  não está pronta na primeira olhada custa a granularidade da consulta.
- **Esperas que estouram em silêncio**: `_esperar_carregar`, `_esperar_ajax` e
  `_esperar_mascara_sumir` engolem o `TimeoutException`. Uma condição presa
  custa 20 s por ocorrência sem aparecer no log.

| Custo observado | Correção candidata | Condição a estabelecer |
| --- | --- | --- |
| Pausa fixa | espera explícita por um sinal | o sinal foi observado (skill `investigacao-legal-one`) e vale em toda variação da tela; sem sinal, a pausa fica |
| Espera engolida estourando | registrar quando estoura e corrigir a condição | frequência medida antes; nunca baixar `TIMEOUT_PADRAO` às cegas |
| Granularidade da consulta | `poll_frequency` menor no `WebDriverWait` do automador | ganho medido por espera; mais consultas são chamadas ao Chrome local |
| Página só de informação | `--rapido`, que já existe | perder o recadastro e a conferência do `SalvarIncerto` é decisão do usuário |

`PAUSA_ENTRE_PROCESSOS` é respiro para o servidor, não desperdício: não se
corta por velocidade. Pela mesma razão, o comentário do `DEBOUNCE_DELAY` do
responsável diz que não há estado no DOM antes do ENTER — trocar exige
evidência nova, não palpite.

## Meça sem martelar o Legal One

- Declare o orçamento antes (rodadas × processos × páginas, mais a conferência
  de tipo e responsável de cada rodada) e peça o ok do usuário. Conta em
  [medição](references/medicao.md#orçamento-de-acessos).
- Só simulação ou `--so-buscar`, com `--limite` pequeno (10 a 20), em
  sequência, com a pausa mantida. Nunca `--executar` para medir (cria tarefa;
  recadastro duplica), nunca abas ou sessões em paralelo, nunca ao mesmo tempo
  que uma rodada de produção, nunca laço em endpoint de lookup.
- Pare na sessão expirada (código 3), num disjuntor ou com `erro` subindo.
- Cronometre sem editar o código versionado: um wrapper em `/tmp/<tarefa>/` que
  envolve os métodos do `AutomadorLegalOne` e chama `main.main(...)`, com
  `FATURAMENTO_LOG_FILE` apontado para `/tmp` (receita em
  [medição](references/medicao.md#cronômetro-por-método)).
- Antes e depois intercalados (A, B, A, B…), pelo menos três de cada, na mesma
  janela de horário; reporte mediana e dispersão. O primeiro processo de cada
  rodada carrega a conferência inicial e o cache frio do Chrome: separe.

## Caches e estado reaproveitado

Todo cache diz chave, dono, invalidação e tempo de vida. O que existe hoje:
`catalogo.Resolucao`, chave = valor pedido de tipo ou responsável, dono = a
rodada (`_modo_rodada`), vida = uma rodada — a conferência "antes do primeiro
cadastro" é garantia do README. Guardar a árvore de tipos ou os usuários entre
rodadas enfraquece essa garantia; guardar resultado de busca entre rodadas
duplica o papel do ledger, que já tem invalidação explícita (`--retentar`,
`--processo`).

## Compare e limite a afirmação

Reporte: o gargalo, a mudança no dono, a semântica preservada (mesmo resumo,
mesma lista de conferência, mesma tarefa enviada), os testes rodados
(`python -m pytest`, `ruff check .`), carga, número de rodadas, mediana e
dispersão antes e depois, acessos gastos e o que não foi medido. Um retry que
passa não explica uma falha. Se os números mudarem, o README "Desempenho
medido" e o MANUAL ("Ajustes finos") mudam junto. Pare quando o gargalo
demonstrado estiver resolvido ou o ganho restante for especulativo.
