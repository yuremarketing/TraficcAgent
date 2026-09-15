# Evidências de validação do MVD

Data: 14/09/2026

## Escopo

Validação local das entregas das issues #5, #21, #30 e #33.

## Checks executados

- `dist/index.html`: JavaScript compilado com sucesso via Node.js.
- `dist/mvp.html`: JavaScript compilado com sucesso via Node.js.
- `git diff --check`: aprovado.
- `py -3 -m pytest -q`: **71 passed**.
- Cenários de dois usuários e acesso cruzado: `tests/test_auth_and_ownership.py` + `tests/test_api.py` → **21 passed**.
- Os testes confirmam que sites do Philipy não aparecem para Yure e que acesso direto por ID é rejeitado.
- `.github/workflows/pytest.yml`: presente e configurado para Python 3.12 + `pytest`.
- Último workflow confirmado: GitHub Actions run `34869826414`, concluído com sucesso na branch `dev/philipy`.
- `GET http://localhost:8080/healthz`: respondeu `{"status":"ok","service":"traficcagent"}`.
- Proteção XSS: `escapeHTML` presente no frontend e aplicado aos dados dinâmicos renderizados.
- Dados simulados: sites, links, pautas, lotes e estado da operação persistidos em `localStorage` no MVD.
- Responsividade: breakpoints CSS verificados em `950px` e `620px`, com colunas empilhadas no celular.

## Roteiro manual

1. Criar ou entrar com um usuário.
2. Criar um site e confirmar sua exibição no dashboard.
3. Pesquisar e filtrar o site.
4. Duplicar e arquivar o site.
5. Cadastrar link, pauta e lote local.
6. Abrir a Central de operação e avançar as etapas.
7. Exportar os dados e confirmar o arquivo JSON.
8. Repetir em viewport móvel para conferir responsividade.

## Pendências externas

- O Compose completo exige `POSTGRES_PASSWORD` no `.env`.
- Links, pautas, lotes e métricas ainda usam armazenamento local no frontend até a integração definitiva com a API.
- Capturas visuais em 1440px, 768px e 390px ainda precisam ser feitas no navegador local; a sessão de automação bloqueou `localhost`/`file://`.
- Deploy e credenciais de produção dependem da configuração do Yure.
