# Agent Loop — Claude + Gemini

Faz o Claude e o Gemini trabalharem juntos, em turnos, **sem abrir processo
ou sessão nova pra nenhum dos dois**. O script é só o "gerente" do pipeline:
confere o git, decide de quem é a vez, cria/atualiza uma Issue + quadro
Kanban (GitHub Projects) no repo `yuremarketing/TraficcAgent`, e aplica as
regras de parada. Quem "pensa" cada turno é sempre um chat de verdade,
já aberto, com um humano supervisionando — a sua conversa com o Claude Code
e a sua sessão interativa do Gemini.

Como funciona:

1. Você roda `run.sh` — com uma tarefa (texto livre), um issue já existente,
   ou **sem nada**: nesse caso o script confere sozinho se houve mudança no
   git (na sua branch ou na de outra pessoa, ex: `dev/philipy`) desde a
   última vez que rodou.
2. Se houve mudança e nenhuma tarefa foi passada, entra um **debate** antes
   de qualquer código ser tocado: Gemini e Claude se alternam propondo e
   criticando qual deve ser a próxima tarefa (`STATUS: PROPOSAL` /
   `STATUS: COUNTER` / `STATUS: AGREE`), até os dois concordarem — só então
   a tarefa vira Issue e a execução começa. Se você já passou `TASK=`, o
   debate é pulado e vai direto pra execução.
3. **A cada turno** (de debate ou de execução), o script imprime o prompt
   daquele turno e **para**, esperando você colar a resposta:
   - Turno do Claude → você leva o prompt pra sua conversa com o Claude
     Code (ele edita/commita arquivos de verdade neste repo), e cola a
     resposta dele de volta no terminal.
   - Turno do Gemini → mesma coisa, na sua sessão do Gemini já aberta.
   - Termine a colagem com uma linha sozinha contendo `FIM`.
4. Cada turno fica registrado no transcript local e (opcionalmente) é
   postado como comentário no Issue, pra ficar no histórico do GitHub.
5. O item do Issue se move automaticamente no Kanban: `Todo → In Progress`
   ao começar, `→ Done` quando um dos dois sinalizar `STATUS: DONE`.
6. O loop para quando alguém sinaliza `STATUS: DONE` ou quando atinge
   `MAX_TURNS` (padrão 20).

Por precisar que você cole cada resposta, o script exige um terminal
interativo de verdade — não dá pra disparar isso em background sem ninguém
pra alimentar os turnos.

## Pré-requisitos

- [`gh`](https://cli.github.com) instalado e autenticado (`gh auth login`),
  com escopo `project` se for usar o Kanban (`gh auth refresh -s project`).
- `jq` instalado (só necessário se usar o Kanban).
- Uma conversa aberta com o Claude Code e uma sessão aberta do Gemini —
  são eles que efetivamente fazem o trabalho de cada turno.

## Configuração (`.env`)

A configuração estrutural (persistente) do loop fica no `.env` do projeto,
com prefixo `AGENT_LOOP_` — veja `.env.example` na raiz do repo. `run.sh` dá
`source .env` automaticamente antes de rodar.

| Variável | Padrão | Descrição |
|---|---|---|
| `AGENT_LOOP_REPO` | `yuremarketing/TraficcAgent` | Repositório `owner/name` |
| `AGENT_LOOP_FIRST_AGENT` | `gemini` | Quem começa: `gemini` ou `claude` |
| `AGENT_LOOP_MAX_TURNS` | `20` | Limite de turnos antes de parar (execução) |
| `AGENT_LOOP_WATCH_BRANCHES` | `master dev/philipy` | Branches observadas pra detectar mudança no git (separadas por espaço) |
| `AGENT_LOOP_DEBATE_MAX_TURNS` | `6` | Teto de turnos do debate "qual a próxima tarefa" antes de seguir com a última proposta |
| `AGENT_LOOP_PROJECT_NUMBER` | — | Número do GitHub Project (kanban); vazio desativa o sync |
| `AGENT_LOOP_POST_TO_ISSUE` | `1` | Comentar cada turno no Issue (`0` desativa) |
| `AGENT_LOOP_AUTO_PUSH` | `0` | `1` = dá `git push` depois de cada turno com commit |

`TASK` e `ISSUE_NUMBER` **não** ficam no `.env` — mudam a cada execução, veja
abaixo.

O estado de "o que já foi visto" em cada branch observada fica em
`logs/agent-loop/.state/` (fora do git, local à sua máquina) — é o que
permite ao script saber se há algo novo desde a última rodada.

## Setup do Kanban (uma vez só, opcional)

```bash
./scripts/agent-loop/setup-project.sh
```

Isso cria um GitHub Project novo com as colunas padrão `Todo / In Progress /
Done` e imprime o `PROJECT_NUMBER` a colocar em `AGENT_LOOP_PROJECT_NUMBER`
no `.env`. Se preferir usar um Project já existente, pule este passo e
descubra o número dele em `https://github.com/orgs/<owner>/projects` (ou
`/users/<owner>/projects`).

## Rodando o loop

Deixando os agentes decidirem a tarefa sozinhos (só funciona se algo mudou
no git desde a última rodada — veja `AGENT_LOOP_WATCH_BRANCHES`):

```bash
./scripts/agent-loop/run.sh
```

O script vai parar assim:

```
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Turno do GEMINI — leve o texto abaixo para sua sessão do Gemini:
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Você é GEMINI, debatendo com CLAUDE qual deve ser a PRÓXIMA tarefa...
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Cole abaixo a resposta do GEMINI. Numa linha sozinha, digite FIM pra terminar:
```

Cole o prompt no Gemini, pegue a resposta dele, cole de volta no terminal
seguida de uma linha `FIM`. O script processa, checa `STATUS:`, e já
imprime o próximo turno (agora pedindo pra levar o prompt pro Claude).

Criando uma tarefa nova direto (pula o debate, cria o Issue automaticamente):

```bash
TASK="Ligar o backend Python (traficcagent/) ao dist/index.html via API" \
  ./scripts/agent-loop/run.sh
```

Retomando um Issue já existente (também pula o debate):

```bash
ISSUE_NUMBER=42 ./scripts/agent-loop/run.sh
```

Na execução funciona igual — o script alterna pedindo o prompt pro Claude e
pro Gemini, você cola cada resposta, e ele segue registrando tudo em
`logs/agent-loop/loop-<timestamp>.md` (pasta ignorada pelo git) até alguém
sinalizar `STATUS: DONE`.

## Avisos

- Quem edita e commita arquivos de verdade neste repo é o Claude ou o
  Gemini, no chat correspondente — o script só orquestra o pipeline
  (git, Issue, Kanban, regra de parada). Revise o `git log` / `git diff`
  sempre que quiser antes de confiar no que foi commitado.
- `AGENT_LOOP_AUTO_PUSH=1` empurra commits para o remoto automaticamente
  depois de cada turno — só ative se já confiar no loop rodando sem revisão
  manual antes do push. O default (`0`) deixa o push manual, sob seu controle.
- Precisa de terminal interativo de verdade (o script falha rápido se
  detectar que não tem stdin pra colar as respostas).
