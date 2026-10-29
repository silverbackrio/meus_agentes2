"""Views do app market_data — API v1 /api/v1/series/ e /api/v1/dados/.

Passo 2 da `specs/aplicacao.md`: leitura do banco histórico local com cobertura,
gaps e proveniência. Três princípios marcam este arquivo:

- **R3 — leitura local primeiro**: nada aqui faz chamada de rede; `as_of` diz de
  quando é o dado que você está vendo.
- **R4 (da fontes-de-dados) — gap, não escopo**: os intervalos faltantes vêm do
  módulo puro `gaps.py`, que é quem a ingestão também usa.
- **R2/R5 — envelope datado**: todo número sai com `valor`, `unidade` e
  `data_base`, e o dinheiro é `Decimal` no banco, `float` só na borda do JSON.

Escrita não existe neste arquivo: observação só entra pelo script de ingestão
(R12 de `specs/fontes-de-dados.md`).
"""

import csv
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from io import StringIO

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .gaps import calcular_gaps, cobertura, datas_esperadas
from .models import FetchLog, Serie
from .serializers import SerieSerializer

_EXP = Decimal("0.0001")  # arredondamento só na borda (R5)


def _erro(mensagem: str, sugestao: str, codigo=status.HTTP_422_UNPROCESSABLE_ENTITY):
    """Envelope de erro padrão da API: `{erro, campo, sugestao}` (aplicacao.md)."""
    campo = mensagem.split(":", 1)[0].strip() if ":" in mensagem else "entrada"
    return Response({"erro": mensagem, "campo": campo, "sugestao": sugestao}, status=codigo)


def _data(param, padrao=None) -> date:
    """Converte parâmetro ISO-8601 em `date`, com erro nomeando o campo."""
    if param in (None, ""):
        if padrao is None:
            raise ValueError("periodo: informe 'de' e 'ate' em ISO (AAAA-MM-DD)")
        return padrao
    try:
        return date.fromisoformat(str(param))
    except ValueError as exc:
        raise ValueError(f"periodo: {param!r} não está em formato AAAA-MM-DD") from exc


def _periodo(dados, serie: Serie) -> tuple[date, date]:
    """Período pedido, com padrão = tudo o que a série já tem guardado (R3).

    Série vazia cai no padrão "hoje": a resposta vem vazia com `sem_dado`, que é
    o comportamento da R11 — relatar a lacuna em vez de inventar número.
    """
    datas = list(serie.observations.values_list("data", flat=True))
    padrao_de = min(datas) if datas else date.today()
    padrao_ate = max(datas) if datas else date.today()
    de = _data(dados.get("de"), padrao=padrao_de)
    ate = _data(dados.get("ate"), padrao=padrao_ate)
    if de > ate:
        raise ValueError(f"periodo: 'de' ({de}) não pode ser posterior a 'ate' ({ate})")
    return de, ate


def _proveniencia(serie: Serie) -> dict:
    """Fonte + licença + URL, sempre junto do dado (R9)."""
    fonte = serie.source
    return {
        "nome": fonte.nome,
        "tipo": fonte.tipo,
        "url_base": fonte.url_base,
        "licenca": fonte.licenca,
        "cota": fonte.cota,
    }


def _cobertura_da_serie(serie: Serie, de: date, ate: date) -> dict:
    """Cobertura + gaps da série no período, com fração arredondada na borda."""
    datas = list(serie.observations.values_list("data", flat=True))
    resumo = cobertura(datas, de, ate, serie.frequencia)
    resumo["fracao"] = float(resumo["fracao"].quantize(_EXP, rounding=ROUND_HALF_UP))
    resumo["pct"] = round(resumo["fracao"] * 100, 2)
    resumo["de"] = de.isoformat()
    resumo["ate"] = ate.isoformat()
    resumo["gaps"] = [[a.isoformat(), b.isoformat()] for a, b in calcular_gaps(datas, de, ate, serie.frequencia)]
    resumo["primeira"] = resumo["primeira"].isoformat() if resumo["primeira"] else None
    resumo["ultima"] = resumo["ultima"].isoformat() if resumo["ultima"] else None
    return resumo


@api_view(["GET"])
def series_list(request):
    """GET /series/?ativo=&moeda=&frequencia=&de=&ate= — séries com cobertura e `as_of`."""
    filtros = {}
    for parametro, campo in (("ativo", "ativo__icontains"), ("moeda", "moeda"), ("frequencia", "frequencia")):
        valor = request.query_params.get(parametro)
        if valor:
            filtros[campo] = valor

    series = Serie.objects.filter(**filtros).select_related("source").order_by("ativo", "codigo")
    try:
        corpo = []
        for serie in series:
            de, ate = _periodo(request.query_params, serie)
            dados = SerieSerializer(serie).data
            dados["cobertura"] = _cobertura_da_serie(serie, de, ate)
            dados["as_of"] = dados["cobertura"]["ultima"]
            dados["observacoes"] = serie.observations.count()
            corpo.append(dados)
    except ValueError as exc:
        return _erro(str(exc), "Use AAAA-MM-DD e 'de' menor ou igual a 'ate'.")

    # Um único relógio no topo: de quando é o banco como um todo (GLOSSARY).
    as_of_geral = max((d["as_of"] for d in corpo if d["as_of"]), default=None)
    return Response({"as_of": as_of_geral, "total": len(corpo), "series": corpo})


