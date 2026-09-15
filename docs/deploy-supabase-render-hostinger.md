# Configuração #35 → #36 → #37

Este fluxo separa o banco, a API e a publicação do frontend:

1. **Supabase (#35)**: crie um projeto PostgreSQL e use a URI de conexão no `DATABASE_URL` do Render. O backend já inicializa as tabelas ao subir. A URI e chaves nunca entram no Git.
2. **Render (#36)**: crie o serviço a partir de `render.yaml`. Configure `DATABASE_URL`, `CORS_ORIGINS` e, quando necessário, as credenciais das integrações. O health check é `GET /healthz`.
3. **Hostinger/domínio (#37)**: publique somente os arquivos estáticos de `dist/`. Antes do upload, altere `dist/runtime-config.js` para a URL pública da API Render, por exemplo `https://api.seu-dominio.tld`.

## Variáveis obrigatórias

No Render:

- `DATABASE_URL`: conexão PostgreSQL do Supabase;
- `CORS_ORIGINS`: origem HTTPS exata do frontend Hostinger, sem barra final;
- credenciais de Google Ads, Bot Afiliado e Anthropic apenas se forem usadas.

No frontend:

- `dist/runtime-config.js` contém somente `API_BASE_URL` público;
- não publique `.env`, tokens, chaves privadas ou a service role key do Supabase.

## DNS e validação

Configure no provedor DNS o domínio/subdomínio indicado pelo Render e aguarde o certificado HTTPS. Depois valide:

```text
GET https://api.seu-dominio.tld/healthz
GET https://api.seu-dominio.tld/api/status
```

Abra o frontend pelo domínio Hostinger, faça login e confirme que `/api/context`, os filtros de dimensão/ambiente e os eventos de auditoria usam a API remota. Sem domínio, credenciais e projeto Supabase fornecidos, esta etapa fica preparada, mas não é considerada deploy concluído.
