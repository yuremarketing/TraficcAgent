# Caminho crítico TraficcAgent

Data: 14/09/2026

## Sequência e gates

1. **#17/#18/#19/#20/#23/#25 — Governança**  
   Estado: proposta documentada; aprovação de Philipy e Yure pendente.  
   Gate: papéis, propriedade, saída, divisão financeira e novos stakeholders aprovados.
2. **#27 — Auth**  
   Estado: autenticação local e sessão testadas; tenant/permissões finais pendentes.  
   Responsável: Yure.
3. **#28 — Ownership/Persistência**  
   Estado: sites e WorkItems protegidos; links, reviews, campanhas e métricas ainda sem persistência completa.  
   Responsável: Yure.
4. **#24/#31 — Segurança e produção**  
   Estado: checklist preparado; compliance, rollback e aprovação de produção pendentes.  
   Gate: segurança aprovada pelos dois sócios.
5. **#5/#33 — Ambiente e CI**  
   Estado: Docker local validado anteriormente; CI verde; 72 testes locais aprovados.  
   Pendência: branch protection e revisão/merge.
6. **#7 — Bot do Afiliado**  
   Estado: mock validado; integração real bloqueada por API key, sessão e contrato do serviço.
7. **#8/#9/#10 — Core**  
   Estado: regras e mocks testáveis; integração e dados reais pendentes.
8. **#11 — Pivô SEO**  
   Estado: lógica simulada testável; depende de métricas persistidas e critérios aprovados.
9. **#21/#30/#34 — Frontend**  
   Estado: MVD, XSS e toast avançados; evidência visual e PR/revisão pendentes.
10. **#12 — QA e lançamento**  
    Estado: 72 testes aprovados; E2E visual, aprovação conjunta e lançamento pendentes.

## Trabalho paralelo permitido

- Philipy: #5, #21, #30, #33, #34 e evidências da #12.
- Yure: #7, #16, #22, #27, #28, #24 e #31.
- Ambos: #17, #18, #19, #20, #23, #25 e aprovação final da #12.

## Regra de liberação

Nenhuma integração real, credencial, deploy ou lançamento é considerado concluído
sem testes, evidência, revisão, aprovação, merge e verificação na `master`.
