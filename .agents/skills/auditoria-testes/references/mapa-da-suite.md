# Mapa da suíte

Levantado em `d2bf736` (22/10/2026). É ponto de partida: confira contra a
árvore atual antes de citar.

## Seleção e descoberta

- `pyproject.toml`: `testpaths = ["tests"]`, `pythonpath = ["src"]`,
  `addopts = "-q --strict-markers"`. Os módulos vivem soltos em `src/`, sem
  `__init__.py`; `tests/conftest.py` também põe `src/` no `sys.path`.
- `tests/conftest.py` zera `FATURAMENTO_LOG_FILE` **antes** de importar
  `config`, para os testes não escreverem no log de produção. Qualquer coisa
  que importe `config` antes dele (um plugin carregado com `-p`, por exemplo)
  voltaria a escrever em `logs/faturamento.log`.
- O fixture `dados_tmp` desvia `DATA_DIR`, `LEDGER_FILE`, `RELATORIO_CSV` e as
  duas listas de conferência para `tmp_path`, e zera `PAUSA_ENTRE_PROCESSOS`.
  Todo teste que chama `main.main(...)` ou abre `config.LEDGER_FILE` precisa
  dele (ou de `registro`, que o usa).
- Imports cruzados: `test_main.py` e `test_catalogo.py` importam
  `AutomadorFalso`, `achou`, `processo`, `ARVORE` e `USUARIOS` de
  `test_rodada.py`. Rodar um arquivo sozinho (`python -m pytest
  tests/test_main.py`) tem de funcionar.
- Positivo e negativo: um arquivo novo `tests/test_*.py` (ou `*_test.py`) é
  descoberto sem registro; um nome fora desses padrões, ou fora de `tests/`,
  não roda e não avisa. Confira a contagem de testes antes e depois de mexer na
  seleção.

## O que cada arquivo protege

| Arquivo | Dono | Protege |
| --- | --- | --- |
| `test_busca.py` | `legalone.interpretar_busca` | em qual pasta a tarefa vai: número exato, só tipo `Processo`, ambíguo, href com query |
| `test_pos_salvar.py` | `legalone.situacao_pos_salvar` | o que conta como gravado: `/processos/tarefas/Edit` nunca é sucesso, aviso antes de erro |
| `test_catalogo.py` | `src/catalogo.py` | tipo pelo caminho inteiro, nome repetido, responsável ambíguo ou inativo |
| `test_datas.py` | `src/datas.py` | formatos de data/hora, duração de 30 min, recusas do Legal One antes do Chrome |
| `test_perfis.py` | `config.carregar_perfis` e `tarefas.toml` | campos obrigatórios, chave desconhecida, nome reservado, os perfis de produção do arquivo versionado |
| `test_planilha.py` | `src/planilha.py` | colunas aceitas (inclusive as quatro da cobrança), deduplicação, modo planilha |
| `test_ledger.py` | `src/ledger.py` | trava de rebaixamento, vazio não apaga preenchido, `esquecer`, migrações |
| `test_rodada.py` | `main.Rodada` | o laço: disjuntor de não encontrados, cota, sessão expirada, Ctrl+C, `SalvarIncerto` |
| `test_main.py` | `main.py` (CLI e preparação) | validação de flags, combinações recusadas, fila, relatórios, ponta a ponta com o falso |

`scripts/` não tem teste próprio (README); a consulta que eles usam,
`Ledger.cadastrados_entre`, tem (`test_cadastrados_entre_recorta_a_leva_por_horario`).

## Falsos e o que eles não cobrem

- `AutomadorFalso` (`tests/test_rodada.py`) responde por dicionário e anota o que
  foi pedido. Ele substitui `legalone.AutomadorLegalOne` inteiro; nos testes de
  `main.main`, `conectar` vira `lambda: object()` e `AutomadorLegalOne` vira
  `lambda *a: automador`.
- Sem cobertura nenhuma, portanto: os seletores e XPaths, os `execute_script`
  (grade, compromissos, Pendo, máscara, aviso `popup_ok`), as esperas
  (`WebDriverWait`, `readyState`, `jQuery.active`), `DEBOUNCE_DELAY`,
  `_buscar_json` e o `PATH` sem chocolatey de `conectar`.
