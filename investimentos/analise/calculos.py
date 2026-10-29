"""Cálculos de domínio — funções puras, sem Django, sem rede, sem estado.

Por que este módulo existe (princípio P3 e regra R4 de ``specs/aplicacao.md``):
a mesma fórmula precisa servir a view, a um comando de manage.py, a um teste e a
qualquer app futura. Aqui **nada** importa Django: entrada explícita, saída
``Decimal``, fórmula documentada. Quem não deve calcular nunca é o JavaScript —
o React só renderiza o que saiu daqui.

Regra de dinheiro (R5): tudo em ``Decimal``, nunca ``float``. Arredondamento
acontece só na borda (view/serializer), nunca no meio da conta.

Responsabilidade desta versão: Bloco 1 da v1 — gestão de posição
(preço médio, P&L, yield on cost e projeção de renda passiva), decidido na
entrevista de 27/10/2026 (caso BBAS3).
"""

from decimal import Decimal, InvalidOperation

ZERO = Decimal("0")


def _decimal(valor, campo: str) -> Decimal:
    """Converte entrada para ``Decimal`` com mensagem de erro que o campo aponta.

    Aceita ``Decimal``, ``int``, ``str`` (ex.: "80.50") e ``float`` (último caso,
    apenas por cortesia — quem chama deve mandar ``Decimal`` ou ``str`` para não
    herdar o erro de representação do float).
    """
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, bool):  # bool é subclasse de int em Python: bloquear
        raise ValueError(f"{campo}: informe um número, não um booleano")
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, str):
        try:
            return Decimal(valor.replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(f"{campo}: {valor!r} não é um número válido") from exc
    if isinstance(valor, float):
        return Decimal(str(valor))
    raise ValueError(f"{campo}: tipo {type(valor).__name__} não é um número")


def _positivo(valor, campo: str) -> Decimal:
    """Converte e exige número estritamente positivo (entrada de preço/quantidade)."""
    numero = _decimal(valor, campo)
    if numero <= ZERO:
        raise ValueError(f"{campo}: precisa ser maior que zero (recebido {numero})")
    return numero


def novo_preco_medio(
    preco_medio_atual,
    quantidade_atual,
    preco_nova_compra,
    quantidade_nova,
):
    """Preço médio resultante depois de um novo aporte.

    Fórmula (custo total novo ÷ quantidade total nova)::

        novo_pm = (qtd_atual * pm_atual + qtd_nova * preco_nova) / (qtd_atual + qtd_nova)

    ``quantidade_atual`` pode ser zero (primeira compra); os demais precisam ser
    positivos. Caso de borda: ``quantidade_nova`` negativa modela **venda parcial**
    e é aceita de propósito — preço médio de quem vende não muda, então a função
    devolve o mesmo ``preco_medio_atual``.

    Exemplo do GLOSSARY: c.m. R$ 30,00 com 100 títulos + 100 a R$ 24,00 → R$ 27,60.
    """
    pm_atual = _decimal(preco_medio_atual, "preco_medio_atual")
    qtd_atual = _decimal(quantidade_atual, "quantidade_atual")
    preco_nova = _decimal(preco_nova_compra, "preco_nova_compra")
    qtd_nova = _decimal(quantidade_nova, "quantidade_nova")

    if qtd_atual < ZERO:
        raise ValueError("quantidade_atual: não pode ser negativa")
    if pm_atual < ZERO:
        raise ValueError(f"preco_medio_atual: não pode ser negativa (recebido {pm_atual})")
    if preco_nova <= ZERO:
        raise ValueError(f"preco_nova_compra: precisa ser maior que zero (recebido {preco_nova})")
    if qtd_nova == ZERO:
        raise ValueError("quantidade_nova: zero não muda preço médio — informe a compra")

    # Venda parcial: preço médio não muda (fato de custo, não de mercado).
    if qtd_nova < ZERO:
        if abs(qtd_nova) > qtd_atual:
            raise ValueError("quantidade_nova: venda maior que a posição atual")
        return pm_atual

    custo_atual = qtd_atual * pm_atual
    custo_nova = qtd_nova * preco_nova
    quantidade_total = qtd_atual + qtd_nova
    return (custo_atual + custo_nova) / quantidade_total


def pnl(quantidade, preco_medio, preco_atual):
    """    Preco lucro/prejuizo nao realizado: ``(preco atual - preco medio) * quantidade``.

    Sai em duas partes: valor em moeda e percentual sobre o custo
    (``(preco atual / preco medio) - 1``), porque a tela do Bloco 1 mostra as duas.
    Retorna ``(valor, percentual)`` como ``Decimal``; percentual é fração
    (0,10 = +10%).
    """
    qtd = _positivo(quantidade, "quantidade")
    pm = _positivo(preco_medio, "preco_medio")
    atual = _positivo(preco_atual, "preco_atual")

    valor = (atual - pm) * qtd
    percentual = (atual / pm) - Decimal("1")
    return valor, percentual


def _rendimento_total(
    proventos_12m_por_acao: Decimal,
    jcp_anual_por_acao: Decimal,
) -> Decimal:
    """Rendimento anual projetado por ação = proventos + JCP (quando JCP é informado).

    Ainda sem fonte real (pendência 10 do CONTEXT.md): no esqueleto, o JCP entra
    como parâmetro separado e pode ser zero. A premissa é sempre "se esse rendimento
    se repetir no próximo ano", nunca garantia (``compliance-e-avisos.md``).
    """
    proventos = _positivo(proventos_12m_por_acao, "proventos_12m_por_acao")
    jcp = _decimal(jcp_anual_por_acao, "jcp_anual_por_acao")
    if jcp < ZERO:
        raise ValueError(
            f"jcp_anual_por_acao: não pode ser negativo (recebido {jcp})"
        )
    return proventos + jcp


def yield_on_cost(
    proventos_12m_por_acao: Decimal,
    preco_medio: Decimal,
    jcp_anual_por_acao: Decimal | None = None,
) -> Decimal:
    """Yield on cost: rendimento total projetado por ação ÷ preço médio pago.

    Quando ``jcp_anual_por_acao`` é omitido, usa apenas os proventos. Quando
    informado, soma proventos + JCP antes de dividir pelo custo.

    Sempre **projeção**, nunca garantia (``specs/compliance-e-avisos.md``).
    Sai como fração — 0,076 = 7,6% a.a. sobre o custo.

    Fórmula::

        rendimento_total = proventos_12m_por_acao + (jcp_anual_por_acao ou 0)
        YoC = rendimento_total ÷ preco_medio
    """
    pm = _positivo(preco_medio, "preco_medio")
    rendimento = _rendimento_total(proventos_12m_por_acao, jcp_anual_por_acao or ZERO)
    return rendimento / pm


def projecao_renda_passiva(
    quantidade: Decimal,
    proventos_12m_por_acao: Decimal,
    preco_medio: Decimal | None = None,
    jcp_anual_por_acao: Decimal | None = None,
) -> tuple[Decimal, Decimal | None]:
    """Renda passiva anual projetada da posição, em moeda da posição.

    ``quantidade * (proventos_12m_por_acao + jcp_anual_por_acao)``. Se
    ``preco_medio`` for informado, devolve também o YoC — assim a view preenche
    o bloco inteiro em uma chamada.

    Retorna ``(renda_anual, yield_on_cost | None)``.
    """
    qtd = _positivo(quantidade, "quantidade")
    rendimento = _rendimento_total(proventos_12m_por_acao, jcp_anual_por_acao or ZERO)

    renda = qtd * rendimento
    yoc = yield_on_cost(proventos_12m_por_acao, preco_medio, jcp_anual_por_acao) if preco_medio is not None else None
    return renda, yoc


def resumo_simulacao(
    *,
    quantidade_atual,
    preco_medio_atual,
    quantidade_nova,
    preco_nova_compra,
    preco_atual_tela=None,
    proventos_12m_por_acao=None,
    jcp_anual_por_acao=None,
):
    """Monta o dicionário completo do simulador do Bloco 1 (entrada da view).

    Todas as chaves saem em ``Decimal``. Campos opcionais voltam ``None`` quando
    não informados — a view decide o que mostrar; aqui não existe número
    inventado para "preencher a tela".

    Levanta ``ValueError`` com a mensagem pronta para virar ``{erro, campo,
    sugestao}`` (HTTP 422) quando a entrada for inválida.
    """
    pm_novo = novo_preco_medio(
        preco_medio_atual=preco_medio_atual,
        quantidade_atual=quantidade_atual,
        preco_nova_compra=preco_nova_compra,
        quantidade_nova=quantidade_nova,
    )

    resultado: dict[str, Decimal | None] = {
        "preco_medio_atual": _decimal(preco_medio_atual, "preco_medio_atual"),
        "preco_medio_novo": pm_novo,
        "custo_novo_total": _decimal(quantidade_nova, "quantidade_nova")
        * _decimal(preco_nova_compra, "preco_nova_compra"),
        "quantidade_total": _decimal(quantidade_atual, "quantidade_atual")
        + _decimal(quantidade_nova, "quantidade_nova"),
        "pnl": None,
        "pnl_pct": None,
        "yield_on_cost": None,
        "yield_on_cost_novo": None,
        "projecao_renda_passiva": None,
    }

    if preco_atual_tela is not None:
        valor, percentual = pnl(
            quantidade=resultado["quantidade_total"],
            preco_medio=pm_novo,
            preco_atual=preco_atual_tela,
        )
        resultado["pnl"] = valor
        resultado["pnl_pct"] = percentual

    if proventos_12m_por_acao is not None:
        renda, yoc_novo = projecao_renda_passiva(
            quantidade=resultado["quantidade_total"],
            proventos_12m_por_acao=proventos_12m_por_acao,
            preco_medio=pm_novo,
        )
        resultado["projecao_renda_passiva"] = renda
        resultado["yield_on_cost_novo"] = yoc_novo
        resultado["yield_on_cost"] = yield_on_cost(
            proventos_12m_por_acao=proventos_12m_por_acao,
            preco_medio=resultado["preco_medio_atual"],
        )

    return resultado
