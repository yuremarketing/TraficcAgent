### Especificação de Requisitos e Arquitetura RAG: TraficcAgent

##### 1\. Visão Geral do TraficcAgent e Contexto de Negócio

O  **TraficcAgent**  é uma solução de arquitetura RAG (Retrieval-Augmented Generation) de alta performance, desenhada para operar na intersecção entre a autoridade de conteúdo (SEO) e a conversão direta (Ads). Diferente de assistentes genéricos, o agente é otimizado para o  **fundo de funil** , segmentando usuários com o mais alto "Nível de Consciência" — aqueles que já decidiram pela compra e buscam validação técnica ou comparativos de preço e performance. O sistema deve priorizar a captura de tráfego vindo de "AI Overview" e "AI-powered Search", transformando a documentação técnica do Google em estratégias acionáveis para sites de review de nicho (ex: Rei da Carne, PDN Materiais), visando maximizar o ROI em programas de afiliados como Mercado Livre e Amazon.

##### 2\. Mapeamento da Estrutura de Conhecimento (Base de Dados RAG)

A base vetorial deve indexar de forma granular a documentação oficial, com metadados que permitam a filtragem por tipo de consulta.| Categoria de Conhecimento | Temas-Chave | Utilidade para o Agente || \------ | \------ | \------ || **Fundamentos da Pesquisa** | Metatags, atributos HTML, requisitos técnicos e políticas de spam. | Garantir a integridade técnica do site e evitar punições por práticas "Black Hat". || **Rastreamento e Indexação** | robots.txt, Sitemaps,  **Canonização**  e Redirecionamentos. | Consolidar URLs duplicadas em sites de afiliados e gerenciar o orçamento de rastreamento (Crawl Budget). || **Google Ads: Estrutura** | **8 passos para o sucesso** , Performance Max (PMax), Search e Smart Bidding. | Implementar o framework de configuração de campanhas focado em conversão imediata. || **Políticas de Privacidade** | Requisitos de conformidade do Google Ads e proteção de dados. | Garantir que o agente não sugira estratégias que violem as regras de privacidade do anunciante. || **E-commerce & Rich Results** | **Product Snippets** ,  **Review Snippets**  e Merchant Center. | Estruturar dados para que o Google exiba preço, avaliação e estoque diretamente na SERP. |

##### 3\. Requisitos Funcionais do Agente

O agente deve operar como um motor de decisão baseado nos seguintes pilares funcionais:

1. **Segmentação de Intenção de Fundo de Funil:**  Filtrar e priorizar termos de busca que indiquem decisão de compra iminente (ex: "melhor máquina de solda profissional" ou "faca artesanal custo-benefício").  
2. **Orquestração de Campanha (8 Passos):**  Executar a lógica de preparação descrita na documentação do Google Ads (support.google.com/google-ads/topic/10554989), desde a definição de metas até a revisão final.  
3. **Comparativo de Preço e Performance:**  Gerar matrizes de decisão baseadas na curadoria da PDN Materiais, focando nos parâmetros de "Qualidade, Preço e Performance".  
4. **Geração de Dados Estruturados para E-commerce:**  Automatizar a criação de JSON-LD para  *Product Snippets* , garantindo que a "IA Overview" extraia informações corretas do site de review.  
5. **Depuração Lógica de Tráfego:**  Em caso de oscilações, aplicar o fluxo de "Depurar quedas de tráfego" da Search Central, distinguindo entre atualizações de algoritmos (Core Updates) e problemas técnicos de indexação.

##### 4\. Arquitetura de Recuperação (RAG) e Tipos de Consultas

Para evitar alucinações e garantir o  **Absolute Grounding** , o sistema deve implementar  **Metadata Filtering**  nas consultas:

* **Consultas Informativas Técnicas:**  O sistema deve filtrar exclusivamente a "Search Central" (ex: "Como implementar rel=canonical em páginas de review?").  
* **Consultas de Estratégia de Performance:**  O sistema deve priorizar o "Ads Help" (ex: "Como configurar Smart Bidding para produtos com comissão variável?").  
* **Filtro de Segurança e Ética:**  O agente deve rejeitar automaticamente qualquer prompt que induza a práticas de spam ou conteúdo não útil, conforme definido em developers.google.com/search/docs/essentials/spam-policies.

##### 5\. Parâmetros de Otimização e Regras de Decisão

O motor de regras deve integrar dados de marketing e lógica de negócios de afiliados:| Se (Condição/Input) | Então (Ação do Agente) || \------ | \------ || Detecção de  **Ganho Extra de Comissão**  (ex: 12% para 20%) | Acionar regra de lance agressivo no Smart Bidding/PMax para o SKU específico. || Objetivo é "Autoridade de Nicho" | Priorizar conteúdo de "Toque Humano" e monitoramento via Search Console. || Produto classificado como "Profissional" (Modelo PDN) | Destacar parâmetros de "Eficiência" e "Alta Performance" no anúncio/artigo. || Consulta sobre queda de tráfego pós-update | Iniciar diagnóstico via developers.google.com/search/docs/monitor-debug/debugging-search-traffic-drops. || Busca por "Melhor Produto" | Gerar review comparativo com links de afiliados (Amazon/Mercado Livre) e Review Snippets. |

##### 6\. Requisitos Não-Funcionais

* **Fidelidade Absoluta à Fonte:**  Toda recomendação técnica deve vir acompanhada do campo source\_url apontando para a URL exata da documentação do Google (ex: developers.google.com/search/docs/essentials).  
* **Latência Crítica:**  Respostas para ajustes de lances de leilão em tempo real devem ter latência sub-segundo para integração via API.  
* **Privacidade por Design:**  Adesão rigorosa às políticas de privacidade e proteção de dados mencionadas no support.google.com/google-ads/topic/11337105.  
* **Robustez Algorítmica:**  O sistema deve ser capaz de distinguir entre consultas informativas (topo de funil) e transacionais (fundo de funil), recusando-se a processar estratégias de baixo ROI.

##### 7\. Estratégia de Conteúdo e Conversão (Integração de Nicho)

O TraficcAgent orienta a criação de ativos digitais baseados no modelo de "Sites Lucrativos":

* **Produção Híbrida de Conteúdo:**  Uso de IA para 90% da redação técnica (especificações e dados brutos) e obrigatoriedade do  **"Toque Humano para Diferenciação"**  nos 10% finais (edição, tom de voz e confiabilidade editorial).  
* **Autoridade de Nicho Ultra-Segmentado:**  Foco em micro-nichos de alta conversão, como "máquinas de solda profissionais" ou "facas artesanais para churrasco", visando o ranqueamento acelerado.  
* **Engenharia de Conversão:**  Inserção estratégica de CTAs de "Confira o Preço" vinculados diretamente ao Mercado Livre ou Amazon, utilizando a estrutura de review validada pelos modelos Rei da Carne e PDN Materiais.

&nbsp;