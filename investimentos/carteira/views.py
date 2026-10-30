"""Views do app carteira — API v1 /api/v1/carteira/.

Contrato da API (specs/aplicacao.md):
- GET  /carteira/classes/ — esquema das classes de investimento (gera o formulário)
- GET  /carteira/posicoes/ · POST /carteira/posicoes/ — cadastro manual de posição
- GET  /carteira/resumo/ — posições, custo médio, pesos atuais vs política, P&L com as_of
- POST /carteira/operacoes/ — registrar operação (evento, data, custos, IR, base de cálculo)
- GET  /carteira/ — lista de posições

Regra R4: aqui **não se calcula** — custo médio vem de `analise/calculos.py`, a
validação de atributos e custos de `carteira/validacao.py` (função pura), e a
view só monta o envelope datado da R2 (valor + unidade + data_base).
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from investimentos.analise.calculos import novo_preco_medio

from .esquemas import CLASSES, CUSTOS, EVENTOS, Campo, Classe
from .models import Operacao, Politica, Posicao
from .serializers import OperacaoSerializer, PosicaoSerializer
from .validacao import (
    efeito_financeiro,
    evento_permitido,
    total_custos,
    validar_atributos,
    validar_custos,
)

_EXP = Decimal("0.0001")
_ZERO = Decimal("0")

EVENTOS_VALIDOS = {
    "aplicacao",
    "resgate",
    "venda",
    "distribuicao",
    "beneficio",
    "amortizacao",
    "provento",
    "ir_pago",
    "taxa",
    "encerramento",
}


def _num(valor: Decimal, exp: Decimal = _EXP) -> float:
    """Arredonda na borda e devolve float só para o JSON (cálculo é Decimal — R5)."""
    return float(valor.quantize(exp, rounding=ROUND_HALF_UP))


def _erro(mensagem: str, sugestao: str, codigo=status.HTTP_422_UNPROCESSABLE_ENTITY):
    """Envelope de erro padrão da API: {erro, campo, sugestao}."""
    campo = mensagem.split(":", 1)[0].strip() if ":" in mensagem else "entrada"
    return Response({"erro": mensagem, "campo": campo, "sugestao": sugestao}, status=codigo)


def _erro_validacao(erros: list[dict]):
    """422 com todos os erros de validação, mantendo o envelope padrão."""
    primeiro = erros[0]
    return Response(
        {
            "erro": f"{primeiro['campo']}: {primeiro['mensagem']}",
            "campo": primeiro["campo"],
            "sugestao": primeiro["sugestao"],
            "erros": erros,
        },
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def _numero(valor) -> Decimal | None:
    """Converte entrada numérica simples; `None` quando não é número."""
    if valor in (None, ""):
        return None
    try:
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _campo_json(item: Campo) -> dict:
    return {
        "nome": item.nome,
        "rotulo": item.rotulo,
        "tipo": item.tipo,
        "obrigatorio": item.obrigatorio,
        "unidade": item.unidade,
        "opcoes": list(item.opcoes),
        "ajuda": item.ajuda,
    }


def _classe_json(item: Classe) -> dict:
    return {
        "nome": item.nome,
        "rotulo": item.rotulo,
        "nota": item.nota,
        "campos": [_campo_json(campo) for campo in item.campos],
        "eventos": [{"nome": evento, "rotulo": EVENTOS.get(evento, evento)} for evento in item.eventos],
    }


@api_view(["GET"])
def classes_list(request):
    """GET /carteira/classes/ — esquema que monta o formulário mutável no front.

    O React não conhece CDB, FII ou ouro: ele desenha os campos que esta resposta
    descreve. Classe nova no backend aparece no formulário sem tocar no front (P4).
    """
    return Response(
        {
            "classes": [_classe_json(item) for item in CLASSES.values()],
            "custos": [_campo_json(item) for item in CUSTOS],
            "eventos": EVENTOS,
        }
    )


@api_view(["GET", "POST"])
def posicoes_list_create(request):
    """GET lista posições; POST cadastra posição manual (com atributos da classe)."""
    if request.method == "GET":
        return Response(PosicaoSerializer(Posicao.objects.all(), many=True).data)

    dados = request.data if isinstance(request.data, dict) else {}
    ativo = str(dados.get("ativo") or "").strip()
    classe_nome = str(dados.get("classe") or "acoes").strip()

    if not ativo:
        return _erro("ativo: campo obrigatório ausente", "Informe o nome ou o ticker do ativo.")

    atributos, erros = validar_atributos(classe_nome, dados.get("atributos"))
    if erros:
        return _erro_validacao(erros)

    quantidade = _numero(dados.get("quantidade")) or _ZERO
    preco_medio = _numero(dados.get("preco_medio")) or _ZERO
    if quantidade < _ZERO or preco_medio < _ZERO:
        return _erro("quantidade: não pode ser negativa", "Informe quantidade e preço médio maiores ou iguais a zero.")

    data_entrada = None
    if dados.get("data_entrada") not in (None, ""):
        try:
            data_entrada = date.fromisoformat(str(dados["data_entrada"]))
        except ValueError:
            return _erro("data_entrada: não está em AAAA-MM-DD", "Use o formato ISO-8601 (ex: 2026-10-29).")

    posicao = Posicao.objects.create(
        owner=request.user if request.user.is_authenticated else None,
        ativo=ativo[:300],
        classe=classe_nome,
        quantidade=quantidade,
        preco_medio=preco_medio,
        moeda=str(dados.get("moeda") or "BRL")[:10],
        instituicao=str(dados.get("instituicao") or "")[:200],
        atributos=atributos,
        data_entrada=data_entrada,
    )
    return Response(PosicaoSerializer(posicao).data, status=status.HTTP_201_CREATED)


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
            elif op.evento in {"venda", "resgate", "amortizacao", "encerramento"} and op.quantidade > 0:
                # Saída: preço médio de quem vende não muda (fato de custo)
                qtd_atual -= op.quantidade

        custo_total = qtd_atual * pm_atual

        posicoes_data.append(
            {
                "id": pos.id,
                "ativo": pos.ativo,
                "classe": pos.classe,
                "quantidade": _num(qtd_atual),
                "preco_medio": _num(pm_atual),
                "custo_total": _num(custo_total),
                "moeda": pos.moeda,
                "instituicao": pos.instituicao,
                "status": pos.status,
                "data_entrada": pos.data_entrada.isoformat() if pos.data_entrada else None,
                "data_encerramento": pos.data_encerramento.isoformat() if pos.data_encerramento else None,
                "atributos": pos.atributos,
                "operacoes_count": operacoes.count(),
            }
        )
        total_geral += custo_total

    # Pesos atuais vs. política
    politicas = Politica.objects.all()
    pesos = []
    for pol in politicas:
        valor_classe = sum(
            Decimal(str(p["custo_total"])) for p in posicoes_data if p["classe"] == pol.classe
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

    Valida evento (contra os eventos da classe da posição), data ISO-8601, valor
    positivo e custos discriminados. Grava `custos`, `custo_total` e
    `valor_efeito` calculados por função pura — a view não faz conta (R4).

    Não calcula preço médio aqui — apenas grava. O cálculo acontece na leitura
    (GET /carteira/resumo/) usando analise/calculos.py (princípio P3).
    """
    dados = request.data if isinstance(request.data, dict) else {}

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

    if dados["evento"] not in EVENTOS_VALIDOS:
        return _erro(
            f"evento: {dados['evento']!r} não é válido",
            f"Use um de: {', '.join(sorted(EVENTOS_VALIDOS))}.",
        )

    try:
        data_operacao = date.fromisoformat(str(dados["data"]))
    except ValueError:
        return _erro(
            f"data: {dados['data']!r} não está em formato AAAA-MM-DD",
            "Use o formato ISO-8601 (ex: 2026-10-28).",
        )

    try:
        valor = Decimal(str(dados["valor"]))
    except (InvalidOperation, ValueError):
        return _erro(
            f"valor: {dados['valor']!r} não é um número válido",
            "Use formato numérico (ex: 2400.00).",
        )
    if valor <= _ZERO:
        return _erro(f"valor: precisa ser positivo (recebido {valor})", "Informe um valor maior que zero.")

    posicao = None
    if dados.get("posicao_id"):
        try:
            posicao = Posicao.objects.get(id=dados["posicao_id"])
        except Posicao.DoesNotExist:
            return _erro(
                f"posicao_id: {dados['posicao_id']} não existe",
                "Consulte GET /api/v1/carteira/posicoes/ para ver posições válidas.",
                status.HTTP_404_NOT_FOUND,
            )

    # Evento precisa fazer sentido para a classe (provento não existe em CDB).
    classe_nome = posicao.classe if posicao is not None else str(dados.get("classe") or "acoes")
    if not evento_permitido(classe_nome, str(dados["evento"])):
        return _erro(
            f"evento: {dados['evento']!r} não se aplica à classe {classe_nome!r}",
            f"Eventos de {classe_nome}: {', '.join(CLASSES[classe_nome].eventos) if classe_nome in CLASSES else '-'}.",
        )

    custos, erros_custos = validar_custos(dados.get("custos"))
    if erros_custos:
        return _erro_validacao(erros_custos)

    custo_total = total_custos(custos)
    valor_efeito = efeito_financeiro(str(dados["evento"]), valor, custos)

    operacao = Operacao.objects.create(
        posicao=posicao,
        evento=dados["evento"],
        data=data_operacao,
        valor=valor,
        quantidade=Decimal(str(dados.get("quantidade", 0))),
        base_de_calculo=dados.get("base_de_calculo", ""),
        aliquota_ir=Decimal(str(dados.get("aliquota_ir", 0))),
        ir_ja_retido=Decimal(str(custos.get("ir", dados.get("ir_ja_retido", 0)))),
        iof=Decimal(str(custos.get("iof", dados.get("iof", 0)))),
        custos=custos,
        custo_total=custo_total,
        valor_efeito=valor_efeito,
        observacao=dados.get("observacao", ""),
    )

    # Encerramento dá baixa na posição (o histórico de operações continua).
    if dados["evento"] == "encerramento" and posicao is not None:
        posicao.status = "encerrada"
        posicao.data_encerramento = data_operacao
        posicao.save(update_fields=["status", "data_encerramento"])

    corpo = OperacaoSerializer(operacao).data
    corpo["custo_total"] = _num(custo_total, Decimal("0.01"))
    corpo["valor_efeito"] = _num(valor_efeito, Decimal("0.01"))
    return Response(corpo, status=status.HTTP_201_CREATED)
