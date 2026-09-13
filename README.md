# TraficcAgent MVD

Mínimo viável distribuível, executado como aplicação HTML estática para gerenciar a fábrica de sites afiliados.

## Executar

Abra `dist/index.html` em qualquer navegador. Não exige instalação ou servidor.

## Fluxo demonstrável

`Criar site → definir nicho e dev → organizar produção → revisar conteúdo → gerenciar links → acompanhar publicação`

## Telas incluídas

- Dashboard operacional.
- Meus sites, com busca e status.
- Calendário de produção.
- Links afiliados.
- Pautas e reviews.
- Fila de aprovação.
- Equipe e permissões.
- Configurações do modelo 90–10.
- Organograma vertical da operação.

Os dados ainda são demonstrativos e ficam em memória do navegador. Banco de dados, autenticação e integrações reais ficam para a próxima fase.

## Backend (em construção)

Agente que vai alimentar o dashboard com dados reais (issues #6, #7, #8, #9, #10, #11).
A lógica de negócio das issues #8, #9 e #11 já está implementada e testada; as
integrações externas (#6, #7, #10) rodam em modo mock até as credenciais reais
chegarem via `.env`.

```bash
cp .env.example .env   # preencha com suas chaves
pip install -r requirements.txt
pytest                 # roda os testes de lógica de negócio
python -m traficcagent # smoke test: mostra o que está em modo real vs mock
docker compose up      # sobe o app + Postgres via Docker
```

Estrutura:

```text
traficcagent/
├── config.py              # settings lidas do ambiente + regras de negócio
├── core/
│   ├── financial_engine.py  # filtro de comissão (#8)
│   ├── traffic_manager.py   # Early Stop / maturação (#9)
│   └── seo_pivot.py         # gatilho de pivô para SEO orgânico (#11)
├── integrations/
│   ├── google_ads.py         # cliente Google Ads MCP (#6)
│   └── affiliate_bot.py      # cliente da API do Bot do Afiliado (#7)
└── content/
    └── rag_engine.py         # motor RAG 90/10 + Schema.org (#10)
```
