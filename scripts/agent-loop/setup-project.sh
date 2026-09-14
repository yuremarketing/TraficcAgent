#!/usr/bin/env bash
#
# Cria (uma vez só) o quadro Kanban no GitHub Projects usado pelo run.sh.
# Roda local, com `gh` autenticado e permissão para criar Projects na conta/org dona do repo.
#
# Uso:
#   REPO=yuremarketing/TraficcAgent ./scripts/agent-loop/setup-project.sh
#
# Ao final, ele imprime o PROJECT_NUMBER a colocar em AGENT_LOOP_PROJECT_NUMBER no .env:
#   AGENT_LOOP_PROJECT_NUMBER=<n>

set -uo pipefail

REPO="${REPO:-yuremarketing/TraficcAgent}"
OWNER="${REPO%%/*}"
TITLE="${TITLE:-Agent Loop — Claude + Gemini}"

command -v gh >/dev/null 2>&1 || { echo "Erro: 'gh' (GitHub CLI) não encontrado no PATH." >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Erro: 'jq' não encontrado no PATH." >&2; exit 1; }

echo "Criando GitHub Project '$TITLE' para $OWNER..."
CREATE_OUT="$(gh project create --owner "$OWNER" --title "$TITLE" --format json)" || {
  echo "Falha ao criar o Project. Verifique se 'gh auth status' tem o escopo 'project'." >&2
  exit 1
}

PROJECT_NUMBER="$(echo "$CREATE_OUT" | jq -r '.number')"
echo "Project criado: #$PROJECT_NUMBER"

echo "Garantindo label 'agent-loop' no repo $REPO..."
gh label create agent-loop -R "$REPO" --color 8B5CF6 \
  --description "Criado pelo agent-loop (Claude + Gemini)" 2>/dev/null || true

echo "Campos padrão do board (Status: Todo / In Progress / Done):"
gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json | jq -r '.fields[] | select(.name=="Status") | .options[].name'

echo ""
echo "Tudo pronto. Adicione no .env:"
echo ""
echo "  AGENT_LOOP_REPO=$REPO"
echo "  AGENT_LOOP_PROJECT_NUMBER=$PROJECT_NUMBER"
echo ""
echo "Board: https://github.com/orgs/$OWNER/projects/$PROJECT_NUMBER (ou https://github.com/users/$OWNER/projects/$PROJECT_NUMBER se for conta pessoal)"