@api_view(["GET"])
def serie_observacoes(request, serie_id: int):
    """GET /series/{id}/observacoes/?de=&ate= — pontos + gaps + proveniência."""
    serie = Serie.objects.filter(id=serie_id).select_related("source").first()
    if serie is None:
        return _erro(
            f"serie: id {serie_id} não existe",
            "Consulte /api/v1/series/ para ver os ids válidos.",
            status.HTTP_404_NOT_FOUND,
        )

    try:
        de, ate = _periodo(request.query_params, serie)
        esperadas = list(datas_esperadas(de, ate, serie.frequencia))
    except ValueError as exc:
        return _erro(str(exc), "Use AAAA-MM-DD e uma frequência válida da série.")

    pontos = [
        [obs.data.isoformat(), float(obs.valor)]
        for obs in serie.observations.filter(data__gte=de, data__lte=ate).order_by("data")
    ]
    datas = [date.fromisoformat(p[0]) for p in pontos]
    gaps = [[a.isoformat(), b.isoformat()] for a, b in calcular_gaps(datas, de, ate, serie.frequencia)]

    return Response(
        {
            "serie": SerieSerializer(serie).data,
            "fonte": _proveniencia(serie),
            "periodo": {"de": de.isoformat(), "ate": ate.isoformat()},
            "as_of": pontos[-1][0] if pontos else None,
            "unidade": serie.unidade,
            "frequencia": serie.frequencia,
            "pontos": pontos,
            "esperadas": len(esperadas),
            "gaps": gaps,
            "sem_dado": not pontos,
        }
    )


@api_view(["GET"])
def serie_export_csv(request, serie_id: int):
    """GET /series/{id}/export.csv — CSV com fonte e data-base em cada linha (R10)."""
    serie = Serie.objects.filter(id=serie_id).select_related("source").first()
    if serie is None:
        return _erro(
            f"serie: id {serie_id} não existe",
            "Consulte /api/v1/series/ para ver os ids válidos.",
            status.HTTP_404_NOT_FOUND,
        )

    buffer = StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(
        ["data", "valor", "unidade", "serie", "codigo_fonte", "fonte", "licenca", "fetched_at"]
    )
    for obs in serie.observations.order_by("data"):
        escritor.writerow(
            [
                obs.data.isoformat(),
                str(obs.valor),
                serie.unidade,
                serie.nome,
                serie.codigo,
                serie.source.nome,
                serie.source.licenca,
                obs.fetched_at.isoformat() if obs.fetched_at else "",
            ]
        )

    resposta = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    resposta["Content-Disposition"] = f'attachment; filename="serie_{serie.id}_{serie.codigo}.csv"'
    return resposta


@api_view(["GET"])
def dados_status(request):
    """GET /dados/status — cobertura por série, `fetch_log` do dia e cota consumida."""
    hoje = date.today()
    series = []
    as_of_geral = None

    for serie in Serie.objects.select_related("source").order_by("ativo", "codigo"):
        de, ate = _periodo(request.query_params, serie)
        cobertura_serie = _cobertura_da_serie(serie, de, ate)
        as_of_geral = max(filter(None, [as_of_geral, cobertura_serie["ultima"]]), default=None)
        series.append(
            {
                "id": serie.id,
                "ativo": serie.ativo,
                "codigo": serie.codigo,
                "frequencia": serie.frequencia,
                "moeda": serie.moeda,
                "fonte": _proveniencia(serie),
                "cobertura": cobertura_serie,
                "as_of": cobertura_serie["ultima"],
            }
        )

    logs_do_dia = [
        {
            "fonte": log.source.nome,
            "dia": log.dia.isoformat(),
            "endpoint": log.endpoint,
            "status": log.status,
            "itens": log.itens,
            "latencia": log.latencia,
        }
        for log in FetchLog.objects.filter(dia=hoje).select_related("source").order_by("dia")
    ]

    # R7: cota contada por fonte no dia, para o script abortar antes de estourar.
    cota = []
    fontes = {serie.source for serie in Serie.objects.select_related("source")}
    for fonte in sorted(fontes, key=lambda f: f.nome):
        usadas = FetchLog.objects.filter(source=fonte, dia=hoje).count()
        cota.append(
            {
                "fonte": fonte.nome,
                "cota": fonte.cota,
                "usadas_hoje": usadas,
                "restantes": (fonte.cota - usadas) if fonte.cota is not None else None,
            }
        )

    return Response(
        {
            "as_of": as_of_geral,
            "banco_atualizado_em": as_of_geral,
            "series": series,
            "fetch_log": logs_do_dia,
            "cota": cota,
        }
    )
