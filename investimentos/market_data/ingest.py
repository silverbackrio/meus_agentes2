"""Ingestão de dados — janela de gap, parse da resposta e gravação idempotente.

Este módulo é a metade "fina" da ingestão (regra R5 de `specs/fontes-de-dados.md`):
o **transporte** (HTTP) fica no comando `manage.py ingest`, e aqui ficam o que
precisa ser testado sem rede:

- ``janela_de_ingestão`` — calcula **só o gap** (R4): do maior `data` guardado até
  a data pedida; série vazia cai no backfill completo, que acontece uma vez.
- ``parsear_ptax_periodo`` — transforma o JSON do BCB em linhas datadas, sem
  dependência de terceiro (P5: stdlib `json` basta).
- ``persistir_observacoes`` — gravação append-only com a chave de idempotência
  ``(série, data)`` (R1/R2): igual não duplica, diferente **não sobrescreve** —
  vira divergência para decisão humana.

Nada aqui é chamado por view: escrita de dado de mercado é só via CLI (R12).
"""

import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Max

from investimentos.market_data.models import Observation

ZEROS = {"criadas": 0, "iguais": 0, "divergentes": 0}


def janela_de_ingestao(serie, ate: date, de: date | None = None) -> tuple[date, date]:
    """Intervalo que **falta** buscar para a série até `ate` (regra R4).

    Com dado guardado, começa um dia depois da maior `data` — período já coberto
    nunca é baixado de novo. Sem dado, o backfill começa em `de` (obrigatório
    nesse caso, para não tentar baixar a história inteira sem querer).
    """
    maxima = Observation.objects.filter(serie=serie).aggregate(maior=Max("data"))["maior"]

    if maxima is None:
        if de is None:
            raise ValueError(
                "janela: série sem histórico — informe --de para o backfill completo"
            )
        inicio = de
    else:
        inicio = maxima + timedelta(days=1)

    if inicio > ate:
        return inicio, ate  # vazio: já coberto até `ate` (o chamador trata)
    return inicio, ate


def parsear_ptax_periodo(texto_bruto: str) -> list[tuple[date, Decimal, Decimal]]:
    """Lê a resposta da API PTAX do BCB e devolve `(data, compra, venda)`.

    Aceita tanto o formato ``{"value": [...]}`` da API Olinda quanto uma lista
    pura. Linha sem valor ou com número inválido é **pulada e relatada** pelo
    chamador — nunca vira zero silencioso (regra R11).

    Exemplo de linha: ``{"cotacaoCompra": 3.2632, "cotacaoVenda": 3.2638,
    "dataHoraCotacao": "2016-09-09 13:14:00.885"}``.
    """
    dados = json.loads(texto_bruto)
    linhas = dados["value"] if isinstance(dados, dict) else dados

    pontos: list[tuple[date, Decimal, Decimal]] = []
    for linha in linhas:
        try:
            data = date.fromisoformat(str(linha["dataHoraCotacao"])[:10])
            compra = Decimal(str(linha["cotacaoCompra"]))
            venda = Decimal(str(linha["cotacaoVenda"]))
        except (KeyError, ValueError, InvalidOperation):
            continue
        pontos.append((data, compra, venda))

    pontos.sort(key=lambda ponto: ponto[0])
    return pontos


def persistir_observacoes(serie, pontos, *, usar_venda: bool = True) -> dict:
    """Grava `(data, valor)` na série sem duplicar e sem sobrescrever (R1/R2).

    Retorna contagem em ``{"criadas", "iguais", "divergentes"}`` para o comando
    imprimir e para o    `fetch_log` registrar. Divergência = já existe uma linha
    para a data com valor diferente: a antiga fica intacta (fato passado é
    imutável) e a contagem sobe — decisão de corrigir é humana.
    """
    contagem = dict(ZEROS)
    for ponto in pontos:
        data, valor = ponto[0], (ponto[2] if usar_venda else ponto[1])
        existente = Observation.objects.filter(serie=serie, data=data).first()

        if existente is None:
            Observation.objects.create(
                serie=serie,
                data=data,
                valor=valor,
                unidade=serie.unidade,
                payload_hash="",
            )
            contagem["criadas"] += 1
        elif existente.valor == valor:
            contagem["iguais"] += 1
        else:
            contagem["divergentes"] += 1

    return contagem
