"""Cliente para APIs do Banco Central do Brasil (BCB).

Princípio crítico: APENAS leitura. Dados passados não mudam, então banco local
é a fonte verdadeira. Nenhuma gravação é feita por este módulo.

Endpoints gratuitos, sem necessidade de chave/token.
"""

import os
import time
import logging
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BCB_BASE_URL = "https://api.bcb.gov.br/dados/serie"


def _request(url: str, max_retries: int = 3) -> Dict[str, Any]:
    """Faz requisição HTTP ao BCB com retry em 429.

    Args:
        url: URL completa da API BCB
        max_retries: Número máximo de tentativas para 429 (rate limit)

    Returns:
        Dict com dados JSON da resposta

    Raises:
        RuntimeError: Em erros 404, 429 após retries ou outras falhas
    """
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data

            if response.status_code == 404:
                logger.warning(f"BCB: 404 - Recurso não encontrado: {url}")
                raise RuntimeError(f"BCB: 404 - Recurso não encontrado.")

            if response.status_code == 429:
                if attempt < max_retries:
                    # BCB costuma enviar Retry-After em segundos
                    retry_after = response.headers.get("Retry-After")
                    wait = int(retry_after) if retry_after and retry_after.isdigit() else 30
                    logger.warning(
                        f"BCB: 429 Rate limit. Waiting {wait}s antes de retry..."
                    )
                    time.sleep(wait)
                    continue
                logger.error("BCB: 429 Max retries exceeded")
                raise RuntimeError(
                    "BCB: 429 - Cota excedida. Tente novamente mais tarde."
                )

            logger.error(f"BCB: Unexpected status {response.status_code}: {response.text}")
            raise RuntimeError(f"BCB: Erro {response.status_code} - {response.text}")

        except RuntimeError:
            raise
        except Exception as e:
            if attempt < max_retries:
                wait = 2 ** attempt  # backoff: 1, 2, 4 seconds
                logger.warning(f"BCB request error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"BCB: Max retries exceeded. Last error: {e}")
                raise


def get_dolar_ptax(
    data_inicial: str, data_final: str, endpoint: str = "cotacao"
) -> Optional[Dict[str, Any]]:
    """Busca cotação do dólar (USD/BRL) pelo PTAX do BCB.

    Endpoints disponíveis:
    - CotacaoDolarPeriodo: dados históricos detalhados
    - CotacaoVenda: apenas taxa de venda

    Args:
        data_inicial: Data inicial em AAAA-MM-DD
        data_final: Data final em AAAA-MM-DD
        endpoint: "cotacao" (padrão, mais detalhado) ou "cotacao_venda"

    Returns:
        Dict com dados do PTAX ou None em caso de erro
    #"""
    if endpoint == "cotacao":
        url = (
            f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            f"CotacaoDolarPeriodo?$dataInicial={data_inicial}&"
            f"$dataFinal={data_final}&$format=json"
        )
    else:
        url = (
            f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            f"CotacaoVenda?$dataInicial={data_inicial}&"
            f"$dataFinal={data_final}&$format=json"
        )

    try:
        data = _request(url)
        value = data.get("value", [])
        if not value:
            return None

        # Formatar retorno - BCB traz o último dia da sequência
        ultimo_registro = value[-1] if value else None
        if not ultimo_registro:
            return None

        return {
            "data": ultimo_registro.get("data"),
            "cotacaoVenda": (
                Decimal(str(ultimo_registro["cotacaoVenda"]))
                if ultimo_registro.get("cotacaoVenda") is not None
                else None
            ),
            "cotacaoCompra": (
                Decimal(str(ultimo_registro["cotacaoCompra"]))
                if ultimo_registro.get("cotacaoCompra") is not None
                else None
            ),
            "dataHoraCotacao": ultimo_registro.get("dataHoraCotacao"),
        }

    except RuntimeError as e:
        logger.error(f"BCB: Erro PTAX para {data_inicial}-{data_final}: {e}")
        return None


def get_series_sgs(
    codigo_sgs: int, data_inicial: str, data_final: str
) -> Optional[List[Dict[str, Any]]]:
    """Busca série histórica do BCB pelo código SGS (Sistema Gerencial de Séries).

    Códigos SGS comuns:
    - 432 - Taxa Selic
    - 433 - Inflação IPCA
    - 11 - PIB
    - 2015 - Dólar Turismo

    Args:
        codigo_sgs: Código da série SGS
        data_inicial: Data inicial em AAAA-MM-DD
        data_final: Data final em AAAA-MM-DD

    Returns:
        Lista de dicts com {'data':, 'valor':} ou None em caso de erro
    """
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_sgs}/dados/"
        f"?dataInicial={data_inicial}&"
        f"dataFinal={data_final}&"
        f"formato=json"
    )

    try:
        data = _request(url)
        registros = data.get("value", [])

        if not registros:
            return []

        # Formatar dados - BCB vem em ordem crescente de data
        formatted = []
        for registro in registros:
            try:
                formatted.append(
                    {
                        "data": registro.get("data"),
                        "valor": (
                            Decimal(str(registro["valor"]))
                            if registro.get("valor") is not None
                            else None
                        ),
                    }
                )
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"BCB: Erro formatando registro: {e}")
                continue

        return formatted

    except RuntimeError as e:
        logger.error(f"BCB: Erro série SGS {codigo_sgs}: {e}")
        return None


def get_selic(
    data_inicial: str, data_final: str
) -> Optional[List[Dict[str, Any]]]:
    """Atalho para busca da taxa Selic.

    Códigos SGS: 432 (Taxa Selic) e 432 (variação da Taxa Selic)

    Args:
        data_inicial: Data inicial em AAAA-MM-DD
        data_final: Data final em AAAA-MM-DD

    Returns:
        Lista de dicts com taxa Selic ou None
    """
    return get_series_sgs(432, data_inicial, data_final)


def get_ipca(
    data_inicial: str, data_final: str
) -> Optional[List[Dict[str, Any]]]:
    """Atalho para busca do IPCA (inflação).

    Códigos SGS: 433 (IPCA)

    Args:
        data_inicial: Data inicial em AAAA-MM-DD
        data_final: Data final em AAAA-MM-DD

    Returns:
        Lista de dicts com IPCA ou None
    """
    return get_series_sgs(433, data_inicial, data_final)