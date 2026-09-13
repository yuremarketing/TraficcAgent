from traficcagent.content.rag_engine import (
    FilaRevisaoHumana,
    StatusReview,
    gerar_rascunho_review,
    gerar_schema_jsonld,
)
from traficcagent.core.financial_engine import Produto


def test_rascunho_nasce_aguardando_revisao_humana():
    produto = Produto(nome="Fone Bluetooth", preco=100.0, comissao_pct=12.0)
    draft = gerar_rascunho_review(produto)
    assert draft.status == StatusReview.AGUARDANDO_REVISAO_HUMANA
    assert "mock" in draft.corpo_ia
    assert draft.schema_jsonld["@type"] == "Product"


def test_schema_jsonld_tem_review_snippet_valido():
    produto = Produto(nome="Fone Bluetooth", preco=100.0, comissao_pct=12.0)
    schema = gerar_schema_jsonld(produto)
    assert schema["@context"] == "https://schema.org"
    assert schema["offers"]["price"] == "100.00"
    assert schema["review"]["@type"] == "Review"


def test_fila_revisao_humana_move_para_publicado_ao_aprovar():
    produto = Produto(nome="Fone Bluetooth", preco=100.0, comissao_pct=12.0)
    draft = gerar_rascunho_review(produto)

    fila = FilaRevisaoHumana()
    fila.enfileirar(draft)
    assert draft in fila.pendentes

    fila.aprovar(draft, nota_humana="Revisado, ok publicar.")
    assert draft.status == StatusReview.PUBLICADO
    assert draft not in fila.pendentes
    assert draft in fila.publicados
    assert draft.nota_humana == "Revisado, ok publicar."


def test_aprovar_rascunho_fora_da_fila_falha():
    produto = Produto(nome="Fone Bluetooth", preco=100.0, comissao_pct=12.0)
    draft = gerar_rascunho_review(produto)
    fila = FilaRevisaoHumana()
    try:
        fila.aprovar(draft)
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass
