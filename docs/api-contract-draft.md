# Contrato de APIs — rascunho MVD

Status: proposta para revisão do Yure e validação conjunta

## Regras comuns

- Rotas privadas exigem `Authorization: Bearer <token>`.
- O backend deriva `user_id` e `tenant_id` da sessão; nunca aceita esses campos do cliente.
- Listagem, busca, edição, exclusão e exportação filtram pelo tenant do usuário.
- Respostas de recurso inexistente e recurso de outro tenant usam `404`.
- Valores financeiros usam número decimal em reais; percentuais são números.

## Entidades e relações

```text
Produto 1 ── N LinkAfiliado
Site 1 ── N Produto
Site 1 ── N Review
Review 1 ── N Campanha
Campanha 1 ── N Metrica
```

Todas as entidades persistidas possuem `id`, `tenant_id`, `created_at` e `updated_at`.

## Endpoints propostos

- `GET/POST /api/sites`
- `GET/PATCH/DELETE /api/sites/{id}`
- `GET/POST /api/produtos`
- `GET/PATCH/DELETE /api/produtos/{id}`
- `GET/POST /api/links`
- `GET/PATCH/DELETE /api/links/{id}`
- `GET/POST /api/reviews`
- `GET/PATCH/DELETE /api/reviews/{id}`
- `GET/POST /api/campanhas`
- `GET/PATCH/DELETE /api/campanhas/{id}`
- `GET/POST /api/campanhas/{id}/metricas`
- `GET /api/exportacao`

## Campanha e métricas

Campos mínimos: `site_id`, `produto_id`, `review_id`, `nome`, `status`, `orcamento`,
`cliques`, `conversoes`, `receita`, `custo`, `cpc`, `cpa`, `roi`.

Fórmulas:

- `cpc = custo / cliques`, quando cliques > 0;
- `cpa = custo / conversoes`, quando conversões > 0;
- `roi = (receita - custo) / custo * 100`, quando custo > 0.

## Critérios de aceite do contrato

- [ ] Yure aprova entidades e relacionamentos.
- [ ] Yure aprova papéis, tenant e autorização.
- [ ] Migrations refletem este contrato.
- [ ] Cada endpoint possui teste de posse e acesso cruzado.
- [ ] Frontend usa os mesmos nomes e formatos.
- [ ] Mock e API real retornam o mesmo formato.
