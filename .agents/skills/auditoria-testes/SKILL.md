---
name: auditoria-testes
description: Audita a suíte pytest, o ruff e os workflows ci.yml, codeql.yml e seguranca.yml do FaturamentoLegalOne — o que de fato executa, se um teste verde protege alguma coisa (prova por perturbação), deriva dos automadores falsos em relação ao Legal One real e custo medido. Use para investigar a suíte ou a CI como um todo, ou antes de mudá-las. Pule para escrever o teste de uma funcionalidade nova, para uma falha isolada de causa óbvia e para dúvidas de operação da rodada (essas estão no MANUAL.md).
metadata:
  version: "1"
---

# Auditoria de testes e CI

> Adapted from morluto/rea `rea-ci-tests-audit` (MIT, © 2026 morluto).

Descobrir quais checagens ainda pegam regressão de verdade e quais custos dá
para cortar sem perder essa proteção. O resultado pode ser uma correção
verificada, uma recomendação com evidência ou a decisão explícita de parar.

Use os comandos de hoje do [README](../../../README.md#desenvolvimento) e do
`pyproject.toml`, e não os lembrados de outra auditoria. Investigar não autoriza
editar; esta skill não autoriza commit, push, issue nem PR.

## Dados de cliente (classe C)

- Notas e saídas da auditoria ficam fora da árvore versionada, em
  `/tmp/<tarefa>/`. O `.gitignore` cobre `data/`, `logs/`, `*.csv`, `*.xlsx` e
  `*.sqlite3`, mas não `*.json`, `*.har` nem `*.md` soltos na raiz.
- Número de processo (CNJ), nome de parte ou de cliente, CPF/CNPJ e capturas do
  Legal One nunca entram em commit, issue, PR ou fixture. Fixture usa
  placeholder, como o `0000001-11.2025.8.05.0001` de `tests/test_rodada.py`.
- A auditoria não abre `data/`, `logs/`, `Planilhas/`, `Cadastros/`, `*.sqlite3`
  nem `*.xlsx`: a suíte não precisa deles.
- Nunca mande código ou dados deste projeto para modelos gratuitos (OpenCode
  free tier, Nous `:free`).

## Fixe a linha de base executada

- Registre `git rev-parse HEAD`, `git status --short`, as versões de Python,
  pytest e ruff e o comando exato. Para mudar ou comparar código, use uma
  worktree isolada; nunca a checkout de outra tarefa.
- Comandos, da raiz e com a venv do projeto: `.venv/bin/python -m pytest` e
  `.venv/bin/ruff check .` (no Windows, `python -m pytest` e `ruff check .`).
  O `pyproject.toml` fixa `testpaths`, `pythonpath = ["src"]` e
  `-q --strict-markers`.
- Confira a venv contra os pinos (`pip freeze` × `requirements*.txt`): em
  22/10/2026 a desta máquina trazia ruff 0.16.1 (pino 0.16.9) e selenium
  4.41.0 (pino 4.49.0). Lint ou teste verde noutra versão não é o da CI.
- Referência, não garantia: em `d2bf736`, 298 testes passaram em ~1,1 s e o
  ruff saiu limpo em 21 arquivos.
- Importar `config` cria `data/` e `logs/` na raiz da checkout. Rode numa
  worktree limpa e confira depois que `data/` continua vazia: um
  `ledger.sqlite3` ali é teste que escapou do fixture `dados_tmp`
  (`tests/conftest.py`) — na checkout principal, teria escrito no ledger de
  produção.

## Siga a CI até o que executa

| Workflow | Gatilho | O que roda de fato |
| --- | --- | --- |
| `ci.yml` | push em main/master, PR, manual | `lint`: ruff no 3.12; `testes`: pytest no Ubuntu 3.10/3.12/3.14 e Windows 3.14, `fail-fast: false`; `cli`: só `requirements.txt`, `--help`, `--relatorio` com ledger vazio e `--executar` sem planilha saindo 2 |
| `seguranca.yml` | segunda 06:00 UTC, manual, PR que mexe em `requirements*.txt` ou nele | `pip-audit` nos dois requirements, com o próprio `pip-audit` sem versão presa |
| `codeql.yml` | segunda 06:30 UTC, manual | CodeQL Python `security-and-quality`; em repo privado sem GHAS falha no upload (README) |

Não há job agregador nem `needs`, e a proteção de branch não está no
repositório: quais checagens são obrigatórias no merge é evidência
indisponível até alguém conferir no GitHub. Antes de dizer "a CI passou",
confira as quatro pernas da matriz e os três jobs. Detalhes de seleção, fakes e
medição em [o mapa da suíte](references/mapa-da-suite.md).

## Prove a proteção, não a cor

Para cada candidato, diga o comportamento observável e o dono (arquivo e
função) e monte a menor reprodução contra o código de produção.

- **Teste verde suspeito**: perturbe o comportamento numa cópia isolada, veja o
  teste falhar pelo motivo certo e desfaça a mutação. Catálogo com o resultado
  esperado em [perturbações](references/mapa-da-suite.md#perturbações).
- **Teste que repete o próprio mock**: `_linha` (`tests/test_busca.py`) monta a
  grade com `config.COL_*`, então trocar a posição de uma coluna no `config` não
  reprova nada. Os testes comparam o código de saída com `main.SAIDA_*`; só o
  `2` é conferido como número (argparse em `test_main.py` e o job `cli`).
- **Falso × real**: separe evidência do falso, da fronteira e do Legal One.
  `AutomadorFalso` (`tests/test_rodada.py`) substitui o `AutomadorLegalOne`
  inteiro e `conectar` vira `lambda: object()`: nenhum teste exercita Selenium,
  seletores, os scripts JS de `src/legalone.py` nem os endpoints de lookup. Só
  as funções puras (`interpretar_busca`, `situacao_pos_salvar`,
  `catalogo.tipos_da_arvore`) são testadas, com formas montadas à mão. Fixture
  não prova comportamento do Legal One; para reobservar a forma real, use a
  skill `investigacao-legal-one`. Evidência real só vem de simulação,
  `--so-buscar` e `scripts/auditar.py` — nunca da CI.
- **Deriva de fixture**: achou uma, procure a família inteira (outros builders,
  outras grafias de URL) e preserve os casos malformados de propósito, como as
  variações de `/processos/tarefas/Edit` em `tests/test_pos_salvar.py`.

Classifique cada achado como **defeito reproduzido**, **custo sustentado**,
**hipótese** ou **evidência indisponível**, com commit, comando, saída, código
de saída, resultado esperado, alcance e a explicação concorrente. Falha na
`main` pode ser preexistente e continua relevante. Repita só para testar uma
hipótese de transiente específica e guarde a falha original: um retry que passa
não estabelece causa nem correção.

## Eficiência sem perder o gate

A suíte roda em segundos; o custo da CI tende a estar em `pip install` e na
espera de runner. Compare trabalho equivalente (mesmas contagens, mesma matriz)
antes de afirmar ganho, e separe instalação, execução e espera. A perna Windows
é proposital — é onde o programa roda — e não se corta por tempo.

## Corrija e entregue dentro do escopo

- Com correção autorizada: menor mudança no dono, mais um teste que falha na
  linha de base pelo motivo certo; rode pytest e ruff de novo.
- Nunca suprima falha, ponha retry genérico, aumente timeout, apague asserção
  distinta, acrescente `# noqa` ou rode `ruff format` (o código é alinhado à
  mão) só para ficar verde. Mexer nesses controles pede motivo demonstrado.
- Reporte cada achado com commit, reprodução, consequência, correção proposta e
  limites da validação; desempenho com carga e números, não só porcentagem.
- Pare quando o trabalho autorizado estiver verificado, quando o ganho restante
  não for comprovado ou quando seguir trocaria correção por velocidade
  especulativa. Liste as incertezas sem abrir novas rodadas de otimização.
