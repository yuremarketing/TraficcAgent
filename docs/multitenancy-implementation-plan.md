# Plano de implementação — Core administrativo e tenants por domínio

Status: modelo definido por Philipy; implementação incremental em andamento

## Objetivo

O sistema administrativo é o Core central. Cada site publicado, identificado por
seu domínio, representa um tenant isolado, com usuários, papéis, dados e métricas
próprios. O domínio será uma identidade única do tenant no backend; nunca será
aceito apenas como filtro confiado pelo frontend.

## Modelo proposto

```text
Core administrativo
  └── tenants por site/domínio
        ├── membros (Usuario + papel)
        ├── site/configuração
        ├── produtos
        ├── links afiliados
        ├── reviews
        ├── campanhas
        └── métricas/eventos
```

- `tenants`: id, domínio canônico, nome, slug, nicho, status, timestamps;
- `tenant_members`: tenant_id, user_id, role, status, timestamps;
- O registro de site do Core é a origem do tenant e recebe `tenant_id`/domínio canônico;
- Todas as demais entidades de negócio recebem `tenant_id` obrigatório;
- `user_id` permanece como criador/responsável quando necessário;
- Um usuário pode participar de vários tenants;
- O tenant ativo vem da sessão/contexto autorizado, nunca de um valor confiado do navegador.

## Papéis iniciais

- `owner`: administração do tenant e decisões estratégicas;
- `operator`: operação, sites, campanhas e métricas;
- `editor`: conteúdo, reviews e links;
- `viewer/tester`: leitura e validação mock, sem produção.

Mapeamento inicial: Yure como owner/operator técnico; Philipy como owner/operator
comercial; Tester como viewer/tester. A aprovação societária continua necessária.

## Fases

1. Criar o tenant automaticamente/controladamente a partir do site e domínio;
2. Criar migrations de tenants e membros.
3. Associar usuários existentes a um tenant padrão de migração.
4. Adicionar `tenant_id` às entidades e criar índices/constraints.
5. Atualizar Auth para resolver tenant ativo e papel.
6. Aplicar filtro de tenant em toda listagem, busca, edição, exclusão e exportação.
7. Criar testes negativos entre usuários e tenants.
8. Conectar o frontend ao tenant ativo sem confiar em permissões visuais.
9. Executar migração, backup, rollback e teste E2E.

## Gates e riscos

- Não executar migration destrutiva sem backup e plano de rollback.
- Não liberar produção com `tenant_id` opcional.
- Não aceitar `tenant_id`, role ou ownership diretamente do cliente.
- Confirmar compatibilidade com dados atuais de sites e WorkItems.
- Yure aprova arquitetura, migrations, Auth, permissões e deploy.
- Philipy valida fluxo manual, dados simulados, UX e evidências.

## Critérios de aceite

- [ ] Dois tenants podem existir simultaneamente.
- [ ] Cada domínio pertence a um único tenant e não pode ser duplicado.
- [ ] Usuário de um tenant não lista, busca, altera, exclui ou exporta dados de outro.
- [ ] Usuário pode trocar apenas para tenants dos quais é membro.
- [ ] Papéis são validados no backend.
- [ ] Links, reviews, campanhas e métricas possuem `tenant_id`.
- [ ] Testes de acesso cruzado passam.
- [ ] Backup/rollback documentados e testados.
- [ ] Frontend e API usam o mesmo tenant ativo.
- [ ] Yure aprova o desenho e ambos aprovam a liberação.
