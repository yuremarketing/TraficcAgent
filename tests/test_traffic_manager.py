from traficcagent.core.traffic_manager import (
    CampanhaMetrics,
    StatusTrafego,
    avaliar_campanha,
)


def test_aguardando_dados_antes_do_early_stop():
    campanha = CampanhaMetrics(nome="C1", dias_ativa=1, custo_total=50.0, conversoes=0)
    decisao = avaliar_campanha(campanha)
    assert decisao.status == StatusTrafego.AGUARDANDO_DADOS
    assert not decisao.deve_cortar_gasto


def test_corta_gasto_sem_roi_apos_early_stop():
    campanha = CampanhaMetrics(nome="C1", dias_ativa=3, custo_total=200.0, conversoes=0)
    decisao = avaliar_campanha(campanha)
    assert decisao.status == StatusTrafego.CORTAR_EARLY_STOP
    assert decisao.deve_cortar_gasto


def test_mantem_para_maturacao_com_metricas_saudaveis():
    campanha = CampanhaMetrics(nome="C1", dias_ativa=5, custo_total=100.0, conversoes=4)
    decisao = avaliar_campanha(campanha)
    assert decisao.status == StatusTrafego.MANTER_MATURACAO
    assert not decisao.deve_cortar_gasto
    assert campanha.cpa == 25.0


def test_madura_reavaliar_apos_14_dias_com_conversoes():
    campanha = CampanhaMetrics(nome="C1", dias_ativa=14, custo_total=300.0, conversoes=10)
    decisao = avaliar_campanha(campanha)
    assert decisao.status == StatusTrafego.MADURA_REAVALIAR
