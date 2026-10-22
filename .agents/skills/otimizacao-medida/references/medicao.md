# Medição

Receitas para medir a rodada sem editar o código versionado e sem expor dado
de cliente. Tudo roda da raiz do projeto, com arquivos em `/tmp/<tarefa>/`.

## Orçamento de acessos

Conte antes de pedir o ok do usuário. Pelo código de `src/legalone.py`:

| Modo | Por processo | Por rodada |
| --- | --- | --- |
| `--so-buscar` | 1 página (busca) | — |
| simulação | busca + compromissos (sem `--rapido`) + formulário, mais os lookups de status e responsável | `LookupTreeTiposTarefa` uma vez e `LookupGridUsuario` por responsável distinto |

Exemplo: três rodadas A e três B, simulação com `--limite 10` ≈ 6 × (10 × 3
páginas + lookups) ≈ 180 páginas e 6 conferências iniciais. Escreva a conta no
registro da medição. Se o plano pedir muito mais que isso, reveja o plano
antes de pedir mais acesso.

## Cronômetro por método

`/tmp/<tarefa>/cronometro.py`, fora do repositório. Envolve os métodos do
`AutomadorLegalOne`, roda o `main.main` de verdade e imprime só agregados por
método — nenhum CNJ.

```python
"""Cronometra os metodos do AutomadorLegalOne numa rodada simulada."""
import collections
import functools
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))

import legalone
import main

METODOS = ("buscar_processo", "contar_tarefas", "cadastrar_tarefa",
           "_preencher_descricao", "_selecionar_tipo", "_selecionar_status",
           "_preencher_responsavel", "_esperar_carregar", "_esperar_ajax",
           "_esperar_mascara_sumir", "_esperar_resposta_do_salvar")
tempos = collections.defaultdict(list)


def cronometrar(nome):
    original = getattr(legalone.AutomadorLegalOne, nome)

    @functools.wraps(original)
    def medido(self, *args, **kwargs):
        inicio = time.perf_counter()
        try:
            return original(self, *args, **kwargs)
        finally:
            tempos[nome].append(time.perf_counter() - inicio)

    setattr(legalone.AutomadorLegalOne, nome, medido)


# Pelo argparse, e nao pelo texto: "--exec" tambem vale como --executar.
if main.argumentos(sys.argv[1:]).executar:
    sys.exit("cronometro.py so mede simulacao: tire o --executar")
for nome in METODOS:
    cronometrar(nome)

codigo = 1
try:
    codigo = main.main(sys.argv[1:])
finally:
    for nome, valores in sorted(tempos.items()):
        print(f"{nome:30} n={len(valores):4} "
              f"mediana={statistics.median(valores):.2f}s "
              f"max={max(valores):.2f}s total={sum(valores):.1f}s",
              file=sys.stderr)
sys.exit(codigo)
```

```bash
FATURAMENTO_LOG_FILE=/tmp/<tarefa>/rodada-A1.log \
  .venv/bin/python /tmp/<tarefa>/cronometro.py --planilha <arquivo> --limite 10
```

No PowerShell, `$env:FATURAMENTO_LOG_FILE = "..."` antes do comando. O log da
medição fica fora de `logs/faturamento.log`, que é onde se procuram as falhas
reais. A simulação ainda reescreve `data/relatorio.csv` (a partir do ledger,
sem mudar o conteúdo) e `data/nao_encontrados_simulacao.csv`.

Leitura:

- Os tempos são inclusivos: `buscar_processo` contém o seu `_esperar_carregar`.
- Uma espera engolida que estourou aparece como `max` perto de `TIMEOUT_PADRAO`
  (20 s). Conte quantas vezes, em quantos processos.
- O primeiro processo carrega a conferência inicial e o cache frio: compare as
  medianas, não os totais, ou descarte o primeiro.
- Pausas fixas não aparecem como método. Some à mão: `DEBOUNCE_DELAY` × chamadas
  de `_preencher_descricao` (mais as repetições) e de `_preencher_responsavel`,
  e `PAUSA_ENTRE_PROCESSOS` × processos.

## Duração por linha pelo ledger

Só com pedido do usuário, só de rodadas reais (a simulação não escreve no
ledger), numa cópia consistente e só com agregados:

```python
import sqlite3
import statistics
from datetime import datetime

DESDE, ATE = "2026-10-01T09:00", "2026-10-01T18:00"   # a janela de UMA rodada

origem = sqlite3.connect("file:data/ledger.sqlite3?mode=ro", uri=True)
copia = sqlite3.connect("/tmp/<tarefa>/ledger.sqlite3")
origem.backup(copia)
origem.close()

linhas = copia.execute(
    "SELECT situacao, quando FROM processos "
    "WHERE quando >= ? AND quando < ? ORDER BY quando", (DESDE, ATE)).fetchall()
por_situacao = {}
for (_, antes), (situacao, agora) in zip(linhas, linhas[1:]):
    delta = (datetime.fromisoformat(agora) - datetime.fromisoformat(antes)).total_seconds()
    if delta <= 120:                         # mais que isso e intervalo, nao processo
        por_situacao.setdefault(situacao, []).append(delta)
for situacao, deltas in sorted(por_situacao.items()):
    print(situacao, len(deltas), f"mediana {statistics.median(deltas):.1f}s")
```

Limites do que isso mede:

- `quando` tem resolução de segundo e guarda a última escrita do par: num
  cadastro, a de depois do Salvar.
- Um cadastro nosso (`ok`, `recadastrada`) não é reescrito por passadas
  posteriores; outras situações são. Escolha a janela de uma rodada só (o
  início está no log) e saiba que linhas refeitas depois saem dela.
- O delta inclui `PAUSA_ENTRE_PROCESSOS` e cai na linha que terminou; um
  processo descartado pelo disjuntor (`esquecer`) some e soma o tempo dele ao
  seguinte.
- Apague `/tmp/<tarefa>/ledger.sqlite3` ao terminar.
