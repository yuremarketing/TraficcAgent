# TraficcAgent — Alinhamento de produto e operação

Este documento reúne as decisões que devem ser respondidas pelos devs antes da implementação do sistema.

## Objetivo

Definir as regras comuns da fábrica de sites afiliados: garimpo de nichos e produtos, produção 90–10, publicação, tráfego e acompanhamento de resultados.

## Como usar

1. Cada dev responde às perguntas em uma cópia deste documento ou em uma reunião de alinhamento.
2. A equipe compara as respostas.
3. Divergências viram decisões explícitas em reunião.
4. Uma pessoa registra a resposta oficial neste documento.
5. Cada decisão aprovada deve virar requisito, issue ou critério de aceite.

## Decisões que precisam de resposta oficial

### 1. Modelo de produção

- O que será criado: site completo, pressell ou ambos?
- A meta inicial será 5 ou 10 sites por semana por dev?
- O trabalho será diário ou em lotes?
- Qual é o tempo máximo aceitável por site?

### 2. Papéis e permissões

- Cada dev terá três sites próprios ou haverá especialização por frente?
- Quem aprova conteúdo?
- Quem pode publicar?
- Quem pode alterar links, orçamento e regras financeiras?
- Haverá revisão cruzada obrigatória?

### 3. Modelo 90–10

- Quais partes a IA pode executar sem aprovação?
- Quais partes exigem intervenção humana?
- Como será registrada a contribuição humana?
- Quais condições bloqueiam a publicação?
- Quem assume a responsabilidade editorial?

### 4. Garimpo e validação

- Quais fontes serão usadas na primeira versão?
- Quais janelas serão analisadas: 24h, 7 dias, quinzena, mês, semestre e ano?
- O mercado será mundial, brasileiro, regional ou configurável?
- Como será usado o Distrito Federal ou a localização do público?
- Qual pontuação mínima aprova uma oportunidade?

### 5. Produto e afiliados

- Qual comissão mínima?
- Qual lucro líquido mínimo?
- Como tratar produtos sem estoque, preço ou conversão confiável?
- Quais redes de afiliados entram primeiro?
- Como armazenar IDs, links, UTM e data de validade?

### 6. Conteúdo editorial

- Quais formatos são obrigatórios: review, comparativo e guia?
- Quais fontes são aceitas?
- Como a IA deve sinalizar incertezas?
- Quais elementos humanos são obrigatórios?
- Qual padrão de transparência de afiliados será usado?
- Quem revisa Schema.org, SEO e factualidade?

### 7. Publicação e front-end

- Qual template será padrão?
- Quais campos mudam por nicho?
- O dev poderá alterar cores, layout e componentes?
- Quais testes são obrigatórios antes de publicar?
- Como será feito rollback?

### 8. Tráfego e otimização

- Quando usar SEO orgânico?
- Quando usar tráfego pago?
- Qual limite diário de orçamento?
- Qual definição oficial de ROI, CPC e conversão?
- Quando aplicar Early Stop?
- O pivô para SEO será automático ou exigirá aprovação?

### 9. Métricas e governança

- O sucesso será medido por volume, qualidade, receita ou ROI?
- Quais eventos precisam de auditoria?
- Por quanto tempo guardar histórico?
- Quais alertas devem chegar ao dev?
- Qual cadência de reunião e revisão?

## Resultado esperado

Ao final do alinhamento, a equipe deve produzir:

- uma resposta oficial para cada bloco;
- uma lista de decisões ainda pendentes;
- responsáveis por cada decisão;
- critérios de aceite do MVP;
- backlog priorizado;
- regras que não podem ser alteradas sem aprovação.

## Critério de pronto para implementação

O sistema só deve iniciar a construção do fluxo automático quando estiverem definidos: modelo de produção, permissões, regra 90–10, fontes de dados, critérios de produto, padrão editorial, gates de publicação, limites de tráfego e métricas de sucesso.

Atualize este documento por pull request. Não substitua respostas divergentes sem registrar o motivo, a data e os responsáveis pela decisão.
