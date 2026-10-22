# Observação passiva

## Preparar

- O Chrome de debug é o do MANUAL ("Abrir o Chrome em modo debug"): porta
  `9222` (ou `DEBUG_PORT`) e um `--user-data-dir` próprio, logado no Legal One.
  O perfil dedicado não é capricho: desde o Chrome 136 a porta de debug é
  ignorada no perfil padrão.
- Abra uma aba nova para investigar; a aba de trabalho do programa é a de
  `window.name` `FATURAMENTO_LEGALONE`. Nada de rodada ou auditoria em
  andamento no mesmo Chrome.
- Telas que importam hoje, e quem as lê no código:

| Tela | Caminho | Lida por |
| --- | --- | --- |
| Busca de processos | `/processos/processos/search?Search=...` | `buscar_processo` (grade, sentinela `#Search`) |
| Compromissos e tarefas da pasta | `/processos/Processos/DetailsCompromissosTarefas/<id>?Search=...` | `contar_tarefas` |
| Nova tarefa | `/processos/tarefas/CreateFromProcesso/<id>` | `cadastrar_tarefa` e auxiliares |
| Formulário devolvido | `/processos/tarefas/Edit` | `situacao_pos_salvar` |
| Lookups | `/config/TipoAndamentoCompromissoTarefa/LookupTreeTiposTarefa`, `/config/Usuarios/LookupGridUsuario` | `listar_tipos`, `buscar_usuarios` |

## O que pedir ao usuário no DevTools

Peça em texto, só o que a pergunta precisa, e diga por que precisa.

- **Elements**: com o seletor de elemento, o `tag`, o `id`, o `name` e as
  classes do elemento. Para um campo, se o `value` está vazio ou preenchido —
  não o valor em si quando for dado de cliente.
- **Network**, com "Preserve log" ligado e filtro em Doc + Fetch/XHR, antes da
  ação:
  - para cada requisição relevante: método, caminho **sem a query**, status,
    tipo e a coluna Initiator (arquivo e linha do script);
  - num redirect, a sequência de status e o caminho de destino;
  - na aba Payload de um POST de formulário, só os **nomes** dos campos;
  - na aba Preview de um JSON, só as chaves e os tipos;
  - em Timing, quando a requisição saiu em relação à ação (por exemplo, quantos
    ms depois da última tecla) — é a evidência para trocar uma pausa fixa.
- **Console**: só mensagens de erro, sem valores.
- **HAR**: não exporte por padrão. Se for indispensável, salve em
  `/tmp/<tarefa>/`, nunca no repositório, e apague no fim. O export pode omitir
  cookies e cabeçalhos de autenticação, conforme a versão e a configuração, mas
  mantém URLs, query e corpos.

Cobertura: o Network só registra o que aconteceu com o painel aberto. Ausência
na lista não prova que a requisição não existiu antes.

## REA CLI opcional

REA 6.7.0 (morluto/rea, MIT) lê páginas por CDP sem clicar nem executar código.
Use só se o usuário quiser, avulso e local:

- Sempre `npx -y rea-agents@6.7.0 <comando>`, versão presa. O `npx` baixa o
  pacote e grava no cache do npm — aceitar isso é decisão do usuário. Nunca
  `setup`, nunca registro de MCP, nenhum comando além dos listados aqui.
- Saída sempre para `/tmp/<tarefa>/`, nunca para o terminal colado numa
  conversa nem para a árvore do repositório.

```bash
npx -y rea-agents@6.7.0 list-browser-targets http://127.0.0.1:9222 \
  --allowed-origins https://hasson.novajus.com.br --json > /tmp/<tarefa>/alvos.json
npx -y rea-agents@6.7.0 inspect-web-page http://127.0.0.1:9222 <TARGET_ID> \
  --observation-ms 1000 --json > /tmp/<tarefa>/pagina.json
npx -y rea-agents@6.7.0 observe-web-session http://127.0.0.1:9222 <TARGET_ID> \
  --observation-ms 15000 --json > /tmp/<tarefa>/sessao.json
```

O que fica e o que não fica, segundo a documentação da 6.7.0:

- **Fica**: a URL completa de cada requisição e navegação, com query e
  fragmento (só usuário e senha embutidos na URL saem) — portanto o CNJ do
  `?Search=`, o id da pasta e o `term=` do lookup de usuários. A lista de alvos
  traz URL e título de cada aba do filtro. Método, status, MIME, tamanho,
  iniciador e redirects.
- **Não fica**: texto do DOM e **valores de atributo** — a captura traz nome do
  nó, nomes de atributo e tamanho de valor, então não responde "qual é o `id`
  do campo"; para isso, o Elements. Cookies e `Authorization` nunca; cabeçalhos
  só numa projeção mínima; corpos não são lidos por padrão.
- `--include-json-body-shapes` dá a forma de corpos JSON (caminhos e tipos, sem
  valores). Não cobre POST de formulário (`x-www-form-urlencoded`): para os
  nomes dos campos do Salvar, o Payload do DevTools.
- `inspect-web-page` só vê o que acontece depois de anexar
  (`prior_activity_available` é sempre `false`); a navegação do Salvar se
  acompanha melhor com `observe-web-session` (redirects, navegações, ciclo de
  vida), com o usuário clicando dentro da janela.
- Não use contra o Legal One: `capture-browser-scenario` (o agente age e, em
  modo connect, navega a aba para `start_url`, o que pode apagar o formulário),
  `capture-web-screenshot` (pixels com dado de cliente),
  `--include-accessibility-text`, `--include-console-text`,
  `--include-script-sources` e `--include-storage-keys`, salvo pergunta que
  exija e ok do usuário.
- HAR já exportado se lê offline com
  `npx -y rea-agents@6.7.0 inspect-web-network-capture /tmp/<tarefa>/sessao.har har --json`;
  o JSON salvo vai para `inspect-analysis-view` com a view `api-surface`, que
  agrupa por método e modelo de caminho sem os valores da query — o registro de
  origem continua com as URLs exatas. `--sensitive-value` exclui campos com um
  literal declarado, mas põe o literal na linha de comando e no histórico do
  shell.

Resultado do REA é evidência como qualquer outra: cite o arquivo e o comando,
preserve as limitações e lacunas que ele reporta e não trate ausência como
prova.
