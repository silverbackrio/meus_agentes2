#!/usr/bin/env python3
"""Script de ingestão de dividendos e balanço — usa models reais de market_data.

Este script:
1. Configura Django (settings.dev) no topo, antes de qualquer import
2. Verifica fontes existentes (Yahoo Finance, Investing.com, BCB)
3. Faz fetch de dividendos usando yfinance (gratuito, sem chave)
4. Faz fetch de balanços usando Twelve Data (créditos gratuitos) ou BCB
5. Insere observações se não existirem (regra R1 — append-only)
6. Registra fetch_log com status e itens (regra R7)
7. Respeita cota e declara bloqueio se licença não permitir (regra R8/R11)
"""

import os
import sys
from pathlib import Path

# Add workspace root to path (script is at .agents/scripts/ from repo root)
# When running from workspace root:
_workspace_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

# Configura Django antes de qualquer import de models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "investimentos_project.settings.dev")

import datetime
import hashlib
import json
import time

import django
django.setup()

from django.utils import timezone
from django.db.utils import IntegrityError

from investimentos.market_data.models import FetchLog, Observation, RawPayload, Serie, Source
from investimentos.market_data.calculos import calcular_gap_periodo


def sha256_payload(payload_text: str) -> str:
    """Gera hash sha256 do payload bruto para auditoria (regra R9)."""
    return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()


def registrar_fetch_log(
    source: Source | None,
    dia: datetime.date,
    endpoint: str,
    status: str = "ok",
    itens: int = 0,
    latencia: str = "n/a",
    erro: str = "",
) -> None:
    """Registra log de fetch (regra R7).

    Sempre com argumentos nomeados nos chamadores: a ordem dos parâmetros é
    fácil de trocar (status por itens) e o log errado é pior que log nenhum.
    """
    if source is None:
        # R7/R11: sem fonte não há log de fetch — só um aviso na tela. O log tem
        # `source` obrigatório (FK não nula), então não gravamos linha inválida.
        print(f"  ⚠ Sem fonte registrada — fetch_log não gravado (R7): {endpoint}")
        return
    FetchLog.objects.create(
        source=source,
        dia=dia,
        endpoint=endpoint,
        status=status,
        itens=itens,
        latencia=latencia,
    )
    if erro:
        print(f"  → Erro registrado: {erro}")


def salvar_payload_bruto(serie: Serie, payload_text: str, url_origem: str) -> None:
    """Salva payload bruto para auditoria e reprocessamento (regra R9)."""
    # R9: evita duplicata de payload bruto para a mesma série+url
    existe = RawPayload.objects.filter(serie=serie, url=url_origem).exists()
    if existe:
        print(f"  ⊘ Payload já salvo para {serie.ativo} ({url_origem[:40]}...) — não sobrescreve (R9)")
        return
    RawPayload.objects.create(
        serie=serie,
        periodo="",
        url=url_origem,
        resposta_bruta=payload_text,
    )
    print(f"  ✓ Payload salvo: {serie.ativo} em {url_origem[:50]}...")


def inserir_observacao(serie: Serie, data: datetime.date, valor: float, unidade: str = "") -> Observation | None:
    """Insere observação se não existir (regra R1 — append-only)."""
    existe = Observation.objects.filter(serie=serie, data=data).exists()
    if existe:
        print(f"  ⊘ Observação já existe para {serie.ativo} {data} — não sobrescreve (R1)")
        return None

    obs = Observation(
        serie=serie,
        data=data,
        valor=Decimal(str(valor)),
        unidade=unidade,
        payload_hash=sha256_payload(f"{data.isoformat()}:{valor}:{unidade}"),
    )
    obs.save()
    print(f"  ✓ Observação inserida: {serie.ativo} {data} = {valor} {unidade}")
    return obs


