#!/usr/bin/env bash
#
# Loop de turnos entre Claude e Gemini — SEM abrir processo/sessão nova
# pra nenhum dos dois. Este script é só o "gerente" do pipeline: confere
# o git, decide de quem é a vez, cria/atualiza a Issue no GitHub, mexe no
# Kanban e aplica as regras de parada. Quem "pensa" cada turno é sempre
# um chat já aberto e humano-supervisionado — a sua conversa com o Claude
# Code e a sua sessão interativa do Gemini.
#
# A cada turno, o script IMPRIME o prompt daquele turno e PARA, esperando
# você colar a resposta (numa linha sozinha, digite FIM pra terminar):
#   - Turno do Claude → você leva o prompt pra sua conversa com o Claude
#     Code, ele faz o trabalho de verdade (edita/commita arquivos aqui no
#     repo) e você cola a resposta dele de volta aqui.
#   - Turno do Gemini → mesma coisa, só que na sua sessão do Gemini já
#     aberta.
# Isso exige um terminal interativo de verdade (você rodando à mão) — não
# dá pra disparar isso em background sem ninguém pra colar as respostas.
#
# Se você não passar TASK nem ISSUE_NUMBER, o script primeiro confere se
# houve mudança no git desde a última vez que rodou (na sua branch ou na
# de outra pessoa, ex: dev/philipy). Se houve, Claude e Gemini DEBATEM
# entre si qual deve ser a próxima tarefa (um propõe, o outro critica ou
# concorda, alternando turnos) antes de decidir e só então implementar.
# Se você já sabe a tarefa, pode continuar passando TASK="..." direto e
# o debate é pulado.
#
# Pré-requisitos (na máquina onde você roda este script):
#   - `gh` CLI instalado e autenticado (`gh auth login`) com acesso ao repo
#   - `jq` instalado (só necessário se usar o Kanban)
#
# Configuração estrutural (persistente) fica no .env do projeto, prefixada
# com AGENT_LOOP_ — veja .env.example. Este script dá `source .env`
# automaticamente. TASK/ISSUE_NUMBER são passados na hora de rodar, pois
# mudam a cada execução:
#
#   ./scripts/agent-loop/run.sh                       # detecta mudança no git e debate a tarefa
#   TASK="Implementar X" ./scripts/agent-loop/run.sh  # tarefa já definida, pula o debate
#   ISSUE_NUMBER=42 ./scripts/agent-loop/run.sh       # retoma um issue existente, pula o debate
#
# Ver todas as variáveis em scripts/agent-loop/README.md.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT" || exit 1

# ---------- Carrega configuração estrutural do .env ----------
if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

# ---------- Config (env do .env com prefixo AGENT_LOOP_, ou sobrescrita ad-hoc) ----------
REPO="${AGENT_LOOP_REPO:-yuremarketing/TraficcAgent}"
OWNER="${REPO%%/*}"
TASK="${TASK:-}"
ISSUE_NUMBER="${ISSUE_NUMBER:-}"
MAX_TURNS="${AGENT_LOOP_MAX_TURNS:-20}"
FIRST_AGENT="${AGENT_LOOP_FIRST_AGENT:-gemini}"          # gemini | claude
PROJECT_NUMBER="${AGENT_LOOP_PROJECT_NUMBER:-}"           # número do GitHub Project (kanban); vazio = sem sync de kanban
POST_TO_ISSUE="${AGENT_LOOP_POST_TO_ISSUE:-1}"            # 1 = comenta cada turno no issue
AUTO_PUSH="${AGENT_LOOP_AUTO_PUSH:-0}"                    # 1 = dá git push após cada commit de cada agente
WATCH_BRANCHES="${AGENT_LOOP_WATCH_BRANCHES:-master dev/philipy}"  # branches observadas pra detectar mudança
DEBATE_MAX_TURNS="${AGENT_LOOP_DEBATE_MAX_TURNS:-6}"      # teto de turnos do debate "qual a próxima tarefa"
LOG_DIR="${LOG_DIR:-$REPO_ROOT/logs/agent-loop}"
# ----------------------------------------------------------------------

command -v gh >/dev/null 2>&1 || { echo "Erro: 'gh' (GitHub CLI) não encontrado no PATH." >&2; exit 1; }
[ -t 0 ] || { echo "Erro: este script precisa de um terminal interativo (é você quem cola as respostas de cada turno)." >&2; exit 1; }

mkdir -p "$LOG_DIR"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TRANSCRIPT="$LOG_DIR/loop-${TIMESTAMP}.md"

log() { printf '%s\n' "$*" | tee -a "$TRANSCRIPT"; }

