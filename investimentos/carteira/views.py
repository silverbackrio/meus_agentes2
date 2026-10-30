"""Views do app carteira — API v1 /api/v1/carteira/.

Contrato da API (specs/aplicacao.md):
- GET  /carteira/resumo/ — posições, custo médio, pesos atuais vs política, P&L com as_of
- POST /carteira/operacoes/ — registrar operação (valida evento, data, base de cálculo)
- GET  /carteira/ — lista de posições

Regra R4: aqui **não se calcula** — o custo médio vem de `analise/calculos.py` (função pura),
e a view só monta o envelope datado da R2 (valor + unidade + data_base).
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from investimentos.analise.calculos import novo_preco_medio

from .models import Operacao, Politica, Posicao
from .serializers import (
    OperacaoSerializer,
    PosicaoSerializer,
)

_EXP = Decimal("0.0001")
_ZERO = Decimal("0")


def _num(valor: Decimal, exp: Decimal = _EXP) -> float:
    """Arredonda na borda e devolve float só para o JSON (cálculo é Decimal — R5)."""
    return float(valor.quantize(exp, rounding=ROUND_HALF_UP))


def _erro(mensagem: str, sugestao: str, codigo=status.HTTP_422_UNPROCESSABLE_ENTITY):
    """Envelope de erro padrão da API: {erro, campo, sugestao}."""
    campo = mensagem.split(":", 1)[0].strip() if ":" in mensagem else "entrada"
    return Response({"erro": mensagem, "campo": campo, "sugestao": sugestao}, status=codigo)


@api_view(["GET"])
def carteira_list(request):
    """GET /carteira/ — lista de posições de carteira."""
    posicoes = Posicao.objects.all()
    serializer = PosicaoSerializer(posicoes, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def carteira_resumo(request):
    """GET /carteira/resumo/ — resumo completo da carteira.

    Retorna:
    - Posições com custo médio atual vs. preço de referência (se disponível)
    - P&L não realizado por posição
    - Pesos atuais vs. política (quando houver política definida)
    - Data-base (as_of) do dado mais recente
    """
    hoje = date.today().isoformat()
    posicoes_data = []
    total_geral = _ZERO

    # Processar cada posição
    for pos in Posicao.objects.all():
        # Estado inicial = valores gravados na posição (abertura da carteira).
        # As operações salvas depois disso são aplicadas em cima — assim o
        # custo médio sai da soma de todas as operações (Rodada 11 do
        # CONTEXT.md), sem ignorar a posição que já existia.
        qtd_atual = pos.quantidade
        pm_atual = pos.preco_medio
        operacoes = pos.operacoes.all().order_by("data")
        for op in operacoes:
            if op.evento == "aplicacao" and op.quantidade > 0:
                # Compra: atualiza preço médio pela fórmula pura (P3)
                preco_unitario = op.valor / op.quantidade
                pm_atual = novo_preco_medio(
                    preco_medio_atual=pm_atual,
                    quantidade_atual=qtd_atual,
                    preco_nova_compra=preco_unitario,
                    quantidade_nova=op.quantidade,
                )
                qtd_atual += op.quantidade
            elif op.evento == "venda" and op.quantidade > 0:
                # Venda: preço médio de quem vende não muda (fato de custo)
                qtd_atual -= op.quantidade

        # P&L: sem preço de mercado nesta view (será preenchido quando houver série de preço)
        # Por enquanto, retorna custo total e posição sem P&L calculado
        custo_total = qtd_atual * pm_atual

        posicoes_data.append(
            {
                "ativo": pos.ativo,
                "classe": pos.classe,
                "quantidade": _num(qtd_atual),
                "preco_medio": _num(pm_atual),
                "custo_total": _num(custo_total),
                "moeda": pos.moeda,
                "instituicao": pos.instituicao,
                "operacoes_count": operacoes.count(),
            }
        )
        total_geral += custo_total

    # Pesos atuais vs. política
    politicas = Politica.objects.all()
    pesos = []
    for pol in politicas:
        # Calcular peso atual da classe
        valor_classe = sum(
            Decimal(str(p["custo_total"]))
            for p in posicoes_data
            if p["classe"] == pol.classe
        )
        peso_atual = (valor_classe / total_geral * 100) if total_geral > 0 else _ZERO

        pesos.append(
            {
                "classe": pol.classe,
                "peso_alvo": _num(pol.peso_alvo),
                "faixa_min": _num(pol.faixa_min),
                "faixa_max": _num(pol.faixa_max),
                "peso_atual": _num(peso_atual),
                "dentro_faixa": bool(pol.faixa_min <= peso_atual <= pol.faixa_max),
            }
        )

    return Response(
        {
            "as_of": hoje,
            "total_posicoes": len(posicoes_data),
            "custo_total_geral": _num(total_geral),
            "posicoes": posicoes_data,
            "pesos_vs_politica": pesos,
            "pnl_total": None,  # Requer preço de mercado — será implementado quando houver série de preço
            "pnl_total_pct": None,
        }
    )


@api_view(["POST"])
def operacao_create(request):
    """POST /carteira/operacoes/ — registra uma operação de carteira.

    Valida:
    - evento (aplicacao, resgate, venda, distribuicao, beneficio, amortizacao)
    - data (ISO-8601)
    - valor (positivo)
    - quantidade (para operações com preço médio)

    Não calcula preço médio aqui — apenas grava. O cálculo acontece na leitura
    (GET /carteira/resumo/) usando analise/calculos.py (princípio P3).
    """
    dados = request.data if isinstance(request.data, dict) else {}

    # Validações obrigatórias
    obrigatorios = {
        "evento": dados.get("evento"),
        "data": dados.get("data"),
        "valor": dados.get("valor"),
    }
    faltando = [campo for campo, valor in obrigatorios.items() if valor in (None, "")]
    if faltando:
        return _erro(
            f"{faltando[0]}: campo obrigatório ausente",
            "Informe evento, data e valor da operação.",
        )

    # Validar evento
    eventos_validos = {"aplicacao", "resgate", "venda", "distribuicao", "beneficio", "amortizacao"}
    if dados["evento"] not in eventos_validos:
        return _erro(
            f"evento: {dados['evento']!r} não é válido",
            f"Use um de: {', '.join(sorted(eventos_validos))}.",
        )

    # Validar data
    try:
        data_operacao = date.fromisoformat(str(dados["data"]))
    except ValueError:
        return _erro(
            f"data: {dados['data']!r} não está em formato AAAA-MM-DD",
            "Use o formato ISO-8601 (ex: 2026-10-28).",
        )

    # Validar valor
    try:
        valor = Decimal(str(dados["valor"]))
        if valor <= _ZERO:
            return _erro(
                f"valor: precisa ser positivo (recebido {valor})",
                "Informe um valor maior que zero.",
            )
    except Exception:
        return _erro(
            f"valor: {dados['valor']!r} não é um número válido",
            "Use formato numérico (ex: 2400.00).",
        )

    # Buscar posição (opcional — pode ser operação avulsa)
    posicao = None
    if dados.get("posicao_id"):
        try:
            posicao = Posicao.objects.get(id=dados["posicao_id"])
        except Posicao.DoesNotExist:
            return _erro(
                f"posicao_id: {dados['posicao_id']} não existe",
                "Consulte GET /carteira/ para ver posições válidas.",
                status.HTTP_404_NOT_FOUND,
            )

    # Criar operação
    operacao = Operacao.objects.create(
        posicao=posicao,
        evento=dados["evento"],
        data=data_operacao,
        valor=valor,
        quantidade=Decimal(str(dados.get("quantidade", 0))),
        base_de_calculo=dados.get("base_de_calculo", ""),
        aliquota_ir=Decimal(str(dados.get("aliquota_ir", 0))),
        ir_ja_retido=Decimal(str(dados.get("ir_ja_retido", 0))),
        iof=Decimal(str(dados.get("iof", 0))),
        observacao=dados.get("observacao", ""),
    )

    serializer = OperacaoSerializer(operacao)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
