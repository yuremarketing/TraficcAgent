from traficcagent.content.rag_engine import (
    FilaRevisaoHumana,
    StatusReview,
    gerar_rascunho_review,
    gerar_schema_jsonld,
)
from traficcagent.core.financial_engine import Produto
import pytest


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


def test_prompt_e_backend_recebem_dados_do_produto():
    produto = Produto(nome="Notebook Pro", preco=2500.0, comissao_pct=8.0)
    prompts = []

    class FakeLLM:
        def generate(self, prompt):
            prompts.append(prompt)
            return "Conteúdo revisável"

    draft = gerar_rascunho_review(produto, FakeLLM())
    assert "Notebook Pro" in prompts[0]
    assert "2500.00" in prompts[0]
    assert draft.corpo_ia == "Conteúdo revisável"


def test_retorno_vazio_do_llm_e_rejeitado():
    class EmptyLLM:
        def generate(self, prompt):
            return "  "

    produto = Produto(nome="Produto", preco=100, comissao_pct=10)
    with pytest.raises(ValueError, match="conteúdo válido"):
        gerar_rascunho_review(produto, EmptyLLM())


def test_schema_jsonld_preserva_nome_e_preco_do_produto():
    schema = gerar_schema_jsonld(Produto(nome="Câmera", preco=1234.5, comissao_pct=10))
    assert schema["name"] == "Câmera"
    assert schema["offers"]["priceCurrency"] == "BRL"
    assert schema["offers"]["price"] == "1234.50"


def test_fila_nao_publica_rascunho_sem_enfileirar():
    produto = Produto(nome="Produto", preco=100, comissao_pct=10)
    draft = gerar_rascunho_review(produto)
    fila = FilaRevisaoHumana()
    with pytest.raises(ValueError):
        fila.aprovar(draft)
    assert draft.status == StatusReview.AGUARDANDO_REVISAO_HUMANA