# ---------- Repassa o turno pra um humano: imprime o prompt e espera a resposta ----------
# Não abre processo nem sessão nova. Mostra o prompt (e grava no transcript),
# e lê da entrada padrão até uma linha contendo só "FIM" — é você quem leva
# o prompt pro chat certo (Claude ou Gemini) e cola a resposta de volta aqui.
run_agent() {
  local speaker="$1" prompt="$2"
  local destino="sua conversa com o Claude Code"
  [ "$speaker" = "gemini" ] && destino="sua sessão do Gemini"

  {
    echo ""
    echo "=== Prompt para ${speaker^^} ==="
    echo "$prompt"
    echo "=== Fim do prompt ==="
  } >> "$TRANSCRIPT"

  {
    echo ""
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo "Turno do ${speaker^^} — leve o texto abaixo para ${destino}:"
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo "$prompt"
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo "Cole abaixo a resposta d${speaker:+o} ${speaker^^}. Numa linha sozinha, digite FIM pra terminar:"
  } >&2

  local line acc=""
  while IFS= read -r line; do
    [ "$line" = "FIM" ] && break
    acc="${acc}${line}
"
  done
  printf '%s' "$acc"
}

# ---------- Monta o prompt de cada turno de EXECUÇÃO (issue já definido) ----------
build_prompt() {
  local speaker="$1" other="$2" turn="$3"
  local tail
  tail="$(tail -c 12000 "$TRANSCRIPT" 2>/dev/null || true)"
  cat <<PROMPT
Você é ${speaker^^}, trabalhando em par com ${other^^} para resolver o issue
#${ISSUE_NUMBER} do repositório ${REPO}: "${TASK}".

Vocês dois têm acesso direto ao código deste repositório (diretório atual)
e podem editar arquivos, rodar comandos e criar commits. Trabalhem em turnos:
leia o que ${other^^} disse/fez no turno anterior (transcrição abaixo) e dê o
próximo passo real — analise, implemente, corrija, ou responda a uma pergunta
que ${other^^} tenha feito. Não repita o que já foi dito.

Regras:
- Se você alterar arquivos, rode \`git add\` e \`git commit -m "..."\` com uma
  mensagem clara antes de terminar sua resposta.
- Seja direto e objetivo — isto é um diálogo entre dois agentes, não um relatório.
- Quando achar que a tarefa do issue #${ISSUE_NUMBER} está completamente
  resolvida (código funcionando e commitado), termine sua resposta com a
  linha exata: STATUS: DONE
  Caso contrário, termine com: STATUS: CONTINUE

--- Transcrição até agora (turno ${turn}) ---
${tail:-"(este é o primeiro turno — não há histórico ainda)"}
--- Fim da transcrição ---

Sua vez, ${speaker^^}:
PROMPT
}

# ---------- Detecta mudança no git desde a última vez que o loop rodou ----------
# Observa cada branch em WATCH_BRANCHES (local ou origin/) e compara com o
# último SHA visto, guardado em logs/agent-loop/.state/ (fora do git).
STATE_DIR="$LOG_DIR/.state"
mkdir -p "$STATE_DIR"

git fetch origin --quiet 2>/dev/null || true

GIT_CHANGED=0
CHANGE_SUMMARY=""

for br in $WATCH_BRANCHES; do
  cur="$(git rev-parse "origin/$br" 2>/dev/null || git rev-parse "$br" 2>/dev/null || echo "")"
  [ -z "$cur" ] && continue
  state_file="$STATE_DIR/${br//\//_}.sha"
  prev="$(cat "$state_file" 2>/dev/null || echo "")"
  if [ "$cur" != "$prev" ]; then
    GIT_CHANGED=1
    if [ -n "$prev" ]; then
      CHANGE_SUMMARY="$CHANGE_SUMMARY

Novidades em $br:
$(git log --oneline "$prev..$cur" 2>/dev/null || echo "(não consegui comparar — histórico pode ter mudado)")"
    else
      CHANGE_SUMMARY="$CHANGE_SUMMARY

$br está em $(git log -1 --oneline "$cur" 2>/dev/null) (primeira vez observando esta branch, sem histórico anterior)."
    fi
  fi
  echo "$cur" > "$state_file"
done

# ---------- Debate: quando não há TASK/ISSUE explícitos, os agentes decidem juntos ----------
build_debate_prompt() {
  local speaker="$1" other="$2" turn="$3"
  local tail
  tail="$(tail -c 8000 "$DEBATE_TRANSCRIPT" 2>/dev/null || true)"
  cat <<PROMPT
Você é ${speaker^^}, debatendo com ${other^^} qual deve ser a PRÓXIMA tarefa
de desenvolvimento no repositório ${REPO}. Vocês ainda NÃO vão implementar
nada agora — só decidir, os dois de acordo, o que fazer a seguir.

O que mudou no git desde a última vez que este loop rodou:
${CHANGE_SUMMARY:-"(nenhuma mudança detectada — primeira rodada ou nada novo desde a última vez)"}

Se ainda ninguém propôs nada nesta rodada (veja a transcrição abaixo): proponha
UMA tarefa concreta e específica, com raciocínio breve de por que ela é
prioridade agora — considere as mudanças acima, o backlog de issues do
repositório e o estado atual do código. Termine com:
TASK: <descrição de uma linha da tarefa proposta>
STATUS: PROPOSAL

Se ${other^^} já propôs algo (veja a transcrição abaixo):
- Concordando com a proposta dele, termine com:
  TASK: <repita a mesma tarefa proposta por ${other^^}>
  STATUS: AGREE
- Discordando ou querendo ajustar, explique objetivamente por quê e proponha
  o ajuste, terminando com:
  TASK: <sua proposta ajustada>
  STATUS: COUNTER

Seja direto — isto é uma decisão rápida entre dois agentes, não um relatório.

--- Debate até agora (turno ${turn}) ---
${tail:-"(primeiro turno do debate)"}
--- Fim ---

Sua vez, ${speaker^^}:
PROMPT
}

debate_and_pick_task() {
  DEBATE_TRANSCRIPT="$LOG_DIR/debate-${TIMESTAMP}.md"
  local dturn=1 dspeaker="$FIRST_AGENT" dother="" agreed_task="" prompt="" output="" task_line=""

  log "# Debate — qual deve ser a próxima tarefa?"
  log "$CHANGE_SUMMARY"
  log ""

  while [ "$dturn" -le "$DEBATE_MAX_TURNS" ]; do
    dother="claude"; [ "$dspeaker" = "claude" ] && dother="gemini"

    log "----------------------------------------------------------------"
    log "### Debate turno $dturn — ${dspeaker^}"
    log "----------------------------------------------------------------"

    prompt="$(build_debate_prompt "$dspeaker" "$dother" "$dturn")"
    output="$(run_agent "$dspeaker" "$prompt")"
    printf '%s\n' "$output" >> "$DEBATE_TRANSCRIPT"
    log "$output"
    log ""

    task_line="$(printf '%s\n' "$output" | grep -m1 '^TASK:' | sed 's/^TASK:[[:space:]]*//')"
    [ -n "$task_line" ] && agreed_task="$task_line"

    if printf '%s\n' "$output" | grep -q "STATUS: AGREE"; then
      TASK="$agreed_task"
      log "Debate concluído: acordo no turno $dturn — tarefa escolhida: $TASK"
      return 0
    fi

    dspeaker="$dother"
    dturn=$((dturn + 1))
  done

  if [ -n "$agreed_task" ]; then
    TASK="$agreed_task"
    log "Debate encerrado sem AGREE explícito após $DEBATE_MAX_TURNS turnos — seguindo com a última proposta: $TASK"
  else
    echo "Erro: o debate terminou sem nenhum agente propor uma linha TASK: — não dá pra continuar." >&2
    exit 1
  fi
}

if [ -z "$TASK" ] && [ -z "$ISSUE_NUMBER" ]; then
  if [ "$GIT_CHANGED" = "1" ]; then
    debate_and_pick_task
  else
    echo "Erro: nada novo no git desde a última rodada, e nenhuma TASK definida." >&2
    echo "Rode com TASK=\"...\" ou ISSUE_NUMBER=<n>, ou espere alguma mudança em: $WATCH_BRANCHES" >&2
    exit 1
  fi
fi

# ---------- Garante que existe um Issue para trabalhar ----------
if [ -z "$ISSUE_NUMBER" ]; then
  echo "Criando issue no repo $REPO..."
  ISSUE_URL="$(gh issue create -R "$REPO" \
    --title "$TASK" \
    --body "Tarefa aberta automaticamente pelo agent-loop (Claude + Gemini) em ${TIMESTAMP}.

## Objetivo
$TASK

## Como este issue vai evoluir
Claude e Gemini vão trabalhar em turnos, alternando propostas e implementação,
e vão comentar aqui a cada turno até a tarefa ser concluída." 2>&1)" || { echo "Falha ao criar issue: $ISSUE_URL" >&2; exit 1; }
  ISSUE_NUMBER="$(basename "$ISSUE_URL")"
  echo "Issue criado: $ISSUE_URL (#$ISSUE_NUMBER)"
  gh issue edit "$ISSUE_NUMBER" -R "$REPO" --add-label "agent-loop" >/dev/null 2>&1 || true
else
  TASK="$(gh issue view "$ISSUE_NUMBER" -R "$REPO" --json title -q .title 2>/dev/null || echo "Issue #$ISSUE_NUMBER")"
fi

# ---------- Kanban (GitHub Projects v2) ----------
PROJECT_ITEM_ID=""
STATUS_FIELD_ID=""
STATUS_OPT_TODO=""
STATUS_OPT_PROGRESS=""
STATUS_OPT_DONE=""

kanban_enabled() { [ -n "$PROJECT_NUMBER" ]; }

kanban_setup() {
  kanban_enabled || return 0
  local fields item_id
  fields="$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json 2>/dev/null)" || {
    echo "Aviso: não consegui ler os campos do Project #$PROJECT_NUMBER — kanban desativado nesta execução." >&2
    PROJECT_NUMBER=""
    return 0
  }
  STATUS_FIELD_ID="$(echo "$fields" | jq -r '.fields[] | select(.name=="Status") | .id')"
  STATUS_OPT_TODO="$(echo "$fields" | jq -r '.fields[] | select(.name=="Status") | .options[] | select(.name|test("Todo|To Do";"i")) | .id' | head -1)"
  STATUS_OPT_PROGRESS="$(echo "$fields" | jq -r '.fields[] | select(.name=="Status") | .options[] | select(.name|test("In Progress";"i")) | .id' | head -1)"
  STATUS_OPT_DONE="$(echo "$fields" | jq -r '.fields[] | select(.name=="Status") | .options[] | select(.name|test("Done";"i")) | .id' | head -1)"

  item_id="$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" \
    --url "https://github.com/$REPO/issues/$ISSUE_NUMBER" --format json 2>/dev/null | jq -r '.id')"
  PROJECT_ITEM_ID="$item_id"
}

kanban_set_status() {
  kanban_enabled || return 0
  local option_id="$1"
  [ -n "$PROJECT_ITEM_ID" ] && [ -n "$STATUS_FIELD_ID" ] && [ -n "$option_id" ] || return 0
  gh project item-edit --id "$PROJECT_ITEM_ID" --project-id "$PROJECT_NUMBER" \
    --field-id "$STATUS_FIELD_ID" --single-select-option-id "$option_id" >/dev/null 2>&1 || true
}

kanban_setup
kanban_set_status "$STATUS_OPT_PROGRESS"

post_turn_to_issue() {
  local turn="$1" speaker="$2" body="$3"
  [ "$POST_TO_ISSUE" = "1" ] || return 0
  gh issue comment "$ISSUE_NUMBER" -R "$REPO" -b "**Turno ${turn} — ${speaker^}**

${body}" >/dev/null 2>&1 || true
}

# ---------- Loop principal (execução) ----------
log "# Agent Loop — Claude + Gemini"
log ""
log "Repo: $REPO · Issue: #$ISSUE_NUMBER · Tarefa: $TASK"
log "Início: $(date -Iseconds)"
log ""

speaker="$FIRST_AGENT"
done_flag=0
turn=1

while [ "$turn" -le "$MAX_TURNS" ]; do
  other="claude"; [ "$speaker" = "claude" ] && other="gemini"

  log "----------------------------------------------------------------"
  log "### Turno $turn — ${speaker^}"
  log "----------------------------------------------------------------"

  prompt="$(build_prompt "$speaker" "$other" "$turn")"
  output="$(run_agent "$speaker" "$prompt")"

  log "$output"
  log ""

  post_turn_to_issue "$turn" "$speaker" "$output"

  if [ "$AUTO_PUSH" = "1" ]; then
    git -C "$REPO_ROOT" push 2>&1 | tee -a "$TRANSCRIPT" >/dev/null || true
  fi

  if echo "$output" | grep -q "STATUS: DONE"; then
    done_flag=1
    break
  fi

  speaker="$other"
  turn=$((turn + 1))
done

log "----------------------------------------------------------------"
if [ "$done_flag" = "1" ]; then
  log "Loop concluído: ${speaker^} sinalizou STATUS: DONE no turno $turn."
  kanban_set_status "$STATUS_OPT_DONE"
  if [ "$POST_TO_ISSUE" = "1" ]; then
    gh issue close "$ISSUE_NUMBER" -R "$REPO" -c "Loop Claude + Gemini concluiu a tarefa (ver transcrição completa em $TRANSCRIPT)." >/dev/null 2>&1 || true
  fi
else
  log "Loop encerrado sem STATUS: DONE após $MAX_TURNS turnos. Revise a transcrição e rode de novo com ISSUE_NUMBER=$ISSUE_NUMBER se precisar continuar."
fi
log ""
log "Transcrição completa salva em: $TRANSCRIPT"
