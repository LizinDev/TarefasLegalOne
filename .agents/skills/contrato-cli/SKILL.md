---
name: contrato-cli
description: Desenha e revisa o contrato de linha de comando do FaturamentoLegalOne — flags de src/main.py e de scripts/, códigos de saída, combinações recusadas, o que sai em stderr e em arquivo, mensagens de erro acionáveis — e mantém MANUAL.md, README, scripts/rodada_ate_a_meta.ps1 e o job cli da CI em sincronia com o código. Use ao acrescentar, renomear ou remover flag, ou ao mudar validação, código de saída, mensagem de erro de uso ou algo que um script consome. Pule para refatoração interna que não muda argumentos, códigos, arquivos nem mensagens, e para dúvidas de operação (MANUAL.md).
metadata:
  version: "1"
---

# Contrato da CLI

> Adapted from morluto/rea `rea-tool-design` (MIT, © 2026 morluto).

Quatro leitores dependem da CLI: quem opera (as receitas do MANUAL), o
`scripts/rodada_ate_a_meta.ps1` (sem supervisão, decide pelo código de saída),
o job `cli` do `ci.yml` e `tests/test_main.py`. Uma mudança só está pronta
quando os quatro concordam com o código.

## Dados de cliente (classe C)

- Notas e rascunhos ficam em `/tmp/<tarefa>/`, fora da árvore.
- Exemplos de ajuda, MANUAL e testes usam placeholder (`"..."`, `<CNJ>`, o
  `0000001-11.2025.8.05.0001` dos testes). Nunca CNJ real, nome de parte ou de
  cliente, CPF/CNPJ nem trecho de log ou captura — nem em commit, issue ou PR.
- Mensagem nova não traz o que o código evita logar, como CPF e e-mail da busca
  de usuários (`buscar_usuarios`).
- Nunca mande código ou dados deste projeto para modelos gratuitos (OpenCode
  free tier, Nous `:free`).

## Onde o contrato mora

| Peça | Onde |
| --- | --- |
| Flags, tipos, ajuda e exemplos | `argumentos()` em `src/main.py`, com o `epilog` |
| Códigos de saída | `SAIDA_*` e a docstring do topo de `src/main.py`; `Rodada.codigo_saida()`; `main()` (`ErroDeUso` → 2) |
| Recusas e avisos | `_modo_rodada`, `_perfil_da_rodada`, `_conferir_planilha`, `_conferir_datas`, `_resolver_perfis` |
| Operação | MANUAL: "Referência das flags", "Como as flags se combinam", "Códigos de saída", "Variáveis de ambiente", "Quando algo dá errado" |
| Porquê | README: as decisões, "Como os erros são tratados", "Versão" |
| Consumidores | `scripts/rodada_ate_a_meta.ps1`, job `cli` do `ci.yml`, `tests/test_main.py` |
| CLIs próprias | `scripts/auditar.py`, `scripts/planilha_da_leva.py` |

Inventário por flag e por código, com produtor, documentação e consumidor, em
[o inventário](references/inventario.md).

## Regras

- **Simulação é o padrão.** Nada grava no Legal One sem `--executar`, e a
  simulação não escreve no ledger. Flag nova que grava herda as duas coisas.
- **Recusar cedo, com 2.** Combinação perigosa, ou dado que o Legal One
  recusaria, vira `ErroDeUso` antes de abrir o Chrome e antes de qualquer
  cadastro; combinação inofensiva vira aviso e segue. O argparse também sai 2 —
  coincide de propósito.
- **O código diz o que fazer depois**: 0 acabou (inclusive "nada a fazer" e
  cota atingida); 1 abortou e repetir adianta; 2 repetir não muda nada; 3 falta
  login de alguém; 130 interrompida. O ps1 trata 0, 2, 3 e 130 e **religa em
  qualquer outro**: código novo sem ramo no `switch` vira laço de religar.
