#!/usr/bin/env python3
"""
Script de ingestão de dividendos e balanços — usa models reais de market_data.

Este script:
1. Configura Django (settings.dev)
2. Verifica fontes existentes (Yahoo Finance, Investing.com)
3. Faz fetch de exemplo de dividendos (código fictício — sem request real)
4. Insere observações se não existirem (regra R1 — append-only)
5. Registra fetch_log com status e itens (regra R7)
6. Registra bloqueio se licença não permitir (regra R8/R11)
"""
import os
import sys
import json
import base64
import hashlib
import datetime
from pathlib import Path

# Configura Django antes de qualquer import de models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "investimentos_project.settings.dev")
import django
django.setup()

from django.utils import timezone
from investimentos.market_data.models import Source, Serie, Observation, RawPayload, FetchLog


def sha256_payload(payload_text: str) -> str:
    """Gera hash sha256 do payload bruto para auditoria (regra R9)."""
    return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()


def registrar_fetch_log(source: Source, dia: datetime.date, endpoint: str,
                        status: str, itens: int, latencia: str = "n/a"):
    """Registra log de fetch (regra R7)."""
    FetchLog.objects.create(
        source=source,
        dia=dia,
        endpoint=endpoint,
        status=status,
        itens=itens,
        latencia=latencia,
    )


def salvar_payload_bruto(serie: Serie, payload_text: str, url_origem: str):
    """Salva payload bruto para auditoria e reprocessamento (regra R9)."""
    RawPayload.objects.create(
        serie=serie,
        periodo="",
        url=url_origem,
        resposta_bruta=payload_text,
    )


def inserir_observacao(serie: Serie, data: datetime.date, valor: float,
                       unidade: str = "") -> Observation | None:
    """Insere observação se não existir (regra R1 — append-only)."""
    existe = Observation.objects.filter(serie=serie, data=data).exists()
    if existe:
        print(f"  ⊘ Observação já existe para {serie.ativo} {data} — não sobrescreve (R1)")
        return None

    obs = Observation(
        serie=serie,
        data=data,
        valor=valor,
        unidade=unidade,
        payload_hash=sha256_payload(f"{data.isoformat()}:{valor}:{unidade}"),
    )
    obs.save()
    print(f"  ✓ Observação inserida: {serie.ativo} {data} = {valor} {unidade}")
    return obs


def fetch_dividendos_yahoo(serie: Serie, data_inicial: datetime.date, data_final: datetime.date):
    """Fetch de dividendos do Yahoo Finance (exemplo — sem request real).

    Em produção: usar a API do Yahoo Finance (símbolo .<ticker>) com
    rastreio de dividendos. Licença: uso pessoal/educacional, comercial proibido
    (regra R8). Cota limitada por IP (regra R7).
    """
    print(f"\n--- Fetch Yahoo Finance dividendos ({serie.ativo}) ---")
    print(f"  Período: {data_inicial} → {data_final} (regra R4 — gap calculado antes)")

    # Verifica se já existe observação para o período (para não duplicar)
    existentes = Observation.objects.filter(
        serie=serie,
        data__gte=data_inicial,
        data__lte=data_final,
    ).count()
    if existentes > 0:
        print(f"  ⚠ {existentes} observações já existem — recalculando gap...")
        # Em produção: calcular gap real (data_final - max(data existente))
        gap = data_final - data_inicial
        print(f"  Gap estimado: {gap.days} dias (a confirmar)")

    # Simulação de fetch (sem request real, sem chave em ambiente)
    print("  ⚠ Nenhum fetch real — sem chave/tested no ambiente (R6 — chave só em .env)")
    print("  → Verificar se BRAPI_API_KEY ou outra chave está no .env antes de fetch")
    return []  # Retorna lista vazia em produção (a ser implementado)


def fetch_balanco_investing(serie: Serie, data: datetime.date):
    """Fetch de balanço do Investing.com (exemplo — sem request real).

    Em produção: usar a API do Investing.com (gráfico financials) com
    cadastro grátis (exige chave). Licença: uso pessoal, redistribution proibido
    (regra R8). Cota: 80 req/dia free tier (regra R7).
    """
    print(f"\n--- Fetch Investing.com balanço ({serie.ativo}) ---")
    print(f"  Data: {data} (regra R4 — gap calculado antes)")

    existe = Observation.objects.filter(serie=serie, data=data).exists()
    if existe:
        print(f"  ⊘ Observação já existe para {serie.ativo} {data} — não sobrescreve (R1)")
        return None

    print("  ⚠ Nenhum fetch real — sem chave/tested no ambiente (R6 — chave só em .env)")
    print("  → Verificar se EIA_API_KEY ou outra chave está no .env antes de fetch")
    return None


