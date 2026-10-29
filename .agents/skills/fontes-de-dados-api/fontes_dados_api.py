"""Backend competence for fontes-de-dados-api skill.

Responsible for managing the catalog of available data sources (free and paid),
controlling API keys in .env, tracking daily quota, and providing conventions
for provenance and data writing.

Princípio crítico: APENAS fontes gratuitas com cadastro ou cadastro-free.
Fontes-padrão: Brapi, Twelve Data, Yahoo Finance (yfinance).
Fontes-NAO-permitidas: Qualquer fonte que exija pagamento sem alternativa gratuita - ficarão na v2.
"""

import os
from datetime import date
from decimal import Decimal
from typing import Optional, Dict, List, Any, Tuple


def listar_fontes_disponiveis() -> List[Dict[str, Any]]:
    """Lista todas as fontes de dados disponíveis no sistema.
    
    Esta função consulta o banco de dados de fontes e retorna um catálogo
    organizado para o administrador ou frontend.
    
    Returns:
        Lista de dicionários com informações de cada fonte
    """
    # TODO: Quando integrado ao banco Django, consultar Source model
    # Por enquanto, retorna catálogo padrão
    
    fontes_padrao = [
        {
            "id": "brapi",
            "nome": "Brapi (B3)",
            "tipo": "api",
            "descricao": "Endpoints gratuitos para ativos B3 (.SA suffix)",
            "requiere_chave": False,
            "cota_diaria": None,  # Ilimitado no plano gratuito
            "status": "livre",
        },
        {
            "id": "twelve_data",
            "nome": "Twelve Data",
            "tipo": "api",
            "descricao": "8 créditos/min, 800/dia no plano gratuito",
            "requiere_chave": True,
            "cota_diaria": 800,
            "status": "freemium",
        },
        {
            "id": "yfinance",
            "nome": "Yahoo Finance (yfinance)",
            "tipo": "library",
            "descricao": "Biblioteca Python, sem limites de cota",
            "requiere_chave": False,
            "cota_diaria": None,
            "status": "livre",
        },
        {
            "id": "alpha_vantage",
            "nome": "Alpha Vantage",
            "tipo": "api",
            "descricao": "25 req/dia no plano gratuito",
            "requiere_chave": True,
            "cota_diaria": 25,
            "status": "freemium",
        },
    ]
    
    return fontes_padrao


def verificar_cota_diaria(
    fonte_id: str,
    usadas_hoje: int = 0,
) -> Dict[str, Any]:
    """Verifica a cota diária restante para uma fonte.
    
    Args:
        fonte_id: ID da fonte (brapi, twelve_data, yfinance, etc.)
        usadas_hoje: Quantidade já utilizada hoje (vindo do FetchLog)
    
    Returns:
        Dict com informações da cota
    """
    fontes_catalogo = listar_fontes_disponiveis()
    
    fonte = next((f for f in fontes_catalogo if f["id"] == fonte_id), None)
    if fonte is None:
        return {
            "erro": f"Fonte '{fonte_id}' não encontrada no catálogo",
            "fonte_id": fonte_id,
        }
    
    cota = fonte.get("cota_diaria")
    if cota is None:
        # Fonte ilimitada (yfinance, brapi sem restrição)
        return {
            "fonte": fonte["nome"],
            "cota_diaria": "ilimitada",
            "usadas_hoje": usadas_hoje,
            "restantes": "ilimitada",
            "percentual_uso": 0,
            "alert": None,
        }
    
    restantes = max(0, cota - usadas_hoje)
    percentual = round((usadas_hoje / cota) * 100, 2) if cota > 0 else 0
    
    alerte = None
    if percentual >= 90:
        alerte = "⚠️ Próximo do limite diário"
    elif percentual >= 75:
        alerte = "⚡ Atenção: uso elevado"
    
    return {
        "fonte": fonte["nome"],
        "cota_diaria": cota,
        "usadas_hoje": usadas_hoje,
        "restantes": restantes,
        "percentual_uso": percentual,
        "alert": alerte,
    }


def formatar_proveniencia(
    fonte_nome: str,
    fonte_tipo: str,
    url_base: str,
    licenca: str,
    cota_info: str = "",
) -> Dict[str, Any]:
    """Formata bloco de proveniência para anexar em respostas de API.
    
    Regra R9 de specs/fontes-de-dados.md: fonte + licença + URL sempre juntos
    dos dados.
    
    Args:
        fonte_nome: Nome da fonte (ex: "Brapi (B3)")
        fonte_tipo: Tipo (api, library, etc.)
        url_base: URL base da fonte
        licenca: Informação de licença
        cota_info: Informação de cota/restrição
    
    Returns:
        Dict estruturado para resposta JSON
    """
    return {
        "nome": fonte_nome,
        "tipo": fonte_tipo,
        "url_base": url_base,
        "licenca": licenca,
        "cota": cota_info,
    }


def verificar_chave_ambiente(fonte_id: str) -> Dict[str, Any]:
    """Verifica se a chave da API necessária está configurada no .env.
    
    Args:
        fonte_id: ID da fonte a verificar
    
    Returns:
        Dict indicando se chave está presente e status
    """
    # Mapping de fontes que exigem chave
    fontes_que_exigem_chave = {
        "twelve_data": "TWELVE_DATA_API_KEY",
        "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
    }
    
    env_var = fontes_que_exigem_chave.get(fonte_id)
    
    if env_var is None:
        # Fontes que não exigem chave (yfinance, brapi em modo teste)
        return {
            "fonte": fonte_id,
            "chave_necessaria": False,
            "configurada": True,  # Consideramos configurada por ser nativa
            "mensagem": "Não requer chave de API",
        }
    
    chave = os.environ.get(env_var, "")
    configurada = bool(chave) and chave != "SUA_CHAVE_AQUI"
    
    return {
        "fonte": fonte_id,
        "chave_necessaria": True,
        "configurada": configurada,
        "variavel_env": env_var,
        "mensagem": (
            f"Chave '{env_var}' {'configurada ✓' if configurada else 'NÃO configurada - configure no .env'}"
        ),
    }


def obter_instrucoes_integracao(fonte_id: str) -> Dict[str, Any]:
    """Retorna instruções de integração para uma fonte específica.
    
    Útil para documentação e setup inicial.
    
    Args:
        fonte_id: ID da fonte
    
    Returns:
        Dict com steps de instalação e configuração
    """
    instrucoes_padrao = {
        "brapi": {
            "instalacao": "pip install brapi",
            "chave": "Não necessária para plano gratuito",
            "uso": "from brapi import BrapiApi; api = BrapiApi()",
            "ativo_br": "Adicionar .SA ao código: BBAS3.SA",
        },
        "twelve_data": {
            "instalacao": "pip install twelvedata",
            "chave": "Registrar em https://twelvedata.com/signup",
            "variavel_env": "TWELVE_DATA_API_KEY",
            "uso": "import twelvedata; api = twelveddata.API(key=os.getenv('TWELVE_DATA_API_KEY'))",
        },
        "yfinance": {
            "instalacao": "pip install yfinance (já vem no venv)",
            "chave": "Não necessária - gratuita e ilimitada",
            "uso": "import yfinance as yf; ticker = yf.Ticker('BBAS3.SA')",
        },
    }
    
    return instrucoes_padrao.get(
        fonte_id,
        {
            "instalacao": "Verificar README da fonte",
            "chave": "Consultar site da fonte",
            "uso": "Verificar documentação específica",
        },
    )
