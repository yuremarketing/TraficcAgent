### Documentação Técnica e Backlog de Engenharia: TraficcAgent

Esta documentação detalha a arquitetura, as diretrizes de negócio e o planejamento de engenharia para o  **TraficcAgent** , um agente autônomo de Growth Hacking projetado para automatizar a descoberta de produtos de alta conversão, gestão de tráfego pago via  **MCP**  e transição inteligente para estratégias de SEO focadas em  **AI Overviews** .

#### 1\. Visão Geral e Contexto Scrum

##### 1.1. Fase de Inception e Product Discovery

O  **TraficcAgent**  surge para resolver o gap de automação no marketing de afiliados do Mercado Livre. O foco central é a captura de usuários em  **Fundo de Funil** , onde a intenção de compra é imediata (ex: buscas por "melhor faca de churrasco profissional"). O agente atua na intersecção entre análise de dados de produtos e execução automatizada de anúncios, garantindo que o capital seja alocado apenas em itens de alta rentabilidade.

##### 1.2. Refinamento de Backlog: Prioridades Iniciais

1. **Ingestão de Dados** : Integração com a API do Bot do Afiliado para extração de metatags e preços.  
2. **Gestão de Tráfego** : Implementação do  **Google Ads MCP Server**  para automação de lances e criação de campanhas.  
3. **Persistência de Estado** : Configuração de banco de dados NoSQL ( **Firestore** ) para armazenamento de tokens e histórico de performance de produtos.

##### 1.3. Especificação de Critérios de Aceite (AC)

Uma  **User Story**  é considerada "Done" quando:

*  O link de afiliado é gerado via endpoint /api/v1/convert-links com success: true.  
*  O processamento em lote respeita o limite técnico de  **150 URLs**  por requisição.  
*  A ferramenta list\_accessible\_customers do  **MCP**  valida a conta de destino antes do deploy.  
*  O anúncio é confirmado no Google Ads via ferramenta search com query  **GAQL** .  
*  O site de destino injeta automaticamente  **Dados Estruturados**  (JSON-LD) para indexação em  **AI Overviews** .

#### 2\. Regras de Negócio: Inteligência de Afiliados

##### 2.1. Filtros de Rentabilidade

A viabilidade econômica do  **TraficcAgent**  depende da seleção rigorosa de SKUs. O LLM deve aplicar o filtro de comissão mínima de  **10%**  sobre o valor de venda.

##### 2.2. Exceção para Alto Ticket

Para produtos de valor elevado (Ticket Médio \> R $400,00), a regra percentual é substituída pelo ganho absoluto. Se o lucro por conversão estiver entre **R$  40,00 e R$ 50,00**, o produto é aprovado para tráfego pago, independentemente de a porcentagem ser inferior a 10%.

##### 2.3. Automação de Links (Bot do Afiliado)

Devido à ausência de uma API oficial de afiliados no Mercado Livre, o agente utiliza a engine do Bot do Afiliado.

* **Base URL** : https://botdoafiliado.com/api/v1/  
* **Endpoints** : /api/v1/convert-links (atribuição) e /api/v1/product (metadados).  
* **Segurança** : Autenticação via header  **X-API-Key** . É mandatório que o agente mantenha um  **cookie de sessão**  e a  **tag**  configurados no plugin para evitar erros 400 conversion\_failed.

#### 3\. Estratégia de Tráfego e Matriz de Decisão

##### 3.1. Dilema de Gestão de Caixa

O agente deve balancear a proteção do capital ( **Early Stop** ) com a necessidade de aprendizado dos algoritmos de IA do Google.| Estratégia | Janela de Decisão | Gatilho de Ação | Objetivo Técnico || \------ | \------ | \------ | \------ || **Proteção de Caixa** | 3 dias | ROAS \< 0.8 ou CPC \> Comis/10 | Mitigação de prejuízo imediato. || **Learning Window** | 7 a 14 dias | Conversões \> 0 | Estabilização do algoritmo de Smart Bidding. || **SEO Pivot** | Imediato | **Google Trends**  em queda | Migração para tráfego orgânico/review. |

##### 3.2. Fórmulas de Performance (ROAS e CPA)

O monitoramento é feito via  **GAQL**  consumindo métricas do  **MCP** :

* **ROAS**  \= (Σ product.price\_number \* % Comis) / (Σ metrics.cost\_micros / 1.000.000)  
* **CPA**  \= (Total Gasto em Reais) / (Número de Conversões Confirmadas)

