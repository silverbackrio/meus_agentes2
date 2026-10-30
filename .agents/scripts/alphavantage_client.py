"""Cliente para Alpha Vantage API - dados de mercado globais.

Princípio crítico: APENAS leitura. Nada é gravado no banco por este módulo.

Free tier: 25 requisições/dia, sem cartão de crédito.
Chave: ALPHA_VANTAGE_API_KEY (somente em .env, nunca no código/repositório)

Endpoints úteis:
- TIME_SERIES_DAILY - preço diário de ações
- FX_DAILY - cotações de câmbio
- GLOBAL_QUOTE - cotação atual
- SYMBOL_SEARCH - busca por palavras-chave
"""

import os
import time
import logging
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Dict, Any, List

import requests

logger = logging.getLogger(__name__)

ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHAVANTAGE_TIMEOUT = 30
ALPHAVANTAGE_MAX_RETRIES = 3


def _get_api_key() -> str:
    """Retorna a chave da API Alpha Vantage da variável de ambiente."""
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        logger.warning("ALPHA_VANTAGE_API_KEY not set in environment")
    return api_key


def _request_with_retry(
    params: Dict[str, Any], max_retries: int = ALPHAVANTAGE_MAX_RETRIES
) -> Optional[Dict[str, Any]]:
    """Faz requisição à API Alpha Vantage com retry em erros 429.

    Args:
        params: Parâmetros da query string (function, symbol, etc.)
        max_retries: Número máximo de tentativas para 429

    Returns:
        Dict com dados JSON ou None se falhar
    """
    api_key = _get_api_key()
    if not api_key:
        logger.error("ALPHA_VANTAGE_API_KEY not configured - cannot proceed")
        return None

    params["apikey"] = api_key

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                ALPHAVANTAGE_BASE_URL, params=params, timeout=ALPHAVANTAGE_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()

                # Alpha Vantage retorna "Note" quando atinge rate limit
                if "Note" in data:
                    logger.warning(f"Alpha Vantage: Rate limit atingido: {data['Note']}")
                    if attempt < max_retries:
                        wait = 60
                        logger.warning(f"Rate limit - aguardando {wait}s antes de retry...")
                        time.sleep(wait)
                        continue
                    raise RuntimeError(
                        "Alpha Vantage: 429 - Rate limit atingido. Tente mais tarde."
                    )

                # Alpha Vantage retorna "Error Message" para erros
                if "Error Message" in data:
                    error_msg = data["Error Message"]
                    logger.error(f"Alpha Vantage: Error: {error_msg}")
                    raise RuntimeError(f"Alpha Vantage: Error - {error_msg}")

                # Alpha Vantage retorna "Information" para mensagens info
                if "Information" in data:
                    logger.info(f"Alpha Vantage: {data['Information']}")

                return data

            elif response.status_code == 429:
                if attempt < max_retries:
                    retry_after = response.headers.get("Retry-After", "60")
                    wait = int(retry_after) if retry_after.isdigit() else 60
                    logger.warning(f"Alpha Vantage: 429 Rate limit. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                raise RuntimeError("Alpha Vantage: 429 - Rate limit atingido.")

            elif response.status_code == 404:
                logger.warning("Alpha Vantage: 404 - Recurso não encontrado")
                raise RuntimeError("Alpha Vantage: 404 - Recurso não encontrado.")

            else:
                logger.error(
                    f"Alpha Vantage: Unexpected status {response.status_code}: {response.text}"
                )
                raise RuntimeError(
                    f"Alpha Vantage: Error {response.status_code} - {response.text}"
                )

        except RuntimeError:
            raise
        except Exception as e:
            if attempt < max_retries:
                wait = 2 ** attempt
                logger.warning(f"Alpha Vantage request error: {e}. Retry em {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Alpha Vantage: Max retries. Last error: {e}")
                raise


def get_time_series_daily(
    symbol: str, outputsize: str = "compact"
) -> Optional[List[Dict[str, Any]]]:
    """Busca série histórica diária de preços de uma ação.

    Args:
        symbol: Símbolo da ação (ex: "PETR4.SA", "VALE3.SA", "AAPL")
        outputsize: "compact" (últimos 100 dias) ou "full" (todo histórico)

    Returns:
        Lista de dicts com {'date':, 'open', 'high', 'low', 'close', 'volume'}
        ou None em caso de erro
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": outputsize,
        "datatype": "json",
    }

    try:
        data = _request_with_retry(params)
        if not data:
            return None

        time_series = data.get("Time Series (Daily)", {})
        if not time_series:
            logger.warning(f"Alpha Vantage: Nenhuma série para {symbol}")
            return []

        formatted = []
        for date_str, values in time_series.items():
            try:
                formatted.append(
                    {
                        "date": date_str,
                        "open": (
                            Decimal(str(values.get("1. open")))
                            if values.get("1. open")
                            else None
                        ),
                        "high": (
                            Decimal(str(values.get("2. high")))
                            if values.get("2. high")
                            else None
                        ),
                        "low": (
                            Decimal(str(values.get("3. low")))
                            if values.get("3. low")
                            else None
                        ),
                        "close": (
                            Decimal(str(values.get("4. close")))
                            if values.get("4. close")
                            else None
                        ),
                        "volume": (
                            int(values.get("5. volume"))
                            if values.get("5. volume")
                            else None
                        ),
                    }
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Alpha Vantage: Erro formatando {date_str}: {e}")
                continue

        formatted.sort(key=lambda x: x["date"])
        return formatted

    except RuntimeError as e:
        logger.error(f"Alpha Vantage: Erro série diária para {symbol}: {e}")
        return None


def get_fx_daily(
    from_symbol: str = "USD", to_symbol: str = "BRL"
) -> Optional[List[Dict[str, Any]]]:
    """Busca série histórica diária de câmbio (FX).

    Args:
        from_symbol: Moeda origem (padrão: "USD")
        to_symbol: Moeda destino (padrão: "BRL")

    Returns:
        Lista de dicts com {'date':, 'rate'} ou None
    """
    params = {
        "function": "FX_DAILY",
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "outputsize": "compact",
        "datatype": "json",
    }

    try:
        data = _request_with_retry(params)
        if not data:
            return None

        time_series = data.get("Time Series FX (Daily)", {})
        if not time_series:
            return []

        formatted = []
        for date_str, values in time_series.items():
            try:
                rate = values.get("4. close")
                formatted.append(
                    {
                        "date": date_str,
                        "rate": Decimal(str(rate)) if rate else None,
                    }
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Alpha Vantage: Erro formatando FX {date_str}: {e}")
                continue

        formatted.sort(key=lambda x: x["date"])
        return formatted

    except RuntimeError as e:
        logger.error(f"Alpha Vantage: Erro FX {from_symbol}/{to_symbol}: {e}")
        return None


def search_symbol(keywords: str) -> Optional[List[Dict[str, Any]]]:
    """Busca ações por palavras-chave (empresa, setor, etc.).

    Args:
        keywords: Palavras-chave para busca (ex: "Petrobras", "bank")

    Returns:
        Lista de dicts com {'symbol':, 'name':, 'type':, 'region':, 'matchScore':}
        ou None
    """
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": keywords,
    }

    try:
        data = _request_with_retry(params)
        if not data:
            return None

        matches = data.get("bestMatches", [])
        if not matches:
            return []

        formatted = []
        for match in matches:
            try:
                formatted.append(
                    {
                        "symbol": match.get("1. symbol"),
                        "name": match.get("2. name"),
                        "type": match.get("3. type"),
                        "region": match.get("4. region"),
                        "matchScore": (
                            Decimal(str(match.get("9. matchScore")))
                            if match.get("9. matchScore")
                            else None
                        ),
                    }
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Alpha Vantage: Erro formatando match: {e}")
                continue

        return formatted

    except RuntimeError as e:
        logger.error(f"Alpha Vantage: Erro busca '{keywords}': {e}")
        return None


def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """Busca cotação atual de uma ação.

    Args:
        symbol: Símbolo da ação (ex: "PETR4.SA", "AAPL")

    Returns:
        Dict com dados da cotação ou None
    """
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
    }

    try:
        data = _request_with_retry(params)
        if not data:
            return None

        quote = data.get("Global Quote", {})
        if not quote:
            return None

        return {
            "symbol": quote.get("01. symbol"),
            "open": (
                Decimal(str(quote["02. open"])) if quote.get("02. open") else None
            ),
            "high": (
                Decimal(str(quote["03. high"])) if quote.get("03. high") else None
            ),
            "low": (
                Decimal(str(quote["04. low"])) if quote.get("04. low") else None
            ),
            "price": (
                Decimal(str(quote["05. price"])) if quote.get("05. price") else None
            ),
            "volume": (
                int(quote["06. volume"]) if quote.get("06. volume") else None
            ),
            "latest_trading_day": quote.get("07. latest trading day"),
            "previous_close": (
                Decimal(str(quote["08. previous close"]))
                if quote.get("08. previous close")
                else None
            ),
            "change": (
                Decimal(str(quote["09. change"])) if quote.get("09. change") else None
            ),
            "change_percent": (
                Decimal(str(quote["10. change percent"]).replace("%", ""))
                if quote.get("10. change percent")
                else None
            ),
        }

    except RuntimeError as e:
        logger.error(f"Alpha Vantage: Erro quote {symbol}: {e}")
        return None