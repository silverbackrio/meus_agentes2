"""
Views do app analise — API v1 /api/v1/analise/.

Regra R4 (``specs/aplicacao.md``): aqui **não se calcula** — as funções puras de
``calculos.py`` fazem a conta e a view só valida a entrada, arredonda na borda e
monta o envelope datado da R2 (``valor`` + ``unidade`` + ``data_base``/``as_of``).
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .calculos import resumo_simulacao
from .models import Cenario, Dossie, Metrica
from .serializers import (
    CenarioSerializer,
    DossieSerializer,
    MetricaSerializer,
)

ZERO = Decimal("0")

# Casas decimais na borda (arredondamento só aqui, nunca no meio da conta — R5).
_EXP_MOEDA = Decimal("0.01")
_EXP_PRECO = Decimal("0.0001")
_EXP_FRACAO = Decimal("0.000001")

FORMULA_PRECO_MEDIO = (
    "novo_preco_medio = (qtd_atual * preco_medio_atual + qtd_nova * preco_nova) "
    "/ (qtd_atual + qtd_nova)"
)
FORMULA_YOC = (
    "yield_on_cost = (proventos_12m_por_acao + (jcp_anual_por_acao ou 0)) / preco_medio"
)

AVISO_PROJECAO = (
    "Projeção com a premissa datada dos proventos dos últimos 12 meses — não é "
    "garantia de rendimento. Aceitar ou não o risco do ativo é decisão do usuário."
)


def _num(valor: Decimal, exp: Decimal) -> float:
    """Arredonda na borda e devolve ``float`` só para o JSON (o cálculo já é Decimal)."""
    return float(valor.quantize(exp, rounding=ROUND_HALF_UP))


def _campo_do_erro(mensagem: str) -> str:
    """Extrai o campo da mensagem ``"campo: motivo"`` para o envelope de erro (R2)."""
    return mensagem.split(":", 1)[0].strip() if ":" in mensagem else "entrada"


@api_view(["GET"])
def analise_list(request):
    """GET /analise/ — lista de métricas e cenários."""
    metricas = Metrica.objects.all()
    serializer_metricas = MetricaSerializer(metricas, many=True)
    return Response(serializer_metricas.data)


@api_view(["GET"])
def metricas_list(request):
    """GET /analise/metricas/ — métricas calculadas."""
    metricas = Metrica.objects.all()
    serializer = MetricaSerializer(metricas, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def cenarios_list(request):
    """GET /analise/cenarios/ — cenários de estresse."""
    cenarios = Cenario.objects.all()
    serializer = CenarioSerializer(cenarios, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def simular(request):
    """POST /analise/simular/ — simulador de preço médio, YoC e renda passiva.

    Bloco 1 da v1 (entrevista 27/10/2026): o usuário digita quantas ações pretende
    comprar e o backend devolve o novo preço médio, o yield on cost projetado e a
    renda passiva anual — com fórmula, data-base e o aviso de projeção.

    Não grava nada: é simulação, não operação (a escrita de operação é
    ``POST /carteira/operacoes/``).
    """
    if request.method != "POST":
        return Response(
            {"erro": "Método não permitido.", "campo": "metodo", "sugestao": "Use POST."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    dados = request.data if isinstance(request.data, dict) else {}
    data_base = str(dados.get("data_base") or date.today().isoformat())
    moeda = str(dados.get("moeda") or "BRL")
    ativo = str(dados.get("ativo") or "")
    unidade_preco = f"{moeda}/ação"

    obrigatorios = {
        "quantidade_atual": dados.get("quantidade_atual"),
        "preco_medio_atual": dados.get("preco_medio_atual"),
        "quantidade_nova": dados.get("quantidade_nova"),
        "preco_nova_compra": dados.get("preco_nova_compra"),
        "jcp_anual_por_acao": dados.get("jcp_anual_por_acao") or ZERO,
    }
    faltando = [campo for campo, valor in obrigatorios.items() if valor in (None, "")]
    if faltando:
        return Response(
            {
                "erro": "Faltou entrada obrigatória da simulação.",
                "campo": faltando[0],
                "sugestao": "Informe quantidade_atual, preco_medio_atual, quantidade_nova e preco_nova_compra.",
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        resultado = resumo_simulacao(
            quantidade_atual=obrigatorios["quantidade_atual"],
            preco_medio_atual=obrigatorios["preco_medio_atual"],
            quantidade_nova=obrigatorios["quantidade_nova"],
            preco_nova_compra=obrigatorios["preco_nova_compra"],
            preco_atual_tela=dados.get("preco_atual_tela"),
            proventos_12m_por_acao=dados.get("proventos_12m_por_acao"),
            jcp_anual_por_acao=(
                dados.get("jcp_anual_por_acao")
                if dados.get("jcp_anual_por_acao") not in (None, "")
                else ZERO
            ),
        )
    except ValueError as exc:
        mensagem = str(exc)
        return Response(
            {
                "erro": mensagem,
                "campo": _campo_do_erro(mensagem),
                "sugestao": "Corrija o campo indicado e reenvie a simulação.",
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Envelope da R2: todo número com valor, unidade e data-base.
    def bloco(valor, unidade, exp):
        if valor is None:
            return None
        return {
            "valor": _num(valor, exp),
            "unidade": unidade,
            "data_base": data_base,
        }

    moeda_fracao = "%"
    unidade_qtd = "títulos"
    preco_nova = Decimal(str(obrigatorios["preco_nova_compra"]))
    corpo = {
        "ativo": ativo,
        "moeda": moeda,
        "data_base": data_base,
        "as_of": data_base,
        "premissas": {
            "quantidade_atual": {
                "valor": _num(Decimal(str(obrigatorios["quantidade_atual"])), _EXP_PRECO),
                "unidade": unidade_qtd,
            },
            "preco_medio_atual": bloco(resultado["preco_medio_atual"], unidade_preco, _EXP_PRECO),
            "quantidade_nova": {
                "valor": _num(Decimal(str(obrigatorios["quantidade_nova"])), _EXP_PRECO),
                "unidade": unidade_qtd,
            },
            "preco_nova_compra": bloco(preco_nova, unidade_preco, _EXP_PRECO),
        },            "resultado": {
            "preco_medio_novo": bloco(resultado["preco_medio_novo"], unidade_preco, _EXP_PRECO),
            "quantidade_total": bloco(resultado["quantidade_total"], "títulos", _EXP_PRECO),
            "custo_novo_total": bloco(resultado["custo_novo_total"], moeda, _EXP_MOEDA),
            "pnl": bloco(resultado["pnl"], moeda, _EXP_MOEDA),
            "pnl_pct": bloco(resultado["pnl_pct"], moeda_fracao, _EXP_FRACAO),
            "yield_on_cost": bloco(resultado["yield_on_cost"], moeda_fracao, _EXP_FRACAO),
            "yield_on_cost_novo": bloco(resultado["yield_on_cost_novo"], moeda_fracao, _EXP_FRACAO),
            "projecao_renda_passiva": bloco(
                resultado["projecao_renda_passiva"], f"{moeda}/ano", _EXP_MOEDA
            ),
            "jcp_anual_por_acao": bloco(
                (
                    Decimal(str(obrigatorios["jcp_anual_por_acao"]))
                    if obrigatorios["jcp_anual_por_acao"] not in (None, "")
                    else ZERO
                ),
                f"{moeda}/ação/ano",
                _EXP_MOEDA,
            ),
        },
        "formula": {
            "preco_medio_novo": FORMULA_PRECO_MEDIO,
            "yield_on_cost": FORMULA_YOC,
        },
        "aviso": AVISO_PROJECAO,
    }
    return Response(corpo, status=status.HTTP_200_OK)


@api_view(["GET"])
def dossies_list(request):
    """GET /analise/dossies/ — dossiês datados."""
    dossies = Dossie.objects.all()
    serializer = DossieSerializer(dossies, many=True)
    return Response(serializer.data)
