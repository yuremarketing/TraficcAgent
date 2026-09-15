# Arquitetura do TraficcAgent

## Decisão estrutural

O TraficcAgent terá um único Core administrativo. Cada site publicado ou
planejado, identificado por um domínio canônico, será um tenant e funcionará
como um agente operacional isolado.

```text
Core administrativo
├── Usuários, papéis e auditoria
├── Cadastro e seleção de tenants/agentes
├── Visão consolidada e exportação
└── Operação por tenant
    ├── Site/domínio
    ├── Produto e nicho
    ├── Links afiliados
    ├── Pautas e reviews
    ├── Campanhas e métricas
    └── Central de operação/histórico
```

## Limites de responsabilidade

- O Core autentica o usuário e resolve o tenant ativo a partir da sessão.
- O backend aplica `tenant_id` em toda leitura, busca, edição, exclusão e
  exportação de dados operacionais.
- O domínio é único e pertence a um único tenant.
- O frontend apenas exibe o tenant autorizado; seleção visual não concede
  acesso.
- Cada ação operacional gera histórico com usuário, tenant, entidade, ação e
  horário.
- O modo manual/mock é o padrão até a aprovação das integrações reais.

## Modelo de dados alvo

```text
usuarios ──< tenant_members >── tenants (domain unique)
                                  │
                                  ├── sites
                                  ├── produtos ──< links
                                  ├── reviews
                                  └── campanhas ──< metricas
```

Todas as entidades filhas possuem `tenant_id`, `created_by` quando aplicável,
timestamps e status controlado pelo backend. Relacionamentos entre entidades
devem confirmar que os registros pertencem ao mesmo tenant.

## Camadas do sistema

1. **API/Auth:** sessão, papéis, tenant ativo e respostas HTTP.
2. **Domínio:** regras de status, associação, métricas, ROI, pausa e escala.
3. **Persistência:** PostgreSQL, migrations, índices por `tenant_id` e
   constraints de domínio/relacionamento.
4. **Integrações:** Bot do Afiliado e Google Ads atrás de interfaces mockáveis.
5. **Frontend Core:** navegação única, telas por ambiente e responsividade.
6. **Auditoria/QA:** histórico, exportação, testes anti-IDOR, E2E e evidências.

## Estrutura de código alvo

```text
traficcagent/
├── api/              # rotas, schemas, autenticação e dependências
├── domain/           # regras de negócio e serviços de operação
├── integrations/     # adapters mock/real
├── repositories/     # acesso persistente por tenant
├── migrations/       # evolução controlada do PostgreSQL
└── db.py             # engine, sessão e bootstrap local
dist/                 # Core frontend e ambientes operacionais
tests/                # unitários, integração, anti-IDOR e E2E
docs/                 # contratos, decisões, runbooks e evidências
```

## Ordem de implementação

1. `Tenant` por domínio e `tenant_members`.
2. Resolução do tenant na sessão e autorização por papel.
3. Migrations e migração compatível dos sites existentes.
4. `tenant_id` em produto, link, review, campanha, métrica e histórico.
5. CRUD e associações com validação de tenant.
6. Frontend Core com seletor de agente autorizado.
7. Testes de isolamento, métricas, exportação e fluxo manual ponta a ponta.
8. Integrações reais somente após aprovação de segurança e produção.

## Critérios de aceite da fundação

- Dois sites/domínios podem operar simultaneamente como tenants distintos.
- Nenhum usuário acessa dados de tenant do qual não é membro.
- Não existe associação entre entidades de tenants diferentes.
- O domínio não pode ser duplicado nem alterado sem regra de governança.
- O Core continua sendo o único ponto administrativo.
- O fluxo manual permanece utilizável sem API key.
- Migrations, rollback, secrets e aprovação de produção estão documentados.
