"""Backend competence for pesquisador-de-mercado skill.

Responsible for structuring analyst recommendation searches and consensus
data to unlock the BBAS3 decision screen v1.

Princípio crítico: APENAS fontes gratuitas com cadastro ou cadastro-free.
Fontes-padrão: Brapi (B3), Twelve Data, Yahoo Finance (yfinance).
Fontes-NAO-permitidas: News generalistas ( Jornal Nacional, Folha, etc.) -
ficarão na v2.
"""

from decimal import Decimal
from typing import Optional, Dict, List, Any, Tuple
from datetime import date


def formatar_termometro_consenso(
    compra_pct: Optional[Decimal],
    neutro_pct: Optional[Decimal], 
    venda_pct: Optional[Decimal],
    preco_alvo_medio: Optional[Decimal],
    preco_tela_atual: Optional[Decimal],
    banco_destaque: Optional[str] = None,
    revisao_ultimos_dias: Optional[int] = None,
) -> Dict[str, Any]:
    """Formata o termômetro de consenso para a tela de decisão.
    
    Este é o output principal que aparecerá no bloco 'Foi o mercado?' da tela.
    
    Args:
        compra_pct: Porcentagem de analistas recomendando compra (0-100)
        neutro_pct: Porcentagem de analistas recomendando neutro (0-100)
        venda_pct: Porcentagem de analistas recomendando venda (0-100)
        preco_alvo_medio: Preço-alvo médio do mercado
        preco_tela_atual: Preço de tela atual do ativo
        banco_destaque: Casa de análise em destaque (ex: "Citi", "Banco do Brasil")
        revisao_ultimos_dias: Quantidade de dias desde a última revisão do price target
    
    Returns:
        Dict estruturado para o template do frontend
    """
    # Cálculo do upside/downside se tiveros os dados
    upside = None
    if preco_alvo_medio is not None and preco_tela_atual is not None and preco_tela_atual > 0:
        upside = ((preco_alvo_medio - preco_tela_atual) / preco_tela_atual) * 100
        upside = upside.quantize(Decimal("0.01"))
    
    # Determina sentimento dominante
    if compra_pct is not None and (venda_pct is None or compra_pct > venda_pct):
        sentimento = "positive"
    elif venda_pct is not None:
        sentimento = "negative"
    else:
        sentimento = "neutral"
    
    # Construção do dicionário de retorno
    resultado = {
        "compra_pct": float(compra_pct) if compra_pct is not None else None,
        "neutro_pct": float(neutro_pct) if neutro_pct is not None else None,
        "venda_pct": float(venda_pct) if venda_pct is not None else None,
        "preco_alvo_medio": float(preco_alvo_medio) if preco_alvo_medio is not None else None,
        "preco_tela_atual": float(preco_tela_atual) if preco_tela_atual is not None else None,
        "upside_pct": float(upside) if upside is not None else None,
        "sentimento": sentimento,
        "banco_destaque": banco_destaque or "",
        "revisao_alert": False,
    }
    
    # Lógica de alerta de revisão (caso crítico do Citi/BBAS3)
    if revisao_ultimos_dias is not None and revisao_ultimos_dias <= 48:
        resultado["revisao_alert"] = True
        resultado["revisao_dias"] = revisao_ultimos_dias
        resultado["revisao_mensagem"] = (
            f"⚠️ {banco_destaque or 'Casa de análise'} revisou o price target "
            f"nas últimas {revisao_ultimos_dias}h/dias"
        )
    
    return resultado


def calcular_gap_consenso(
    dados_novos: date,
    dados_anteriores: Optional[date] = None,
) -> Dict[str, Any]:
    """Calcula gap entre duas datas de dados de consenso.
    
    Regra R4: gaps não afetam o escopo, mas são calculados para
    informação de estaleness do dado.
    """
    if dados_anteriores is None:
        return {
            "gap_dias": None,
            "dados_estaoveis": True,
            "mensagem": "Dado único - sem comparação possível",
        }
    
    gap = (dados_novos - dados_anteriores).days
    
    # Definição de dado estalizado (over 30 days old for consensus)
    estalizado = gap > 30
    
    return {
        "gap_dias": gap,
        "dados_estaoveis": not estalizado,
        "mensagem": (
            f"Dado com {gap} dias - {'estalizado ⚠️' if estalizado else 'recente ✓'}"
        ),
    }


