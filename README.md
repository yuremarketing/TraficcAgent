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

Esqueleto do agente que vai alimentar o dashboard com dados reais (issues #6, #7, #8, #9, #10, #11).

```bash
cp .env.example .env   # preencha com suas chaves
docker compose up
```

Estrutura:

```text
src/
├── garimpo/    # busca e filtragem de produtos no Mercado Livre
├── conteudo/   # gerador de reviews SEO (RAG 90/10)
└── anuncios/   # conector GAQL e automação Google Ads
```
