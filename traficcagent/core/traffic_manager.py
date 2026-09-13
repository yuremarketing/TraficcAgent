"""Robô de gestão de tráfego pago (issue #9).

Regra oficial (README / artefatos):
  - Trava de Early Stop: se a campanha já rodou por >= EARLY_STOP_DIAS (3 dias
    por padrão) e ainda não teve nenhuma conversão, corta o gasto.
  - Maturação: se as métricas estão saudáveis (já converteu), mantém a
    campanha rodando até MATURACAO_DIAS (14 dias por padrão) para dar tempo
    do Smart Bidding do Google Ads aprender.
  - Antes do fim do Early Stop, ainda não há dados suficientes para decidir.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from traficcagent.config import BusinessRules


class StatusTrafego(str, Enum):
    AGUARDANDO_DADOS = "aguardando_dados"
    CORTAR_EARLY_STOP = "cortar_early_stop"
    MANTER_MATURACAO = "manter_maturacao"
    MADURA_REAVALIAR = "madura_reavaliar"


@dataclass(frozen=True)
class CampanhaMetrics:
    nome: str
    dias_ativa: int
    custo_total: float
    conversoes: int

    @property
    def cpa(self) -> float | None:
        """Custo por aquisição (conversão). None se ainda não converteu."""
        if self.conversoes <= 0:
            return None
        return round(self.custo_total / self.conversoes, 2)

    @property
    def tem_roi(self) -> bool:
        return self.conversoes > 0


@dataclass(frozen=True)
class DecisaoTrafego:
    campanha: CampanhaMetrics
    status: StatusTrafego
    motivo: str

    @property
    def deve_cortar_gasto(self) -> bool:
        return self.status == StatusTrafego.CORTAR_EARLY_STOP


def avaliar_campanha(campanha: CampanhaMetrics, rules: BusinessRules | None = None) -> DecisaoTrafego:
    rules = rules or BusinessRules()

    if campanha.dias_ativa < rules.early_stop_dias:
        return DecisaoTrafego(
            campanha=campanha,
            status=StatusTrafego.AGUARDANDO_DADOS,
            motivo=(
                f"Campanha com {campanha.dias_ativa} dia(s) ativa, ainda dentro da "
                f"janela de observação de {rules.early_stop_dias} dias."
            ),
        )

    if not campanha.tem_roi:
        return DecisaoTrafego(
            campanha=campanha,
            status=StatusTrafego.CORTAR_EARLY_STOP,
            motivo=(
                f"Sem nenhuma conversão após {campanha.dias_ativa} dia(s) ativa "
                f"(limite de observação: {rules.early_stop_dias} dias) — corte de gasto."
            ),
        )

    if campanha.dias_ativa < rules.maturacao_dias:
        return DecisaoTrafego(
            campanha=campanha,
            status=StatusTrafego.MANTER_MATURACAO,
            motivo=(
                f"Métricas saudáveis (CPA R${campanha.cpa:.2f}) — mantendo até "
                f"{rules.maturacao_dias} dias para o Smart Bidding maturar."
            ),
        )

    return DecisaoTrafego(
        campanha=campanha,
        status=StatusTrafego.MADURA_REAVALIAR,
        motivo=(
            f"Campanha atingiu {rules.maturacao_dias} dias com conversões — "
            "pronta para reavaliação de margem (ver gatilho de pivô SEO)."
        ),
    )