- Formas montadas à mão que imitam o Legal One — cada uma é uma suposição sobre
  o sistema real:
  - a grade de busca por posição de coluna (`_linha` com `config.COL_*`) e o
    link `/processos/processos/details/<id>`;
  - a árvore de `LookupTreeTiposTarefa` como `Rows` com `Id`/`Value`/
    `ParentId`/`Path` (`ARVORE`);
  - a busca de usuários casando por trecho do nome, sem acento nem caixa
    (`AutomadorFalso.buscar_usuarios`);
  - as URLs e textos de aviso e erro de `test_pos_salvar.py`.
- Se o Legal One mudar qualquer uma, a suíte continua verde. Reobservar é com a
  skill `investigacao-legal-one`; o teste só guarda a forma que alguém observou.

## Perturbações

Faça numa worktree isolada, uma por vez, rode `python -m pytest` e desfaça.
"Esperado" é o que a leitura do código prevê; o que vale é o resultado da
execução.

| Mutação | Esperado |
| --- | --- |
| `situacao_pos_salvar` devolve `SALVOU` para `/processos/tarefas/edit` | falham `test_formulario_devolvido_nunca_e_sucesso` e as variações de endereço |
| `interpretar_busca` sem o filtro `TIPO_ACEITO` | falham `test_escolhe_a_pasta_do_tipo_processo` e `test_so_recurso_ou_incidente_nao_e_chute` |
| `_SQL_NAO_REBAIXAR` sempre falso | falha `test_ok_nao_e_rebaixado_para_ja_existia` e vizinhos |
| `inteiro_positivo` aceitando `0` | falha `test_inteiro_positivo_recusa` |
| `config.COL_PROCESSO` trocado | **verde** — o builder usa a mesma constante; só a grade real pega |
| `main.SAIDA_SESSAO = 4` | **verde** provável — os testes comparam com a constante; quebra `scripts/rodada_ate_a_meta.ps1` e o MANUAL |
| `MAX_ERROS_SEGUIDOS` alto ou sem o `break` do disjuntor de erros | **verde** provável — nenhum teste cita `MAX_ERROS_SEGUIDOS` nem `disjuntor_erros` |
| `dados_tmp` sem desviar `LEDGER_FILE` | testes verdes, mas aparece `data/ledger.sqlite3` na checkout — só a conferência de `data/` vazia pega |
| sem o `time.sleep(config.DEBOUNCE_DELAY)` | **verde** — `AutomadorLegalOne` não é testado |

Um "verde" confirmado é achado (custo sustentado ou lacuna de proteção), não
defeito: descreva o que deixaria de ser pego e proponha o teste mínimo, sem
escrever antes de autorizado.

## Medição

- Local: `time .venv/bin/python -m pytest` e `python -m pytest --durations=10`
  para achar os mais lentos. Em 22/10/2026: ~1,1 s de pytest, ~1,3 s de parede.
- CI: tempos por job e passo da execução, com `gh run view <id> --json jobs`
  (se o `gh` estiver autenticado no repositório privado). Do disparo ao início
  do job entram fila e dependências; sem os carimbos de elegibilidade, reporte a
  soma e diga que a divisão é desconhecida.
- Cache: os três jobs usam `actions/setup-python` com `cache: pip` e
  `cache-dependency-path: requirements-dev.txt`. A chave é o hash desse
  arquivo, cujo texto só traz `-r requirements.txt`: um bump em
  `requirements.txt` (selenium, openpyxl) não muda a chave. Como é cache de
  downloads do pip, a instalação continua correta; o custo possível é baixar de
  novo o que mudou — hipótese, a medir antes de propor mudança. Para afirmar
  reuso ou invalidação, mude um input e observe o passo de restore.
- Compare execuções equivalentes: mesma contagem de testes, mesmas pernas da
  matriz, mesmo runner. Uma execução com menos testes ou que parou cedo não
  prova aceleração.
