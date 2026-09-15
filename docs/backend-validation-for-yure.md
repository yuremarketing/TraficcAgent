# Pacote de validação backend para revisão do Yure

Data: 14/09/2026

## #27 — Matriz de Auth

| Perfil | Sites próprios | WorkItems próprios | Dados de outro usuário | Produção/credenciais |
|---|---|---|---|---|
| Tester | leitura e teste local | criar/alterar mock | negar | negar |
| Philipy | operar distribuição | registrar validação | negar | negar |
| Yure | operar arquitetura | revisar backend | negar por padrão | revisar/aprovar |

Regras esperadas:

- Sem token: `401`;
- Token inválido/expirado: `401`;
- Recurso de outro usuário/tenant: `404`;
- `user_id` e `tenant_id` derivados da sessão;
- Nenhuma permissão pode depender apenas da interface.

## #28 — Anti-IDOR

- Criar recurso com Philipy;
- Listar com Yure e confirmar ausência;
- Buscar por ID com Yure e confirmar `404`;
- Alterar por ID com Yure e confirmar `404`;
- Excluir/exportar recurso de outro usuário e confirmar negação;
- Repetir para links, reviews, campanhas e métricas quando os endpoints existirem.

Evidência atual: sites e WorkItems possuem filtros por usuário; testes de Auth/ownership passam.

## #7 — Mocks

- Bot do Afiliado sem API key: metadados e links mockados;
- Lotes de 1, 10, 150 e 151 URLs;
- Resposta inválida e falha transitória cobertas;
- Google Ads sem credenciais: campanhas e métricas mockadas;
- Transporte fake usado para testar o caminho real sem rede.

## #16/#22 — Contrato e ambiente

- Contrato de APIs: `docs/api-contract-draft.md`;
- Healthcheck: `GET /healthz`;
- Compose: app + PostgreSQL;
- `.env.example` sem segredos reais;
- Rollback: `docs/production-readiness-checklist.md`;
- CI: `.github/workflows/pytest.yml`.

## #24/#31 — Segurança e aprovação

- [x] Testes automatizados locais;
- [x] Secrets fora do Git;
- [x] Mock sem credenciais;
- [x] Anti-IDOR inicial;
- [ ] Tenant e permissões finais aprovados;
- [ ] E2E visual e rollback em ambiente de deploy;
- [ ] Aprovação do Yure e de ambos os sócios.

## Resultado

Este documento é material de preparação e revisão. Não substitui aprovação arquitetural,
credenciais, revisão de segurança, PR, merge ou validação de produção.
