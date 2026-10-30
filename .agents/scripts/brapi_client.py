"""Cliente para a API brapi.dev v2 - dados de mercado B3.

Princípio crítico: APENAS leitura. Nada é gravado no banco por este módulo.
O módulo lê da rede e retorna dados estruturados para o backend Django
ou para scripts de ingestão.

- Usa BRAPI_TOKEN da variável de ambiente (NUNCA código hardcoded)
- Header: Authorization: Bearer <BRAPI_TOKEN>
- Endpoint: /api/v2/quote?symbols=PETR4.SA,VALE3.SA
- Erros: 401, 404, 429 (com Retry-After)
- Dados: Decimal, dates formatados, None para campos nulos
"""

import os
import time
import json
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

import requests
from requests.models import Response

from django.conf import settings

logger = logging.getLogger(__name__)


BRAPI_BASE_URL = "https://brapi.dev/api/v2"
BRAPI_TIMEOUT = 30  # seconds
BRAPI_MAX_RETRIES = 3


def _get_token() -> str:
    """Retorna o token da variável de ambiente BRAPI_TOKEN."""
    from dotenv import load_dotenv
    load_dotenv()  # carrega .env para o ambiente
    token = os.environ.get("BRAPI_TOKEN", "")
    if not token:
        logger.warning("BRAPI_TOKEN not set in environment")
    return token


def _headers() -> Dict[str, str]:
    """Retorna headers com autenticação Bearer."""
    token = _get_token()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "investimentos-project/1.0",
    }


def _handle_brapi_error(response: Response) -> None:
    """Trata erros da API Brapi.

    - 401: Token inválido/expirado - lança erro específico
    - 404: Ativo não encontrado - retorna None/empty
    - 429: Limite de cota - respeita Retry-After header
    - Outros: logged e relança como RuntimeError
    """
    status_code = response.status_code

    if status_code == 401:
        logger.error("BRAPI: 401 Unauthorized - token inválido ou expirado")
        raise RuntimeError("BRAPI: 401 - Token inválido ou expirado. Verifique BRAPI_TOKEN.")
    elif status_code == 404:
        logger.warning("BRAPI: 404 - Ativo não encontrado")
        raise RuntimeError("BRAPI: 404 - Ativo ou endpoint não encontrado.")
    elif status_code == 429:
        # Respeitar header Retry-After se presente
        retry_after = response.headers.get("Retry-After")
        wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 60
        logger.warning(
            f"BRAPI: 429 Rate limit exceeded. Waiting {wait_seconds}s before retry."
        )
        time.sleep(wait_seconds)
        raise RuntimeError(f"BRAPI: 429 - Cota excedida. Aguarde {wait_seconds}s e tente novamente.")
    else:
        logger.error(f"BRAPI: Unexpected error {status_code}: {response.text}")
        raise RuntimeError(f"BRAPI: Error {status_code} - {response.text}")


def _request_with_retry(
    url: str, max_retries: int = BRAPI_MAX_RETRIES
) -> Dict[str, Any]:
    """Faz requisição à API Brapi com retry em 429 e tratamento de erros.

    Args:
        url: URL completa da API
        max_retries: Número máximo de tentativas (considera o inicial + retries)

    Returns:
        Dict com dados JSON da resposta

    Raises:
        RuntimeError: Em erros 401, 404, 429 ou após exceder max_retries
    """
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=_headers(), timeout=BRAPI_TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                # Validar que tem dados
                if not data or "results" not in data or not data.get("results"):
                    raise RuntimeError("BRAPI: resposta vazia ou inválida")
                return data

            _handle_brapi_error(response)

        except RuntimeError:
            raise
        except Exception as e:
            if attempt < max_retries:
                wait = 2 ** attempt  # exponential backoff: 1, 2, 4 seconds
                logger.warning(f"BRAPI request error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"BRAPI: Max retries exceeded. Last error: {e}")
                raise


def quote_symbols(symbols: List[str]) -> Optional[Dict[str, Any]]:
    """Busca cotação de múltiplos símbolos em uma chamada única.

    Este é o endpoint principal da brapi.dev para obter preços e dados
    de mercado de ativos B3.

    Args:
        symbols: Lista de códigos de exemplo, ex: ["PETR4.SA", "VALE3.SA"]
                 O sufixo .SA é opcional - o Brapi normaliza internamente.

    Returns:
        Dict com estrutura {'symbol': 'PETR4.SA', 'price': Decimal('24.50'), ...}
        None se falhar após todos os retries.

    Example:
        >>> dados = quote_symbols(["PETR4.SA", "VALE3.SA"])
        >>> dados["PETR4.SA"]["price"]
        Decimal('24.50')
    """
    if not symbols:
        logger.error("BRAPI: Nenhum símbolo fornecido")
        return None

    # O Brapi aceita múltiplos símbolos separados por vírgula
    symbols_str = ",".join(symbols)
    url = f"{BRAPI_BASE_URL}/quote?symbols={symbols_str}"

    try:
        data = _request_with_retry(url)

        # Estrutura de retorno do Brapi v2:
        # {
        #   "status": "success",
        #   "message": "OK",
        #   "results": {
        #     "PETR4.SA": {
        #       "symbol": "PETR4.SA",
        #       "companyName": "Petrobras",
        #       "price": 24.50,
        #       "change": 1.25,
        #       "changePercent": "5.35",
        #       "dayLow": 23.45,
        #       "dayHigh": 25.10,
        #       "marketCap": 856700000000,
        #       "52WeekHigh": 30.,
        #       "52WeekLow": 18.,
        #       "timestamp": "2024-01-15T14:30:00.000Z",
        #       "meta": {...}
        #     },
        #     ...
#                }
#        }

        results = data.get("results", {})
        if not results:
            logger.warning("BRAPI: Nenhum resultado retornado")
            return None

        # Estruturar resultados em dicionário mais fácil de usar
        formatted: Dict[str, Any] = {}
        for symbol, data_item in results.items():
            try:
                formatted[symbol] = {
                    "symbol": symbol,
                    "companyName": data_item.get("companyName"),
                    "price": (
                        Decimal(str(data_item["price"]))
                        if data_item.get("price") is not None
                        else None
                    ),
                    "change": (
                        Decimal(str(data_item["change"]))
                        if data_item.get("change") is not None
                        else None
                    ),
                    "changePercent": (
                        Decimal(str(data_item["changePercent"]).replace("%", ""))
                        if data_item.get("changePercent") is not None
                        else None
                    ),
                    "dayLow": (
                        Decimal(str(data_item["dayLow"]))
                        if data_item.get("dayLow") is not None
                        else None
                    ),
                    "dayHigh": (
                        Decimal(str(data_item["dayHigh"]))
                        if data_item.get("dayHigh") is not None
                        else None
                    ),
                    "marketCap": (
                        Decimal(str(data_item["marketCap"]))
                        if data_item.get("marketCap") is not None
                        else None
                    ),
                    "52WeekHigh": (
                        Decimal(str(data_item["52WeekHigh"]))
                        if data_item.get("52WeekHigh") is not None
                        else None
                    ),
                    "52WeekLow": (
                        Decimal(str(data_item["52WeekLow"]))
                        if data_item.get("52WeekLow") is not None
                        else None
                    ),
                    "timestamp": data_item.get("timestamp"),
                    "currency": data_item.get("currency"),
                }
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"BRAPI: Error formatting {symbol}: {e}")
                formatted[symbol] = {
                    "symbol": symbol,
                    "error": str(e),
                })

        return formatted

    except RuntimeError as e:
        logger.error(f"BRAPI: Failed to quote symbols {symbols}: {e}")
        return None


