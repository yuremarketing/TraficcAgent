"""Motor de conteúdo RAG híbrido 90/10 (issue #10).

Regra oficial (README / artefatos):
  - 90% do conteúdo do review é gerado pela IA (RAG sobre os dados do
    produto).
  - Os 10% restantes são toque humano: todo rascunho nasce em
    `StatusReview.AGUARDANDO_REVISAO_HUMANA` e só é publicado depois que
    alguém aprova via `FilaRevisaoHumana.aprovar`.
  - Todo review publicado carrega o JSON-LD de Schema.org (`Product` +
    `Review`/`AggregateRating`) para habilitar Review Snippets no Google.

Sem ANTHROPIC_API_KEY, `gerar_rascunho_review` usa `MockLLMBackend` — um
template determinístico, só para exercitar o pipeline (fila de revisão +
geração de schema) sem depender de chamada real de LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from traficcagent.core.financial_engine import Produto


class LLMBackend(Protocol):
    def generate(self, prompt: str) -> str: ...


class MockLLMBackend:
    """Backend determinístico usado quando não há ANTHROPIC_API_KEY."""

    def generate(self, prompt: str) -> str:
        return (
            "[conteúdo gerado por IA — mock]\n"
            "Este review cobre os principais recursos, prós, contras e "
            "melhor custo-benefício com base nos dados do produto."
        )


@dataclass
class AnthropicLLMBackend:
    """Backend real. Requer `anthropic` instalado e ANTHROPIC_API_KEY.

    TODO (bloqueado por credencial, ver issue #10): validar prompts finais
    com um review real assim que a chave estiver disponível em produção.
    """

    api_key: str
    model: str = "claude-sonnet-5"

    def generate(self, prompt: str) -> str:
        import anthropic  # import tardio: dependência opcional

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class StatusReview(str, Enum):
    AGUARDANDO_REVISAO_HUMANA = "aguardando_revisao_humana"
    PUBLICADO = "publicado"


@dataclass
class ReviewDraft:
    produto: Produto
    corpo_ia: str
    schema_jsonld: dict
    status: StatusReview = StatusReview.AGUARDANDO_REVISAO_HUMANA
    nota_humana: str | None = None


def montar_prompt_review(produto: Produto) -> str:
    return (
        f"Escreva um review de afiliado para o produto '{produto.nome}', "
        f"preço R${produto.preco:.2f}, destacando prós, contras e para quem "
        "vale a pena comprar. Tom neutro e informativo, sem exagero."
    )


def gerar_schema_jsonld(produto: Produto) -> dict:
    """JSON-LD Schema.org (Product + Review) para Review Snippets."""
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": produto.nome,
        "offers": {
            "@type": "Offer",
            "price": f"{produto.preco:.2f}",
            "priceCurrency": "BRL",
        },
        "review": {
            "@type": "Review",
            "reviewRating": {
                "@type": "Rating",
                # Placeholder — substituído pela nota real na revisão humana.
                "ratingValue": "4.5",
                "bestRating": "5",
            },
            "author": {"@type": "Organization", "name": "TraficcAgent"},
        },
    }


def gerar_rascunho_review(produto: Produto, llm: LLMBackend | None = None) -> ReviewDraft:
    llm = llm or MockLLMBackend()
    corpo = llm.generate(montar_prompt_review(produto))
    return ReviewDraft(
        produto=produto,
        corpo_ia=corpo,
        schema_jsonld=gerar_schema_jsonld(produto),
    )


@dataclass
class FilaRevisaoHumana:
    """Fila simples que guarda os 10% de toque humano antes da publicação."""

    pendentes: list[ReviewDraft] = field(default_factory=list)
    publicados: list[ReviewDraft] = field(default_factory=list)

    def enfileirar(self, draft: ReviewDraft) -> None:
        self.pendentes.append(draft)

    def aprovar(self, draft: ReviewDraft, nota_humana: str | None = None) -> None:
        if draft not in self.pendentes:
            raise ValueError("Rascunho não está na fila de revisão.")
        draft.status = StatusReview.PUBLICADO
        draft.nota_humana = nota_humana
        self.pendentes.remove(draft)
        self.publicados.append(draft)
