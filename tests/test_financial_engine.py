from traficcagent.config import BusinessRules
from traficcagent.core.financial_engine import (
    DecisaoProduto,
    Produto,
    avaliar_produto,
    filtrar_produtos,
)


def test_aceita_por_comissao_minima():
    produto = Produto(nome="Fone Bluetooth", preco=100.0, comissao_pct=12.0)
    avaliacao = avaliar_produto(produto)
    assert avaliacao.decisao == DecisaoProduto.ACEITO_COMISSAO_MINIMA
    assert avaliacao.decisao.aceito


def test_aceita_por_excecao_alto_ticket():
    # 6% de R$750 = R$45 de lucro líquido, dentro da faixa R$40-R$50.
    produto = Produto(nome="Notebook", preco=750.0, comissao_pct=6.0)
    avaliacao = avaliar_produto(produto)
    assert avaliacao.decisao == DecisaoProduto.ACEITO_ALTO_TICKET
    assert avaliacao.decisao.aceito


def test_rejeita_comissao_baixa_e_fora_da_faixa_alto_ticket():
    produto = Produto(nome="Capinha de celular", preco=20.0, comissao_pct=5.0)
    avaliacao = avaliar_produto(produto)
    assert avaliacao.decisao == DecisaoProduto.REJEITADO
    assert not avaliacao.decisao.aceito


def test_limites_da_faixa_alto_ticket_sao_inclusivos():
    regras = BusinessRules(alto_ticket_lucro_min=40.0, alto_ticket_lucro_max=50.0)
    limite_inferior = Produto(nome="A", preco=800.0, comissao_pct=5.0)  # lucro = 40.0
    limite_superior = Produto(nome="B", preco=1000.0, comissao_pct=5.0)  # lucro = 50.0
    assert avaliar_produto(limite_inferior, regras).decisao == DecisaoProduto.ACEITO_ALTO_TICKET
    assert avaliar_produto(limite_superior, regras).decisao == DecisaoProduto.ACEITO_ALTO_TICKET


def test_filtrar_produtos_preserva_ordem():
    produtos = [
        Produto(nome="Aceito", preco=100.0, comissao_pct=15.0),
        Produto(nome="Rejeitado", preco=10.0, comissao_pct=2.0),
    ]
    resultados = filtrar_produtos(produtos)
    assert [r.produto.nome for r in resultados] == ["Aceito", "Rejeitado"]
    assert resultados[0].decisao.aceito
    assert not resultados[1].decisao.aceito