def quote_single(symbol: str) -> Optional[Dict[str, Any]]:
    """Busca cotação de um único símbolo.

    Atalho para quote_symbols com lista de um único elemento.

    Args:
        symbol: Código do ativo, ex: "PETR4.SA"

    Returns:
        Dict com dados formatados ou None em caso de erro
    """
    return quote_symbols([symbol])


def search_symbol(name: str) -> Optional[Dict[str, Any]]:
    """Busca símbolos pelo nome da empresa.

    Args:
        name: Nome da empresa, ex: "Petrobras", "Petrobras SA"

    Returns:
        Dict com matches ou None
    """
    url = f"{BRAPI_BASE_URL}/quote?symbols={name}"
    try:
        data = _request_with_retry(url)
        results = data.get("results", {})
        if results:
            # Retornar o primeiro match
            first_symbol = list(results.keys())[0]
            return results[first_symbol]
        return None
    except RuntimeError as e:
        logger.error(f"BRAPI: Search error for '{name}': {e}")
        return None


def historical(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = "1D",
) -> Optional[List[Dict[str, Any]]]:
    """Busca histórico de preços de um ativo.

    Args:
        symbol: Código do ativo, ex: "PETR4.SA"
        start_date: Data inicial em AAAA-MM-DD
        end_date: Data final em AAAA-MM-DD
        interval: Intervalo ("1D", "1W", "1M")

    Returns:
        Lista de dicts com {'date':, 'open', 'high', 'low', 'close', 'volume'}
        ou None em caso de erro
    """
    # O endpoint /historical do Brapi pode exigir parâmetros específicos
    # Esta é uma implementação baseada na estrutura conhecida da API
    url = (
        f"{BRAPI_BASE_URL}/historical"
        f"?symbol={symbol}"
        f"&interval={interval}"
        f"&startDate={start_date}"
        f"&endDate={end_date}"
    )

    try:
        data = _request_with_retry(url)
        historical_data = data.get("historical", [])
        if not historical_data:
            return []

        # Formatar datas e valores
        formatted = []
        for item in historical_data:
            try:
                formatted.append(
                    {
                        "date": item.get("date"),
                        "open": (
                            Decimal(str(item["open"]))
                            if item.get("open") is not None
                            else None
                        ),
                        "high": (
                            Decimal(str(item["high"]))
                            if item.get("high") is not None
                            else None
                        ),
                        "low": (
                            Decimal(str(item["low"]]))
                            if item.get("low") is not None
                            else None
                        ),
                        "close": (
                            Decimal(str(item["close"]))
                            if item.get("close") is not None
                            else None
                        ),
                        "volume": (
                            int(item["volume"])
                            if item.get("volume") is not None
                            else None
                        ),
                    }
                )
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"BRAPI: Error formatting historical item: {e}")
                continue

        return formatted

    except RuntimeError as e:
        logger.error(f"BRAPI: Historical data error for {symbol}: {e}")
        return None