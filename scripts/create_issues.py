import urllib.request
import json
import os

TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "yuremarketing/TraficcAgent"
PROJECT_ID = "PVT_kwHOAEqFx84BjJnG"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
}

graphql_url = "https://api.github.com/graphql"

issues = [
    {"title": "[Setup] Criação do repositório e vinculação com Git remoto", "body": "Tarefa já concluída na Fase 1. Repositório inicializado e vinculado.", "status": "Done"},
    {"title": "[Documentação] Elaboração da Arquitetura e Regras de Negócio (README)", "body": "Tarefa concluída. README gerado com regras de 10% de comissão e Early Stop.", "status": "Done"},
    {"title": "[Documentação] Criação e upload dos Manuais Técnicos e Backlog", "body": "Tarefa concluída. 6 artefatos exportados e comitados na pasta `artefatos/`.", "status": "Done"},
    {"title": "[Infraestrutura] Setup do Quadro Kanban (Project V2) e Colaboradores", "body": "Tarefa concluída. Projeto público gerado e convite enviado para 0xphygames.", "status": "Done"},
    
    {"title": "[Infraestrutura] Setup do Ambiente de Desenvolvimento", "body": "Criar Dockerfile, requirements.txt, configurar variáveis de ambiente e Cloud Run.", "status": "Todo"},
    {"title": "[Integração] Conexão com Google Ads MCP Server", "body": "Implementar e testar a conexão com `googleads/google-ads-mcp` executando queries GAQL para leitura de campanhas.", "status": "Todo"},
    {"title": "[Integração] Integração com a API do Bot do Afiliado", "body": "Autenticação via X-API-Key e extração de metadados e conversão de links rastreáveis.", "status": "Todo"},
    {"title": "[Core] Motor de Decisão Financeira (Filtro de Comissão)", "body": "Implementar lógica: Aceitar produtos com comissão >= 10%. Exceção: Alto ticket com lucro líquido de R$40 a R$50.", "status": "Todo"},
    {"title": "[Core] Robô de Gestão de Tráfego (Early Stop vs Maturação)", "body": "Implementar a trava de 3 dias (cortar gastos se sem ROI) e manter por 14 dias se métricas saudáveis para Smart Bidding.", "status": "Todo"},
    {"title": "[Conteúdo] Motor RAG Híbrido 90/10 e Injeção Schema.org", "body": "Configurar LLM para gerar 90% do conteúdo review e JSON-LD para Review Snippets, aguardando os 10% de toque humano.", "status": "Todo"},
    {"title": "[Core] Gatilho de Pivô Automático para SEO Orgânico", "body": "Desenvolver a regra que desliga campanhas do Google Ads quando o CPC zera a margem e migra os esforços totais para rankear no Google AI Overviews e ChatGPT.", "status": "Todo"}
]

for issue in issues:
    # 1. Create Issue via REST API
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues", data=json.dumps({"title": issue["title"], "body": issue["body"]}).encode(), headers=headers, method="POST")
    try:
        response = urllib.request.urlopen(req)
        resp_data = json.loads(response.read().decode())
        issue_node_id = resp_data["node_id"]
        issue_number = resp_data["number"]
        print(f"Created Issue #{issue_number}: {issue['title']}")
        
        # 2. Add to Project V2 via GraphQL
        gql_payload = {
            "query": f'mutation {{ addProjectV2ItemById(input: {{projectId: "{PROJECT_ID}", contentId: "{issue_node_id}"}}) {{ item {{ id }} }} }}'
        }
        gql_req = urllib.request.Request(graphql_url, data=json.dumps(gql_payload).encode(), headers=headers, method="POST")
        gql_resp = urllib.request.urlopen(gql_req)
        print(f"Added Issue #{issue_number} to Kanban.")
        
    except Exception as e:
        print(f"Error creating issue: {e}")
