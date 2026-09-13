from traficcagent.core.financial_engine import Produto
from traficcagent.core.seo_pivot import DecisaoPivo, avaliar_pivo
from traficcagent.core.traffic_manager import CampanhaMetrics
from traficcagent.config import BusinessRules


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


def test_pivota_no_limite_exato_da_margem():
    produto = Produto(nome="Fone", preco=100.0, comissao_pct=15.0)
    campanha = CampanhaMetrics(nome="C1", dias_ativa=5, custo_total=150.0, conversoes=10)
    assert avaliar_pivo(produto, campanha).decisao == DecisaoPivo.PIVOTAR_SEO_ORGANICO


def test_respeita_janela_customizada_de_observacao():
    produto = Produto(nome="Fone", preco=100.0, comissao_pct=15.0)
    campanha = CampanhaMetrics(nome="C1", dias_ativa=2, custo_total=200.0, conversoes=0)
    regras = BusinessRules(early_stop_dias=2)
    assert avaliar_pivo(produto, campanha, regras).decisao == DecisaoPivo.PIVOTAR_SEO_ORGANICO


def test_mantem_pago_com_cpa_muito_abaixo_da_margem():
    produto = Produto(nome="Notebook", preco=2000.0, comissao_pct=10.0)
    campanha = CampanhaMetrics(nome="C1", dias_ativa=13, custo_total=10.0, conversoes=5)
    assert avaliar_pivo(produto, campanha).decisao == DecisaoPivo.MANTER_TRAFEGO_PAGO
