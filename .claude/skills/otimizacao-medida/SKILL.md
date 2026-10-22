---
name: otimizacao-medida
description: Otimiza o tempo por processo da rodada do FaturamentoLegalOne (busca, checagem de duplicata, formulário, Salvar) com medição antes e depois, o ledger e o placar da rodada como oráculo e um orçamento de acessos que não martela o servidor do Legal One — pausas fixas (config.DEBOUNCE_DELAY, PAUSA_ENTRE_PROCESSOS) versus esperas explícitas, esperas que estouram em silêncio, caches. Use quando a rodada estiver lenta ou antes de mexer em esperas, pausas e timeouts de src/legalone.py. Pule para a velocidade da suíte ou da CI (auditoria-testes) e para bug de correção sem ângulo de desempenho.
metadata:
  version: "1"
---

# Otimização medida

Cópia canônica: [`.agents/skills/otimizacao-medida/SKILL.md`](../../../.agents/skills/otimizacao-medida/SKILL.md).
Leia-a agora e siga-a; `references/` e `agents/openai.yaml` ficam ao lado dela.

Isto é um stub, não um symlink: o Git para Windows grava symlink como arquivo de
texto por padrão, e este repositório também é usado no Windows. Edite só a cópia
canônica; mantenha este frontmatter igual ao dela.