def main():
    print("=" * 60)
    print("Script de ingressão de dividendos e balanços")
    print("=" * 60)
    print(f"Início: {timezone.now()}")
    print()

    # Configura Django (porque roda fora do manage.py)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "investimentos_project.settings.dev")
    import django
    django.setup()

    from investimentos.market_data.models import Source, Serie, Observation, RawPayload, FetchLog
    from investimentos.market_data.models import (
        TIPO_API, TIPO_ARQUIVO, TIPO_MANUAL,
        FREQUENCIA_CHOICES,
    )

    hoje = timezone.now().date()
    hoje_str = hoje.isoformat()

    # Verifica se existem fontes no banco
    fontes_existentes = Source.objects.all()
    print(f"Fontes existentes: {list(fontes_existentes)}")
    if not fontes_existentes:
        print("\n⚠ Nenhuma fonte encontrada no banco.")
        print("→ Registre fontes primeiro (ex.: Source(nome='Yahoo Finance', tipo='api', ...)")
        print("→ Ou use manage.py para criar fontes de exemplo")
        return

    # Busca fontes específicas
    yahoo_source = Source.objects.filter(nome__icontains="yahoo", tipo=TIPO_API).first()
    investing_source = Source.objects.filter(nome__icontains="investing", tipo=TIPO_API).first()

    # Exemplos de séries
    seriel_lista = Serie.objects.all()
    print(f"\nSéries existentes: {list(serie_lista)}")
    print()

    # Para cada série, tenta fazer ingestão
    for serie in serie_lista:
        print(f"\n{'='*40}")
        print(f"Série: {serie.nome} ({serie.ativo})")
        print(f"{'='*40}")

        if not yahoo_source and not investing_source:
            print("  ⚠ Nenhuma fonte de exemplo disponível — registrar apenas log de erro")
            registrar_fetch_log(
                source=serie.source if hasattr(serie, 'source') else None,
                dia=hoje,
                endpoint="ingest_dividendos_balances",
                status="sem_fonte",
                itens=0,
                latencia="n/a",
            )
            continue

        try:
            # Tenta fetch de dividendos (simulado)
            if yahoo_source:
                resultado = fetch_dividendos_yahoo(
                    serie=serie,
                    data_inicial=hoje - datetime.timedelta(days=365),
                    data_final=hoje,
                )
                if resultado:
                    salvar_payload_bruto(serie, json.dumps(resultado), yahoo_source.url_base)
                    registrar_fetch_log(yahoo_source, hoje, "ingest_dividendos_yahoo",
                                       len(resultado), "0.5s")
                else:
                    registrar_fetch_log(yahoo_source, hoje, "ingest_dividendos_yahoo",
                                       itens=0, latencia="n/a")

            # Tenta fetch de balanços (simulado)
            if investing_source:
                resultado_balanco = fetch_balanco_investing(serie, hoje)
                if resultado_balanco:
                    salvar_payload_bruto(serie, json.dumps(resultado_balanco),
                                        investing_source.url_base)
                    registrar_fetch_log(investing_source, hoje, "fetch_balanco_investing",
                                       itens=len(resultado_balanco), latencia="0.3s")
                else:
                    registrar_fetch_log(investing_source, hoje, "fetch_balanco_investing",
                                       itens=0, latencia="n/a")
        except Exception as e:
            print(f"  ✗ ERRO durante ingestão: {str(e)}")
            registrar_fetch_log(
                source=serie.source if hasattr(serie, 'source') else None,
                dia=hoje,
                endpoint="ingest_dividendos_balances",
                status="erro",
                itens=0,
                latencia="n/a",
            )
            print(f"  → Erro registrado no fetch_log (R11 — bloqueio declarado)")

    print("\n" + "=" * 60)
    print("Ingestão concluída.")
    print(f"Fim: {timezone.now()}")
    print("=" * 60)
    print("Log de fetch registrado para todas as fontes.")
    print("Regra R12: escrita só por fontes-de-dados (never via view or API).")


if __name__ == "__main__":
    main()
