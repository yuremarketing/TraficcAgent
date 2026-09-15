# Decisões conjuntas — proposta do Philipy

Status: proposta aguardando aprovação do Yure
Data: 14/09/2026

Este documento registra a posição operacional do Philipy. Nenhum item abaixo
é acordo definitivo até haver aprovação explícita dos dois sócios.

## 1. Regras de negócio

- Cada site deve ter nicho, produto, link afiliado, pauta, responsável e status.
- O fluxo padrão é: produto → margem → link → review → aprovação → campanha → monitoramento → decisão.
- A operação começa em modo manual/tester; automações só entram após validação humana.
- Site sem resultado deve ser pausado ou arquivado, preservando o histórico.

Decisão do Yure: [ ] aprovar [ ] ajustar

## 2. Papéis e permissões

- Yure: sócio operacional, dev sênior, arquitetura, backend, integrações e vendas.
- Philipy: sócio capitalista, dev júnior, distribuição, frontend, portfólio e vendas.
- Ações de produção, credenciais, deploy e merge na `master` exigem revisão do Yure.
- Ações de distribuição, teste visual e operação manual podem ser executadas pelo Philipy.

Decisão do Yure: [ ] aprovar [ ] ajustar

## 3. Divisão financeira

Proposta a definir em reunião: registrar separadamente aportes, custos operacionais,
receita bruta, taxas, impostos e lucro líquido. Nenhuma porcentagem é presumida
neste documento.

Decisão conjunta obrigatória: percentual de cada sócio, pró-labore, reinvestimento,
reserva e data de fechamento mensal.

## 4. Critérios de ROI e pausa

Proposta inicial para teste, não regra definitiva:

- Registrar orçamento, custo, cliques, conversões, receita, CPA e ROI por campanha.
- Não escalar campanha sem dados mínimos definidos pelos sócios.
- Pausar quando atingir o limite de custo aprovado ou quando não houver sinal de conversão dentro da janela acordada.
- Toda decisão de escala, otimização ou arquivamento deve deixar histórico.

Decisão conjunta: valores, janela de análise e limite de perda.

### Baseline operacional para aprovação

- ROI = `(receita - custo) / custo * 100`.
- Registrar no mínimo orçamento, cliques, conversões e receita por campanha.
- Usar janela inicial de 60 a 90 dias para SEO; não concluir fracasso por poucos dias.
- Pausar imediatamente ao atingir o orçamento-piloto aprovado sem conversão.
- Escalar somente após dois períodos consecutivos com ROI positivo e double-check humano.
- Reabrir a campanha quando houver nova hipótese, ajuste de oferta ou evidência de recuperação.

Os valores acima são baseline de teste e aguardam aprovação conjunta; não substituem
acordo societário nem autorização de produção.

## 5. Fluxo operacional

Proposta do Philipy: validar manualmente cada etapa com double-check de 10% antes
de automatizar. O Tester pode simular; produção real exige responsável definido.

Decisão do Yure: [ ] aprovar [ ] ajustar

## 6. Validação do produto e lançamento

- Produto só entra na esteira após validação de nicho, demanda, comissão, margem e risco.
- Lançamento exige conteúdo revisado, link validado, mobile conferido e plano de monitoramento.
- O primeiro lançamento deve ser tratado como piloto, com orçamento limitado e critérios de parada.

Decisão conjunta: checklist final, orçamento-piloto e responsável pela aprovação.

## 7. Novos stakeholders

Antes de incluir outra pessoa, definir por escrito: papel, acesso, contribuição,
remuneração, propriedade intelectual, confidencialidade, saída e autoridade de decisão.

Decisão conjunta obrigatória antes de conceder acesso ao repositório, dados ou contas.

## 8. Caminho crítico para desbloqueio

1. Yure aprovar ou ajustar papéis e permissões.
2. Os dois definirem divisão financeira e reinvestimento.
3. Os dois aprovarem critérios de ROI, pausa e lançamento-piloto.
4. Yure confirmar o contrato técnico do backend e produção.
5. Registrar a decisão final no GitHub antes do deploy.

## 9. Matriz de aprovação

- Mudança de arquitetura, credencial, deploy ou segurança: Yure revisa; ambos aprovam impacto de negócio.
- Distribuição, teste visual e dados simulados: Philipy executa; ambos aprovam lançamento.
- Divisão financeira, propriedade, entrada/saída e venda da operação: aprovação explícita dos dois.
- Nenhum stakeholder novo recebe acesso antes de papel, escopo, remuneração, confidencialidade e saída documentados.

## 10. Checklist de aprovação conjunta

- [ ] #17/#18: papéis, responsabilidades e permissões aprovados por ambos.
- [ ] #19: governança geral aprovada por ambos.
- [ ] #20: regras de stakeholders e autoridade aprovadas por ambos.
- [ ] #23: saída, abandono, venda e continuidade aprovados por ambos.
- [ ] #25: propriedade, participação e divisão financeira aprovadas por ambos.
- [ ] ROI, pausa, escala e lançamento-piloto aprovados por ambos.
- [ ] #12: fluxo manual ponta a ponta executado e aprovado por ambos.

### Registro de aprovação

- Philipy: [ ] aprovado  Data: ____  Observações: ____________________
- Yure: [ ] aprovado  Data: ____  Observações: ____________________
