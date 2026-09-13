"""Gatilho de pivô automático para SEO orgânico (issue #11).

Regra oficial (README / artefatos):
  - Quando o custo por aquisição (CPA) da campanha paga passa a zerar (ou
    ultrapassar) a margem de lucro líquido do produto, o tráfego pago deixa
    de ser viável: a campanha é desligada e o esforço migra por completo para
    ranquear organicamente (SEO técnico, Google AI Overviews, respostas de
    LLMs como o ChatGPT).
  - Também dispara o pivô quando o robô de tráfego (#9) decide cortar por
    Early Stop: gastar sem nenhuma conversão já é sinal de que o canal pago
    não está funcionando para aquele produto/nicho.

Este módulo depende das decisões de #8 (financial_engine) e #9
(traffic_manager) — ele não reimplementa a lógica delas, apenas combina os
resultados.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from traficcagent.core.financial_engine import Produto
from traficcagent.core.traffic_manager import CampanhaMetrics, StatusTrafego, avaliar_campanha


class DecisaoPivo(str, Enum):
    MANTER_TRAFEGO_PAGO = "manter_trafego_pago"
    PIVOTAR_SEO_ORGANICO = "pivotar_seo_organico"
    AGUARDANDO_DADOS = "aguardando_dados"


@dataclass(frozen=True)
class AvaliacaoPivo:
    decisao: DecisaoPivo
    motivo: str


def avaliar_pivo(
    produto: Produto, campanha: CampanhaMetrics, rules=None
) -> AvaliacaoPivo:
    trafego = avaliar_campanha(campanha, rules)

    if trafego.status == StatusTrafego.AGUARDANDO_DADOS:
        return AvaliacaoPivo(
            decisao=DecisaoPivo.AGUARDANDO_DADOS,
            motivo=trafego.motivo,
        )

    if trafego.status == StatusTrafego.CORTAR_EARLY_STOP:
        return AvaliacaoPivo(
            decisao=DecisaoPivo.PIVOTAR_SEO_ORGANICO,
            motivo=(
                "Early Stop acionado sem nenhuma conversão — canal pago não "
                "validou o produto/nicho. " + trafego.motivo
            ),
        )

    margem = produto.lucro_liquido
    cpa = campanha.cpa  # não é None aqui: MANTER_MATURACAO/MADURA_REAVALIAR implicam conversões
    assert cpa is not None

    if cpa >= margem:
        return AvaliacaoPivo(
            decisao=DecisaoPivo.PIVOTAR_SEO_ORGANICO,
            motivo=(
                f"CPA de R${cpa:.2f} já iguala ou ultrapassa a margem líquida de "
                f"R${margem:.2f} por venda — o CPC zerou o lucro do tráfego pago."
            ),
        )

    return AvaliacaoPivo(
        decisao=DecisaoPivo.MANTER_TRAFEGO_PAGO,
        motivo=(
            f"CPA de R${cpa:.2f} ainda está abaixo da margem líquida de R${margem:.2f} "
            "por venda — tráfego pago continua viável."
        ),
    )
