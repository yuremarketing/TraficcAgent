"""Motor de decisão financeira (issue #8).

Regra oficial (README / artefatos):
  - Aceita produtos com comissão percentual >= COMISSAO_MINIMA_PCT (10% por
    padrão).
  - Exceção "alto ticket": mesmo com comissão percentual abaixo do mínimo, o
    produto é aceito se o lucro líquido em reais estiver na faixa
    [ALTO_TICKET_LUCRO_MIN, ALTO_TICKET_LUCRO_MAX] (R$40 a R$50 por padrão) —
    cobre casos de produtos caros com comissão percentual baixa mas retorno
    absoluto relevante.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from traficcagent.config import BusinessRules


class DecisaoProduto(str, Enum):
    ACEITO_COMISSAO_MINIMA = "aceito_comissao_minima"
    ACEITO_ALTO_TICKET = "aceito_alto_ticket"
    REJEITADO = "rejeitado"

    @property
    def aceito(self) -> bool:
        return self is not DecisaoProduto.REJEITADO


@dataclass(frozen=True)
class Produto:
    nome: str
    preco: float
    comissao_pct: float

    def __post_init__(self) -> None:
        if not self.nome.strip():
            raise ValueError("Produto precisa ter nome.")
        if not math.isfinite(self.preco) or self.preco < 0:
            raise ValueError("Preço precisa ser um número não negativo.")
        if not math.isfinite(self.comissao_pct) or self.comissao_pct < 0:
            raise ValueError("Comissão precisa ser um número não negativo.")

    @property
    def lucro_liquido(self) -> float:
        return round(self.preco * (self.comissao_pct / 100), 2)


@dataclass(frozen=True)
class Avaliacao:
    produto: Produto
    decisao: DecisaoProduto
    motivo: str


def avaliar_produto(produto: Produto, rules: BusinessRules | None = None) -> Avaliacao:
    rules = rules or BusinessRules()

    if produto.comissao_pct >= rules.comissao_minima_pct:
        return Avaliacao(
            produto=produto,
            decisao=DecisaoProduto.ACEITO_COMISSAO_MINIMA,
            motivo=(
                f"Comissão de {produto.comissao_pct:.1f}% atinge o mínimo de "
                f"{rules.comissao_minima_pct:.1f}%."
            ),
        )

    lucro = produto.lucro_liquido
    if rules.alto_ticket_lucro_min <= lucro <= rules.alto_ticket_lucro_max:
        return Avaliacao(
            produto=produto,
            decisao=DecisaoProduto.ACEITO_ALTO_TICKET,
            motivo=(
                f"Comissão de {produto.comissao_pct:.1f}% está abaixo do mínimo, mas o "
                f"lucro líquido de R${lucro:.2f} cai na faixa de exceção de alto ticket "
                f"(R${rules.alto_ticket_lucro_min:.2f}–R${rules.alto_ticket_lucro_max:.2f})."
            ),
        )

    return Avaliacao(
        produto=produto,
        decisao=DecisaoProduto.REJEITADO,
        motivo=(
            f"Comissão de {produto.comissao_pct:.1f}% abaixo do mínimo de "
            f"{rules.comissao_minima_pct:.1f}% e lucro líquido de R${lucro:.2f} fora da "
            f"faixa de exceção de alto ticket "
            f"(R${rules.alto_ticket_lucro_min:.2f}–R${rules.alto_ticket_lucro_max:.2f})."
        ),
    )


def filtrar_produtos(produtos: list[Produto], rules: BusinessRules | None = None) -> list[Avaliacao]:
    rules = rules or BusinessRules()
    return [avaliar_produto(p, rules) for p in produtos]
