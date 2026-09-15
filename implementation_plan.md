# Plano de implementação — MVD de gerenciamento

## Escopo aprovado

- Navegação funcional entre telas.
- Formulários locais para sites e links.
- Responsividade para desktop, tablet e celular.
- Componentes visuais reutilizáveis no HTML.
- Dados mockados para a operação.
- Estados de sucesso, erro, vazio e confirmação.
- Ações locais de criar, filtrar, duplicar e arquivar sites.
- Teste simples dos fluxos principais.
- Validação visual no navegador.

## Fora do escopo

Claude/IA externa, credenciais, banco de dados, autenticação, APIs, infraestrutura e deploy.

## Guardrails de colaboração e entrega

1. Trabalho de desenvolvimento somente em branch de tarefa; nunca diretamente na `master`.
2. Cada mudança deve ter issue, commits pequenos e PR rastreável.
3. O PR deve registrar escopo, arquivos alterados, testes, riscos, impedimentos e critério de aceite.
4. A `master` deve exigir revisão, CI verde e bloquear force push.
5. Merge agrupado por bloco coerente, preferencialmente uma vez por dia; hotfix crítico é exceção.
6. Após o merge, validar o commit e os arquivos na `master`.
7. Alterações de arquitetura, produção, credenciais, permissões e negócio exigem decisão do Yure ou de ambos, conforme a issue.
8. Nenhuma entrega será considerada concluída apenas por existir localmente: precisa de commit, PR, revisão, merge e validação.

## Entregáveis planejados

- `CONTRIBUTING.md` com o fluxo de branch, commit, PR e merge.
- Template de PR com checklist de evidências.
- Template de issue com responsável, dependências, aceite e impedimentos.
- `CODEOWNERS` e workflow de validação para proteger a revisão da `master`.
- Documento de relatório diário da operação e das entregas.

## Nova etapa proposta — Central de operação integrada

### Objetivo

Transformar o `mvp.html` no painel operacional integrado, com navegação responsiva e estado compartilhado entre Central de operação, sites, calendário, links afiliados, pautas/reviews, fila de aprovação e usuários.

### Fases

1. Extrair o estado local para um modelo único versionado, com eventos e histórico.
2. Integrar a Central de operação ao dashboard sem iframe, mantendo as oito etapas e o double-check 90/10.
3. Conectar ações de site, lote, link, pauta e aprovação ao mesmo estado.
4. Implementar perfil Tester com permissões simuladas de leitura, navegação e registro de bugs.
5. Adicionar filtros, estados vazio/sucesso/erro e feedback visual consistente.
6. Validar responsividade em celular, tablet e desktop.
7. Criar testes de fumaça para os fluxos principais e registrar evidências no PR.

### Fora desta etapa

Autenticação real, banco remoto, integrações com credenciais, deploy de produção e autorização server-side continuam no escopo do backend do Yure.

### Critérios de aceite

- [ ] Dashboard abre todas as áreas sem iframe quebrado.
- [ ] Central de operação aparece entre Pautas e reviews e Fila de aprovação.
- [ ] Criar/editar/duplicar/arquivar e aprovar atualiza o estado compartilhado.
- [ ] Cada ação gera histórico com usuário, etapa, horário e resultado.
- [ ] Perfil Tester não recebe ações de produção.
- [ ] Fluxos funcionam em viewport móvel.
- [ ] Testes e smoke test passam.
- [ ] PR contém evidências e impedimentos restantes.
