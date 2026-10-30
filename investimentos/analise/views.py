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
from .renda_fixa import (
    DIAS_BASE,
    NORMA_IOF,
    NORMA_IR,
    NORMA_ISSENCAO,
    RISCOS,
    comparar_produtos,
)
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

# compliance-e-avisos.md — "Avisos obrigatórios por tipo de resposta":
# comparação de produtos leva o aviso de comparação; dossiê é conteúdo
# analítico, com data-base e sem recomendação (R9 da aplicacao.md).
AVISO_COMPARATIVA = "Análise comparativa; a escolha e o aporte são seus."
AVISO_DOSSIE = (
    "Dossiê informativo com fontes e datas — não é recomendação de compra ou "
    "venda; números valem para a data-base indicada."
)

FORMULA_VF = "VF = VI * (1 + i)^(n/360)  — i efetiva anual, n em dias corridos"
FORMULA_IR = (
    "IR = rendimento * alíquota_da_faixa(prazo) — 22,5% até 180 dias; 20% de "
    "181 a 360; 17,5% de 361 a 720; 15% acima de 720 (Lei 11.033/2004, vigente em 2026)"
)
FORMULA_LIQUIDO = (
    "rendimento_liquido = VF - VI - IR - IOF; valor_recebido = VF - IR - IOF  "
    "(IOF zera no 30º dia — Decreto 6.306/2007)"
)
FORMULA_EQUIVALENCIA = (
    "equivalência no prazo comum = VI * (1 + taxa_líquida)^(prazo_comum/360), "
    "com taxa_líquida = (valor_recebido/VI)^(360/prazo) - 1"
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


@api_view(["GET"])
def dossie_detail(request, data: str):
    """GET /analise/dossies/{data} — dossiês de uma data (ISO-8601).

    A modelagem permite mais de um dossiê por data (unicidade é data+título),
    então a resposta é a lista daquele dia. Erros no envelope padrão:
    ``422`` para data fora do formato e ``404`` para data sem dossiê — o
    frontend mostra "não há dossiê para esta data" em vez de tela vazia.
    """
    try:
        data_obj = date.fromisoformat(data)
    except (TypeError, ValueError):
        return Response(
            {
                "erro": f"data: {data!r} não está em formato AAAA-MM-DD",
                "campo": "data",
                "sugestao": (
                    "Use AAAA-MM-DD (ex: 2026-10-27) e consulte "
                    "GET /analise/dossies/ para as datas disponíveis."
                ),
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    dossies = Dossie.objects.filter(data=data_obj)
    if not dossies.exists():
        return Response(
            {
                "erro": f"data: não há dossiê para {data_obj.isoformat()}",
                "campo": "data",
                "sugestao": "GET /analise/dossies/ lista as datas com dossiê disponível.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "data": data_obj.isoformat(),
            "data_base": data_obj.isoformat(),
            "total": dossies.count(),
            "dossies": DossieSerializer(dossies, many=True).data,
            "aviso": AVISO_DOSSIE,
        }
    )


@api_view(["GET"])
def comparar(request):
    """GET /comparar?ativos=&base=liquida — comparação justa em base líquida.

    Cada item de ``ativos`` carrega a entrada explícita do produto (regra 3 de
    AGENTS.md): ``nome|taxa_a_a|prazo_dias|tipo``, separado por vírgula — tipo
    é ``isento`` (LCI/LCA/CRI/CRA) ou ``tributado``. ``valor`` (VI, em BRL) é
    opcional e, quando omitido, entra como premissa declarada de R$ 10.000,00
    — o envelope diz qual foi usada. O formato está documentado em
    ``specs/aplicacao.md`` (R12).

    O cálculo é da função pura ``renda_fixa.comparar_produtos`` (R4): aqui só
    há validação, arredondamento na borda e o envelope datado da R2. Sem
    ordenação por retorno e sem recomendação (R9) — o ``aviso`` obrigatório de
    comparação acompanha a resposta.
    """
    ativos = request.query_params.get("ativos")
    base = request.query_params.get("base") or "liquida"
    if not ativos:
        return Response(
            {
                "erro": "ativos: parâmetro ausente",
                "campo": "ativos",
                "sugestao": "Use /api/v1/comparar/?ativos=nome|taxa_a_a|prazo_dias|tipo&base=liquida.",
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if base != "liquida":
        return Response(
            {
                "erro": f"base: {base!r} não é suportada",
                "campo": "base",
                "sugestao": "A v1 compara apenas em base líquida (base=liquida), como manda renda-fixa.md R5.",
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    produtos = []
    for item in str(ativos).split(","):
        item = item.strip()
        partes = [parte.strip() for parte in item.split("|")]
        if len(partes) != 4 or not all(partes):
            return Response(
                {
                    "erro": f"ativos: {item!r} não está no formato nome|taxa_a_a|prazo_dias|tipo",
                    "campo": "ativos",
                    "sugestao": "Ex: CDB Banco A|10|720|tributado,LCI Banco B|11.5|365|isento",
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        nome, taxa, prazo, tipo = partes
        if tipo not in {"isento", "tributado"}:
            return Response(
                {
                    "erro": f"tipo: {tipo!r} em {nome!r} não é válido",
                    "campo": "tipo",
                    "sugestao": "Use 'isento' (LCI, LCA, CRI, CRA — Lei 11.033/2004 art. 3º) ou 'tributado'.",
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        produtos.append(
            {"nome": nome, "taxa": taxa, "prazo_dias": prazo, "isento": tipo == "isento"}
        )

    valor_s = request.query_params.get("valor")
    vi_entrada = valor_s if valor_s not in (None, "") else "10000"
    try:
        resultado = comparar_produtos(produtos, vi_entrada)
    except ValueError as exc:
        mensagem = str(exc)
        return Response(
            {
                "erro": mensagem,
                "campo": _campo_do_erro(mensagem),
                "sugestao": "Corrija o produto apontado e reenvie a comparação.",
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    hoje = date.today().isoformat()

    def _bloco(valor, unidade, exp=_EXP_MOEDA):
        """Envelope datado da R2: valor + unidade + data_base."""
        return {"valor": _num(valor, exp), "unidade": unidade, "data_base": hoje}

    itens = []
    for item in resultado["itens"]:
        itens.append(
            {
                "nome": item["nome"],
                "prazo_dias": item["prazo_dias"],
                "tipo": "isento" if item["isento"] else "tributado",
                "taxa_bruta": _bloco(item["taxa_bruta"] * 100, "% a.a.", _EXP_FRACAO),
                "ir": {
                    "aliquota": _bloco(item["aliquota_ir"] * 100, "%", _EXP_FRACAO),
                    "faixa": item["faixa_ir"],
                    "norma": NORMA_ISSENCAO if item["isento"] else NORMA_IR,
                },
                "bruto": _bloco(item["valor_futuro"], "BRL"),
                "imposto": _bloco(item["imposto"], "BRL"),
                "iof": _bloco(item["iof"], "BRL"),
                "rendimento_liquido": _bloco(item["rendimento_liquido"], "BRL"),
                "valor_recebido": _bloco(item["valor_recebido"], "BRL"),
                "taxa_liquida": _bloco(item["taxa_liquida_aa"] * 100, "% a.a.", _EXP_FRACAO),
                "taxa_bruta_no_prazo_comum": _bloco(
                    item["taxa_bruta_no_prazo_comum"] * 100, "% a.a.", _EXP_FRACAO
                ),
                "valor_recebido_no_prazo_comum": _bloco(
                    item["valor_recebido_no_prazo_comum"], "BRL"
                ),
            }
        )

    return Response(
        {
            "base": "liquida",
            "data_base": hoje,
            "as_of": hoje,
            "valor_inicial": _bloco(resultado["valor_inicial"], "BRL"),
            "convencao": {
                "dias_base": DIAS_BASE,
                "periodo": "dias corridos",
                "unidade_taxa": "% a.a. (efetiva anual)",
            },
            "prazo_comum_dias": resultado["prazo_comum_dias"],
            "itens": itens,
            "formula": {
                "valor_futuro": FORMULA_VF,
                "ir": FORMULA_IR,
                "liquido": FORMULA_LIQUIDO,
                "equivalencia": FORMULA_EQUIVALENCIA,
            },
            "normas": [NORMA_IR, NORMA_ISSENCAO, NORMA_IOF],
            "riscos": list(RISCOS),
            "aviso": AVISO_COMPARATIVA,
        }
    )
