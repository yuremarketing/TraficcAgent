# 🤖 TraficcAgent: Agente Autônomo de Afiliados e Tráfego Multicanal

O **TraficcAgent** é uma solução baseada em Inteligência Artificial Generativa e Arquitetura de Agentes Autônomos projetada para automatizar o ciclo completo de venda de produtos de afiliados (como **Mercado Livre**), integrando gestão de **Tráfego Pago (Google Ads)** e atração por **Tráfego Orgânico (SEO, Google AI Overviews e ChatGPT)**.

---

## 📌 Visão Geral da Arquitetura

O sistema opera como um orquestrador *end-to-end*, conectando garimpo de produtos, geração de conteúdo otimizado, gestão automatizada de campanhas e inteligência financeira de tomada de decisão.

```text
[ Garimpo no Mercado Livre ] ──> [ Redação 90/10 com IA/SEO ] ──> [ Publicação no Site PDN/Nicho ]
                                                                             │
[ Ajuste de CPC via MCP ] <── [ Monitoramento de Vendas/ROAS ] <── [ Lançamento no Google Ads ]
```

---

## ⚙️ Regras de Negócio e Filtros de Garimpo

1. **Filtro Padrão de Comissão:**
   * Seleção preferencial de produtos com comissão mínima de **10%** (alcançando 12% a 20% em promoções pontuais).
2. **Exceção para Produtos de Alto Ticket:**
   * Para itens de valor elevado (ex: R$ 800,00 a R$ 3.000,00), aceitam-se taxas menores (8% a 10%), desde que o retorno absoluto seja de no mínimo **R$ 40,00 a R$ 50,00 por venda**.

---

## 🚦 Matriz de Decisão: Tráfego Pago vs. Orgânico

### 1. Tráfego Pago (Google Ads) & Trava de 3 Dias (*Early Stop*)
* **Guarda-Corpo Precoce (3 Dias):** O agente analisa métricas de topo e meio de funil nos primeiros 3 dias (72h) para mitigar riscos financeiros:
  * `CTR < 1%`: Reformulação do anúncio ou palavras-chave.
  * `Gasto > 1 Comissão sem Conversão/Clique de Saída`: Interrupção imediata.
  * `Sem Impressões/Cliques`: Reajuste de CPC teto ou verificação de políticas.
* **Janela de Aprendizado do Leilão (7 a 14 Dias):** Caso os indicadores de 3 dias sejam saudáveis, a campanha é mantida para que o leilão do Google Ads otimize os lances automáticos (*Smart Bidding*).
* **Cálculo do ROAS Líquido:**
  $$\text{CPA} = \text{CPC Médio} \times \text{Cliques por Venda} < \text{Comissão em Reais}$$

### 2. Transição Automática para Tráfego Orgânico (CPC R$ 0,00)
* Quando o CPC do Google Ads inviabilizar a margem de lucro, o agente desativa a campanha paga e pivotará autonomamente para o **Tráfego Orgânico**.
* Produção de artigos comparativos e reviews de fundo de funil enriquecidos com dados estruturados (`Schema.org` / `ReviewSnippet`) para ranquear no Google Search e ser recomendado em motores de IA (**Google AI Overviews** e **ChatGPT**).

---

## 🛠️ Conectores Técnicos & Integrações

| Componente | Tipo de Integração | Descrição / Protocolo |
| :--- | :--- | :--- |
| **Google Ads** | `MCP Server` (Oficial) | Leitura de métricas, campanhas e relatórios via GAQL utilizando o Model Context Protocol (`googleads/google-ads-mcp`). |
| **Mercado Livre** | `REST API` / Scraping | Conversão automática de links de rastreamento e extração de dados via API de terceiros (ex: Bot do Afiliado com `X-API-Key`). |
| **Engine de Conteúdo** | `RAG 90/10` | 90% da produção e pesquisa executadas por LLM + 10% de curadoria e validação de qualidade técnica. |

---

## 📂 Estrutura do Repositório

```text
traficc-agent/
├── README.md                   # Documentação principal e arquitetura executiva
├── artefatos/                  # Relatórios técnicos, diagramas e especificações
│   ├── especificacao-tecnica.md
│   ├── diagrama-arquitetura.png
│   └── relatorio-scrum-backlog.md
├── docs/                       # Manuais operacionais e diretrizes
│   ├── business-rules.md       # Regras de comissão e calculadoras de ROAS
│   └── decision-matrix.md      # Condicionais de Early Stop (3 vs 14 dias)
├── config/                     # Arquivos de configuração do MCP e APIs
│   └── mcp_tools_config.yaml   # Mapeamento de ferramentas do Google Ads MCP
└── src/                        # Código fonte das automações e agentes
    ├── garimpo/                # Scripts de busca e filtragem no Mercado Livre
    ├── conteudo/               # Gerador de artigos de review SEO 90/10
    └── anuncios/               # Conector GAQL e automação Google Ads
```

---

## 🚀 Como Executar

### Pré-requisitos
* Python 3.12+
* Node.js / Docker (para execução do Google Ads MCP Server)
* Chaves de API: `GOOGLE_ADS_DEVELOPER_TOKEN`, `BOT_DO_AFILIADO_KEY`

### Instalação Rápida
```bash
# Clone o repositório
git clone https://github.com/yuremarketing/TraficcAgent.git
cd TraficcAgent

# Configure o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS ou venv\Scripts\activate no Windows

# Instale as dependências
pip install -r requirements.txt
```

---

## 📄 Licença e Uso

Este projeto é desenvolvido para fins de automação de marketing de afiliados e arbitragem de tráfego. Desenvolvido seguindo as melhores práticas de SEO e políticas oficiais do Google Ads e Mercado Livre.

## Alinhamento da equipe

## Alinhamento da equipe

- [Documento oficial de alinhamento dos devs](docs/ALINHAMENTO-DEVS.md)
- [Dashboard do sistema](dist/dashboard.html)
- [Mockup da pressell pública](dist/index.html)

O quiz deve ser respondido individualmente e consolidado pela equipe antes da implementação do MVP. As decisões oficiais devem ser registradas em `docs/ALINHAMENTO-DEVS.md` por pull request.
