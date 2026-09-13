from traficcagent.core.financial_engine import Produto
from traficcagent.core.seo_pivot import DecisaoPivo, avaliar_pivo
from traficcagent.core.traffic_manager import CampanhaMetrics


def test_aguardando_dados_repassa_status_do_trafego():
    produto = Produto(nome="Fone", preco=100.0, comissao_pct=15.0)
    campanha = CampanhaMetrics(nome="C1", dias_ativa=1, custo_total=30.0, conversoes=0)
    avaliacao = avaliar_pivo(produto, campanha)
    assert avaliacao.decisao == DecisaoPivo.AGUARDANDO_DADOS


def test_pivota_quando_early_stop_sem_conversao():
    produto = Produto(nome="Fone", preco=100.0, comissao_pct=15.0)
    campanha = CampanhaMetrics(nome="C1", dias_ativa=3, custo_total=200.0, conversoes=0)
    avaliacao = avaliar_pivo(produto, campanha)
    assert avaliacao.decisao == DecisaoPivo.PIVOTAR_SEO_ORGANICO


def test_pivota_quando_cpa_zera_a_margem():
    # Lucro líquido do produto: 15% de R$100 = R$15.
    produto = Produto(nome="Fone", preco=100.0, comissao_pct=15.0)
    # CPA de R$20 (100/5) já ultrapassa a margem de R$15.
    campanha = CampanhaMetrics(nome="C1", dias_ativa=5, custo_total=100.0, conversoes=5)
    avaliacao = avaliar_pivo(produto, campanha)
    assert avaliacao.decisao == DecisaoPivo.PIVOTAR_SEO_ORGANICO


def test_mantem_trafego_pago_quando_cpa_abaixo_da_margem():
    # Lucro líquido do produto: 15% de R$100 = R$15.
    produto = Produto(nome="Fone", preco=100.0, comissao_pct=15.0)
    # CPA de R$10 (100/10) está abaixo da margem de R$15.
    campanha = CampanhaMetrics(nome="C1", dias_ativa=5, custo_total=100.0, conversoes=10)
    avaliacao = avaliar_pivo(produto, campanha)
    assert avaliacao.decisao == DecisaoPivo.MANTER_TRAFEGO_PAGO