##### 3.3. Transição Automática para Tráfego Orgânico

Quando o  **CPC**  inviabiliza a margem de lucro no tráfego pago, o agente aciona o workflow de SEO. A decisão de migração é validada pelo  **Google Trends**  para identificar termos de busca emergentes. O conteúdo é direcionado para "Sites de Review" (modelo Rei da Carne), otimizando para o  **Google AI Overviews**  através da densidade semântica e autoridade.

#### 4\. Arquitetura Técnica End-to-End

##### 4.1. Integração com Google Ads MCP Server

O agente opera através do servidor oficial googleads/google-ads-mcp, utilizando:

* **Ferramentas** : search (análise de métricas), get\_resource\_metadata (validação de esquemas) e list\_accessible\_customers (configuração inicial).  
* **Resources** : O agente deve consultar periodicamente os recursos metrics e segments para ajustar as queries  **GAQL** .  
* **Infraestrutura** : Deploy via  **Docker**  em  **Google Cloud Run** . A persistência de tokens e estados de autenticação deve ser feita no  **Firestore**  para garantir escalabilidade stateless.

##### 4.2. Pipeline RAG de Conteúdo (Regra 90/10)

Para escalar a criação de sites de review sem comprometer o  **E-E-A-T** :

* **90% Automação** : LLMs geram descrições técnicas, comparativos e metatags.  
* **10% Curadoria Humana** : Intervenção para adicionar "experiência real" e nuances de especialista, fator determinante para ranking orgânico atual.

##### 4.3. Fluxo de Dados de Produto

1. **Ingestão** : Busca de produtos via /api/v1/product.  
2. **Enriquecimento** : Geração de  **Dados Estruturados**  (Schema.org \- Merchant Listings) em formato JSON-LD.  
3. **Deploy Ads** : Injeção de anúncios responsivos via  **MCP**  utilizando o final\_url (encurtado com tag de atribuição).  
4. **Monitoramento** : Loop de feedback entre conversões e novos lances via  **GAQL** .

#### 5\. Estrutura de Implementação do Repositório (GitHub)

##### 5.1. Mapeamento de Diretórios

* README.md: Documentação de setup e variáveis de ambiente.  
* Dockerfile: Configuração para deploy em  **Cloud Run** .  
* /docs: Relatórios de Discovery e especificações de  **E-E-A-T** .  
* /src:  
* /agents: Core do  **TraficcAgent** .  
* /connectors: Integração com /api/v1/ do Bot do Afiliado.  
* /mcp\_wrappers: Lógica de interação com ferramentas de search e metadata.  
* /config:  
* tools\_config.yaml: Namespacing das ferramentas  **MCP** .  
* cloud\_run\_env.yaml: Definição de secrets e recursos de infra.

##### 5.2. Instruções de Configuração

1. **Segredos** : Configurar GOOGLE\_ADS\_DEVELOPER\_TOKEN e GOOGLE\_ADS\_MCP\_OAUTH\_CLIENT\_ID no Secret Manager.  
2. **Auth** : Habilitar a  **Google Ads API**  e configurar as  **Application Default Credentials (ADC)**  utilizando o escopo https://www.googleapis.com/auth/adwords.  
3. **Persistência** : Definir GOOGLE\_ADS\_MCP\_STORAGE\_TYPE=firestore para cache de tokens e metadados.

#### 6\. Backlog de Desenvolvimento (Roadmap Técnico)

##### 6.1. Sprint 1: Fundação e Infra

* Configuração do ambiente  **Docker**  e deploy inicial no  **Cloud Run** .  
* Implementação de  **ADC**  e suporte a múltiplas contas via list\_accessible\_customers.  
* Setup do  **Firestore**  para persistência de tokens de sessão.

##### 6.2. Sprint 2: Inteligência de Conversão

* Integração completa com a API do Bot do Afiliado (/api/v1/).  
* Desenvolvimento da lógica de filtros de 10% e regras de Alto Ticket.  
* Automação de criação de campanhas via  **MCP**  com lances dinâmicos.

##### 6.3. Sprint 3: Otimização e SEO

* Implementação do gerador de  **Dados Estruturados**  (JSON-LD) para produtos.  
* Automação do gatilho de transição Pago \-\> Orgânico baseado em ROI e  **Google Trends** .  
* Monitoramento avançado de performance via queries  **GAQL**  customizadas para  **AI Overviews** .

&nbsp;