- **Flags estáveis.** Renomear quebra o ps1, o MANUAL e o hábito de quem opera;
  prefira apelido, como `--data`/`--inicio` (`dest="data"`). O argparse está com
  `allow_abbrev` ligado: hoje `--exec` vale como `--executar`, e uma flag nova
  com o mesmo prefixo deixa a abreviação ambígua (erro 2). Remover flag é
  quebra: decisão do usuário, registrada em "Versão".
- **Validação no tipo.** `inteiro_positivo`, `dia_iso` e `status_arg` recusam na
  hora; `--max-cadastros 0` é erro porque zero é falso em Python e viraria "sem
  limite". Flag numérica nova segue o mesmo padrão.
- **Onde sai o quê.** `src/main.py` loga no stderr e em `logs/faturamento.log`
  (ou `FATURAMENTO_LOG_FILE`); no stdout, só o `--help`. Os resultados são
  arquivos (`data/relatorio.csv`, as listas de conferência, a planilha do dia)
  e o código de saída; o ps1 guarda o stderr no log da rodada. Os scripts
  imprimem progresso no stdout. Não passe resultado para o stdout sem decidir
  quem o lê; quando um script ou agente precisa de um resultado, dê a ele um
  código ou arquivo estável (como o ps1 faz com o código e o ledger), e não
  texto de log para raspar.
- **Mensagem acionável.** Diz o que está errado, onde (aba, linha, número) e o
  que fazer, sem stack trace para erro de usuário (o `B904` fica ignorado no
  `pyproject.toml` por isso); o modelo é o `ErroDeUso` de `_conferir_planilha`.
  Falha de automação vai para o `DETALHE` do ledger, cortado em 400 caracteres
  em `executar_fila`: tem de se explicar ali. Para revisar mensagens em lote,
  use a tabela de [revisão de mensagens](references/inventario.md#revisão-de-mensagens).
- **Arquivos também são contrato.** Coluna nova do `relatorio.csv` entra no fim
  (README); separador `;`, UTF-8 com BOM. O ps1 lê o ledger direto
  (`processos`, `situacao`, `quando`) e os scripts usam `cadastrados_entre`.

## Pontos em aberto (confira antes de confiar)

- Os testes comparam com `main.SAIDA_*`; só o 2 é conferido como número. Mudar
  o 1, o 3 ou o 130 passaria verde. *Observação.*
- Exceção não tratada em `_modo_rodada` sai com traceback e código 1 do Python,
  o mesmo do disjuntor — o ps1 religaria. *Inferência pelo código.*
- `Ctrl+C` antes do laço (lendo a planilha, conectando, conferindo tipos) não
  passa pela `Rodada`; o código resultante depende da plataforma. *Inferência.*
- O ps1 consulta `http://127.0.0.1:9222` fixo; `DEBUG_PORT` muda só o
  programa. `scripts/auditar.py` sai 3 na sessão expirada e com traceback se
  não conectar. *Observação.*

Classifique cada um como reproduzido, hipótese ou sem evidência antes de
propor mudança; um teste com o número literal reproduz o primeiro.

## Mudar o contrato, nesta ordem

1. Proponha: flag ou código, semântica, a alternativa existente mais próxima
   (estender antes de criar), o efeito no ps1, na CI e no MANUAL, e como
   verificar. Em pedido de desenho, pare aqui.
2. Implemente em `argumentos()` e na validação, com mensagem acionável.
3. Teste o comportamento e, para código de saída, o **número** literal.
4. Documente na mesma mudança: a linha da tabela de flags e a seção detalhada,
   "Como as flags se combinam", "Códigos de saída", "Quando algo dá errado", a
   docstring do topo de `main.py`, o `epilog`; o README quando muda uma
   decisão; o ps1 quando muda código ou flag que ele passa; o job `cli` quando
   muda `--help`, `--relatorio` ou o código 2.
5. Verifique: `python -m pytest`, `ruff check .`, `python src/main.py --help` e
   a [conferência flags × MANUAL](references/inventario.md#conferência-flags--manual).
6. Proponha a entrada em "Versão" do README e o `config.VERSION`. Commit, tag e
   release não são autorizados por esta skill.
