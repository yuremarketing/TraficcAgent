# Checklist de prontidão — Manual/Mock

Data: 14/09/2026

## Arquitetura e critérios

- [x] API FastAPI local disponível.
- [x] PostgreSQL previsto no Compose.
- [x] Modo mock sem credenciais reais.
- [x] Ownership de sites e WorkItems coberto por testes.
- [ ] Ownership de links, reviews, campanhas e métricas persistidos no backend.
- [ ] Autorização final por papel/tenant aprovada pelo Yure.

## Secrets

- [x] `.env` ignorado pelo Git.
- [x] `.env.example` sem valores reais.
- [x] API keys não incluídas no frontend ou nos testes.
- [ ] Validar secrets no ambiente de deploy.
- [ ] Rotacionar qualquer credencial que tenha sido exposta.

## Rollback

1. Interromper o deploy ou pausar a campanha.
2. Preservar logs, histórico e exportação dos dados.
3. Reverter para o último commit aprovado na `master`.
4. Confirmar `/healthz`, autenticação e isolamento de dados.
5. Comunicar incidente, impacto, responsável e próximo passo.
6. Só reabrir a operação após revisão e teste ponta a ponta.

## Evidência atual

- Suíte completa: `72 passed`.
- Testes de autenticação/ownership: `10 passed`.
- CI anterior confirmado como verde no GitHub Actions.
- Integrações reais, produção e credenciais permanecem bloqueadas até aprovação.
