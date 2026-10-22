# Inventário do contrato

Levantado em `d2bf736` (22/10/2026). Confira contra a árvore atual: a fonte da
verdade é o código, e este arquivo só aponta onde olhar.

## Flags de `src/main.py`

| Flag | No argparse | Validação depois do parse |
| --- | --- | --- |
| `--planilha` | texto | obrigatória salvo `--relatorio` (`_modo_rodada`); arquivo inexistente → 2 |
| `--tarefa` | `choices` = perfis do `tarefas.toml` + `auto` + `planilha` (sem `choices` se o arquivo estiver quebrado) | não combina com `--descricao`; trava `dica_arquivo` (`_conferir_planilha`) |
| `--descricao`, `--responsavel` | texto | avulsa exige `--status` e `--responsavel` (`_perfil_da_rodada`) |
| `--tipo` | texto | conferido no Legal One (`_resolver_perfis`) |
| `--status` | `type=status_arg` | — |
| `--forcar-planilha` | `store_true` | desliga a trava de nome |
| `--abas` | `nargs="+"` | aba inexistente → 2 (`planilha.ler`) |
| `--tipo-contem`, `--status-planilha` | texto | — |
| `--limite`, `--max-cadastros` | `type=inteiro_positivo` | `--max-cadastros` com `--so-buscar` só avisa |
| `--processo` | `nargs="+"`, `metavar="CNJ"` | fora da planilha → aviso |
| `--data` / `--inicio` | mesmo `dest="data"` | `_agenda_da_rodada` e `_conferir_datas` → 2 |
| `--fim`, `--publicacao`, `--disponibilizacao` | texto | idem |
| `--executar`, `--retentar`, `--rapido`, `--pular-existentes`, `--so-buscar`, `--relatorio` | `store_true` | `--so-buscar --executar` → 2; `--pular-existentes --rapido` → 2 |
| `--dia` | `type=dia_iso` | sem `--relatorio` só avisa |

O parser usa `allow_abbrev` padrão (ligado) e `RawDescriptionHelpFormatter`,
para o `epilog` de exemplos sair como está escrito.

## Códigos de saída

| Código | Constante | Quem produz | MANUAL | ps1 | Teste |
| --- | --- | --- | --- | --- | --- |
| 0 | `SAIDA_OK` | fila terminou, cota atingida, "Nada a fazer", `--relatorio` | "Códigos de saída" | para: "a fila acabou" | `test_codigo_de_saida`, `test_fila_vazia_termina_sem_abrir_o_chrome` |
| 1 | `SAIDA_ABORTADA` | `conectar` falhou; conferência de tipo/responsável falhou; disjuntor; e qualquer traceback | "O programa não conecta no Chrome", "PARADO: ..." | espera 20 s e religa | `test_chrome_fora_do_ar_devolve_codigo_de_rodada_abortada` |
| 2 | `SAIDA_USO` | `ErroDeUso` em `main()`; erro do argparse | "Como as flags se combinam" | para | `test_status_invalido_para_na_cli` (número literal), job `cli` (número literal) |
| 3 | `SAIDA_SESSAO` | `SessaoExpirada` na conferência ou no laço; `scripts/auditar.py` | "SESSAO EXPIRADA" | para | `test_sessao_expirada_aborta_a_rodada_inteira` |
| 130 | `SAIDA_INTERROMPIDA` | `KeyboardInterrupt` dentro de `Rodada.executar_fila` | "Preciso parar no meio" | para | `test_ctrl_c_encerra_limpo` |

Fora da tabela, e sem teste: traceback (1 do Python) e `Ctrl+C` fora do laço.

## Variáveis de ambiente

`DEBUG_PORT` (padrão 9222), `LOG_LEVEL` (inválido cai em `INFO`) e
`FATURAMENTO_LOG_FILE` (vazio desliga o arquivo), todas lidas em
`src/config.py` na importação e documentadas no MANUAL. O ps1 não lê
`DEBUG_PORT`.

## CLIs dos scripts

| Script | Flags | Saída |
| --- | --- | --- |
| `scripts/auditar.py` | `--desde` (obrigatória), `--ate` (padrão `9999`), `--saida` (padrão `data/auditoria_<desde>.csv`) | progresso no stdout; 0, ou 3 na sessão expirada |
| `scripts/planilha_da_leva.py` | `--desde`, `--ate`, `--saida` (obrigatórias), `--aba` | uma linha no stdout; 0 |
| `scripts/rodada_ate_a_meta.ps1` | `-Planilha`, `-Meta` (obrigatórios), `-Tentativas` (12), resto depois de `--` vai para o `main.py` | `logs\rodada_<data-hora>.log` |

## Revisão de mensagens

Para revisar várias mensagens de uma vez, monte em `/tmp/<tarefa>/mensagens.csv`
uma linha por mensagem, da mais danosa para a menos:

`risco | onde (arquivo:função) | gatilho | texto atual | o que pode dar errado | texto proposto | status | como foi verificado`

- "O que pode dar errado" é o efeito em quem lê: repetir o comando sem efeito,
  religar um laço no ps1, cadastrar a tarefa errada, apagar o que não devia.
- O texto proposto diz o que fazer em seguida e se repetir adianta — é a mesma
  informação que o código de saída carrega.
- Mensagem que sai no `DETALHE` do ledger também aparece no `relatorio.csv`.
- "Status" e "verificado" só valem com teste ou execução de verdade; texto que
  só foi lido fica como proposta.

## Conferência flags × MANUAL

`/tmp/<tarefa>/conferir_flags.py`, rodado da raiz com `FATURAMENTO_LOG_FILE`
vazio. Compara as flags do argparse com as da seção "Referência das flags" (até
o primeiro `###`). Em 22/10/2026 as 25 batiam; sem a linha de `--rapido` no
MANUAL, ele acusa a falta e sai 1.

```python
"""Compara as flags do argparse com a tabela "Referencia das flags" do MANUAL."""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
import main

capturado = {}


def capturar(self, args=None, namespace=None):
    capturado["parser"] = self
    raise SystemExit(0)


argparse.ArgumentParser.parse_args = capturar
try:
    main.argumentos([])
except SystemExit:
    pass

no_codigo = {opcao for acao in capturado["parser"]._actions
             for opcao in acao.option_strings
             if opcao.startswith("--") and opcao != "--help"}
manual = Path("MANUAL.md").read_text(encoding="utf-8")
tabela = manual.split("## Referência das flags", 1)[1].split("### ", 1)[0]
no_manual = set(re.findall(r"`(--[a-z-]+)`", tabela))

print("so no codigo:", sorted(no_codigo - no_manual) or "-")
print("so no MANUAL:", sorted(no_manual - no_codigo) or "-")
sys.exit(1 if no_codigo != no_manual else 0)
```

Ele confere só a presença das flags. Padrão, argumento e texto de cada linha,
as combinações e os códigos se conferem lendo, contra `--help` e contra as
tabelas acima.