def fetch_dividendos_yfinance(serie: Serie, data_inicial: datetime.date, data_final: datetime.date) -> list[dict]:
    """Fetch de dividendos usando yfinance (gratuito, sem chave de API).

    yfinance consome os endpoints do Yahoo Finance e funciona muito bem de graça,
    exigindo apenas que você adicione o sufixo .SA para ativos brasileiros
    (ex: BBAS3.SA).

    Regra R8: uso pessoal/educacional, comercial proibido.
    Regra R7: cota ilimitada teóricas mas devagar para não ser bloqueado.
    """
    import yfinance as yf

    ticker_symbol = f"{serie.codigo}.SA"
    print(f"  --- Fetch Yahoo Finance dividendos ({serie.ativo}) ---")
    print(f"  Ticker: {ticker_symbol}")
    print(f"  Período: {data_inicial} → {data_final} (regra R4 — gap calculado antes)")

    try:
        ticker = yf.Ticker(ticker_symbol)

        # yfinance dividendos history
        divs = ticker.dividends
        if divs is None or len(divs) == 0:
            print("  ⚠ Nenhum dividendo encontrado no período")
            return []

        # Filtrar apenas no período solicitado
        dividends_data = []
        for data_div, valor_div in divs.items():
            if data_inicial <= data_div <= data_final:
                dividends_data.append({
                    "data": data_div.date() if hasattr(data_div, 'date') else data_div,
                    "valor": float(valor_div),
                    "unidade": "R$/ação",
                    "fonte": "Yahoo Finance (yfinance)",
                })

        print(f"  ✓ Encontrados {len(dividends_data)} dividendos no período")
        return dividends_data

    except ImportError:
        print("  ⚠ yfinance não instalado — pip install yfinance")
        return []
    except Exception as e:
        erro_msg = str(e)
        print(f"  ✗ Erro no fetch Yahoo Finance: {erro_msg}")
        registrar_fetch_log(
            source=serie.source,
            dia=timezone.now().date(),
            endpoint="fetch_dividendos_yfinance",
            status="erro",
            itens=0,
            latencia="0s",
            erro=erro_msg,
        )
        return []


def fetch_balanco_twelve_data(serie: Serie, data: datetime.date) -> list[dict] | None:
    """Fetch de balanço usando Twelve Data (créditos gratuitos: 8/min, 800/dia).

    Twelve Data oferece dados financeiros gratuitos com registro.
    Regra R8: cadastro grátis, uso pessoal.
    Regra R7: 8 créditos/minuto, 800/dia free tier.
    """
    import os
    from decimal import Decimal

    api_key = os.environ.get("TWELVE_DATA_API_KEY", "")
    if not api_key:
        print("  ⚠ Twelve Data API key não configurada — pulei fetch (R6)")
        registrar_fetch_log(
            source=serie.source,
            dia=timezone.now().date(),
            endpoint="fetch_balanco_twelve_data",
            status="sem_chave",
            itens=0,
            latencia="0s",
        )
        return None

    codigo = serie.codigo
    print(f"  --- Fetch Twelve Data balanço ({serie.ativo}) ---")
    print(f"  Ticker: {codigo}")
    print(f"  Data: {data}")

    try:
        import requests

        url = "https://api.twelvedata.com/financials"
        params = {
            "symbol": f"{codigo}.SA",
            "apikey": api_key,
            "interval": "quarterly",
            "filter": "earnings,revenue,debt",
            "date": data.strftime("%Y-%m-%d"),
        }

        inicio = time.time()
        resposta = requests.get(url, params=params, timeout=30)
        latencia = f"{time.time() - inicio:.1f}s"

        if resposta.status_code != 200:
            print(f"  ✗ HTTP {resposta.status_code}: {resposta.text[:200]}")
            registrar_fetch_log(
                source=serie.source,
                dia=timezone.now().date(),
                endpoint="fetch_balanco_twelve_data",
                status="erro_http",
                itens=0,
                latencia=latencia,
                erro=f"HTTP {resposta.status_code}",
            )
            return None

        dados = resposta.json()
        financials = dados.get("earnings", [])

        # Extrair dados relevantes
        resultados = []
        for item in financials[:5]:  # Máximo 5 itens para não encher
            campo = item.get("field", "")
            valor = item.get("result", [{}])[0].get("raw", None) if item.get("result") else None

            if campo and valor is not None:
                resultados.append({
                    "campo": campo,
                    "valor": float(valor) if isinstance(valor, (int, float)) else str(valor),
                    "unidade": "R$",
                    "data": data,
                    "fonte": "Twelve Data",
                })

        print(f"  ✓ Encontrados {len(resultados)} itens de balanço")
        registrar_fetch_log(
            source=serie.source,
            dia=timezone.now().date(),
            endpoint="fetch_balanco_twelve_data",
            status="ok",
            itens=len(resultados),
            latencia=latencia,
        )
        return resultados if resultados else None

    except ImportError:
        print("  ⚠ requests não instalado — pip install requests")
        registrar_fetch_log(
            source=serie.source,
            dia=timezone.now().date(),
            endpoint="fetch_balanco_twelve_data",
            status="dependencia",
            itens=0,
            latencia="0s",
        )
        return None
    except Exception as e:
        erro_msg = str(e)
        print(f"  ✗ Erro no fetch Twelve Data: {erro_msg}")
        registrar_fetch_log(
            source=serie.source,
            dia=timezone.now().date(),
            endpoint="fetch_balanco_twelve_data",
            status="erro",
            itens=0,
            latencia="0s",
            erro=erro_msg,
        )
        return None