def extrair_dados_consenso_brapi(
    codigo_ativo: str = "BBAS3.SA",
) -> Optional[Dict[str, Any]]:
    """Tenta extrair consenso de analistas via Brapi API.
    
    Brapi oferece dados gratuitos para B3 ativos (.SA suffix).
    Este é o método preferido para v1 antes de tentar APIs pagas.
    
    Returns:
        Dict com dados de consenso ou None se falhar (sem chave/limitado)
    """
    import os
    import json
    
    # Verifica se tem chave no .env
    brapi_key = os.environ.get("BRAPI_API_KEY", "")
    
    if not brapi_key:
        # Modo teste: retorna dados simulados para desenvolvimento
        return {
            "fonte": "brapi (modo teste)",
            "consenso": {
                "compra": 55,
                "neutro": 30,
                "venda": 15,
            },
            "preco_alvo_medio": Decimal("24.62"),
            "preco_tela": Decimal("21.40"),
            "ultima_atualizacao": date.today(),
        }
    
    # Em produção tentaria chamada real via brapi SDK
    # from brapi import BrapiApi
    # ... lógica de chamada real ...
    
    return None


def extrair_dados_consenso_twelve_data(
    codigo_ativo: str = "BBAS3.SA",
) -> Optional[Dict[str, Any]]:
    """Tenta extrair dados via Twelve Data API.
    
    Twelve Data free tier: 8 créditos/min, 800/dia.
    Pode ser usado para dados complementares.
    """
    import os
    
    twelved_key = os.environ.get("TWELVE_DATA_API_KEY", "")
    
    if not twelved_key:
        # Modo teste with fallback dados
        return {
            "fonte": "twelve_data (modo teste)",
            "dados_simulados": True,
        }
    
    # Lógica real seria via API call
    # import twelve_data
    # ... chamada real ...
    
    return None


def gerar_alerta_revisao(
    banco: str,
    preco_anterior: Decimal,
    preco_novo: Decimal,
    datas_revisao: date,
    data_atual: date = None,
) -> Optional[Dict[str, Any]]:
    """Gera alerta de revisão de price target - o caso Citi/BBAS3.
    
    Este é o requisito mais crítico da v1. O alerta aparece no bloco
    'Foi o mercado?' da tela de decisão.
    
    Args:
        banco: Nome da casa de análise (ex: "Citi", "Banco do Brasil")
        preco_anterior: Price target anterior
        preco_novo: Novo price target
        datas_revisao: Data da revisão
        data_atual: Data de hoje (usa date.today() se não informado)
    
    Returns:
        Dict com alerta formatado ou None se não houver significativa mudança
    """
    if data_atual is None:
        data_atual = date.today()
    
    dias_desde_revisao = (data_atual - datas_revisao).days
    
    # Só gera alerta se foi revisado nas últimas 48h OU se mudou significativamente
    # (>= 10% de mudança no price target)
    mudanca_pct = abs((preco_novo - preco_anterior) / preco_anterior * 100) if preco_anterior != 0 else 0
    
    if dias_desde_revisao <= 48 or mudanca_pct >= 10:
        return {
            "ativo": banco,
            "tipo": "revisao_price_target",
            "data_revisao": datas_revisao.isoformat(),
            "dias_desde_revisao": dias_desde_revisao,
            "preco_anterior": float(preco_anterior),
            "preco_novo": float(preco_novo),
            "mudanca_pct": round(float(mudanca_pct), 2),
            "eh_recente": dias_desde_revisao <= 48,
            "mensagem": (
                f"⚠️ {banco} revisou o price target de R$ {preco_anterior:.2f} "
                f"para R$ {preco_novo:.2f} "
                f"({'alta' if preco_novo > preco_anterior else 'queda'} de "
                f"{mudanca_pct:.1f}%)"
            ),
        }
    
    return None