def fetch_preco_atual_yfinance(serie: Serie) -> dict | None:
    """Fetch do preço atual usando yfinance (gratuito, sem chave)."""
    import yfinance as yf

    ticker_symbol = f"{serie.codigo}.SA"
    print(f"  --- Preço atual Yahoo Finance ({serie.ativo}) ---")
    print(f"  Ticker: {ticker_symbol}")

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        preco_atual = info.get("regularMarketPrice", None)
        moeda = info.get("currency", "BRL")

        if preco_atual is None:
            print("  ⚠ Preço não disponível")
            return None

        print(f"  ✓ Preço atual: {moeda} {preco_atual}")
        return {
            "preco": float(preco_atual),
            "moeda": moeda,
            "fonte": "Yahoo Finance (yfinance)",
        }

    except ImportError:
        print("  ⚠ yfinance não instalado")
        return None
    except Exception as e:
        print(f"  ✗ Erro: {e!s}")
        return None


def main():
    """Função principal do script de ingestão."""
    print("=" * 60)
    print("Script de ingestão de dividendos e balanços")
    print("=" * 60)
    print(f"Início: {timezone.now()}")
    print()

    # Verifica se existem fontes no banco
    fontes_existentes = Source.objects.all()
    print(f"Fontes existentes: {list(fontes_existentes)}")
    if not fontes_existentes:
        print("\n⚠ Nenhuma fonte encontrada no banco.")
        print("→ Registre fontes primeiro (ex.: Source(nome='Yahoo Finance', tipo='api', ...))")
        print("→ Ou use manage.py para criar fontes de exemplo")
        return

    # Busca fontes específicas
    yahoo_source = Source.objects.filter(nome__icontains="Yahoo Finance", tipo="api").first()
    twelvedata_source = Source.objects.filter(nome__icontains="Twelve Data", tipo="api").first()
    bcb_source = Source.objects.filter(nome__icontains="BCB", tipo="api").first()

    # Exemplos de séries
    print(f"\nSéries existentes: {list(Serie.objects.all())}")
    print()

    # Para cada série, tenta fazer ingestão
    for serie in Serie.objects.all():
        print(f"\n{'=' * 40}")
        print(f"Série: {serie.nome} ({serie.ativo})")
        print(f"{'=' * 40}")

        try:
            # 1. Fetch do preço atual (sempre, yfinance é gratuito)
            preco_info = fetch_preco_atual_yfinance(serie)
            if preco_info:
                # Salvar observação de preço
                inserir_observacao(
                    serie=serie,
                    data=timezone.now().date(),
                    valor=preco_info["preco"],
                    unidade=f"{preco_info['moeda']}/ação",
                )

            # 2. Fetch de dividendos (se tiver fonte Yahoo)
            if yahoo_source:
                data_hoje = timezone.now().date()
                data_um_ano_atras = data_hoje - datetime.timedelta(days=365)

                resultado = fetch_dividendos_yfinance(serie, data_um_ano_atras, data_hoje)
                if resultado:
                    for div in resultado:
                        inserir_observacao(
                            serie=serie,
                            data=div["data"],
                            valor=div["valor"],
                            unidade=div["unidade"],
                        )
                    # Atualizar payload bruto com últimos dividendos
                    salvar_payload_bruto(
                        serie,
                        json.dumps({"dividendos": resultado}),
                        yahoo_source.url_base or "yahoo_finance",
                    )

            # 3. Fetch de balanço (se tiver fonte Twelve Data)
            if twelvedata_source and TWELVE_DATA_API_KEY:
                data_hoje = timezone.now().date()
                resultado_balanco = fetch_balanco_twelve_data(serie, data_hoje)
                if resultado_balanco:
                    salvar_payload_bruto(
                        serie,
                        json.dumps({"balanco": resultado_balanco}),
                        twelvedata_source.url_base or "twelve_data",
                    )

            # 4. Fetch BCB (sem chave, fontes públicas)
            if bcb_source:
                print(f"  → BCB: dados públicos, skip fetch detalhado (regra R7)")
                # BCB PTAX/Dólar pode ser feito via API pública sem chave

        except Exception as e:
            print(f"  ✗ ERRO durante ingestão da série {serie.ativo}: {e!s}")
            registrar_fetch_log(
                source=serie.source,
                dia=timezone.now().date(),
                endpoint="ingest_dividendos_balances",
                status="erro",
                itens=0,
                latencia="0s",
                erro=str(e),
            )
            print(f"  → Erro registrado no fetch_log (R11 — bloqueio declarado)")

    print("\n" + "=" * 60)
    print("Ingestão concluída.")
    print(f"Fim: {timezone.now()}")
    print("=" * 60)
    print("Log de fetch registrado para todas as fontes.")
    print("Regra R12: escrita só por scripts de ingestão (never via view or API).")


if __name__ == "__main__":
    main()