"""Cálculos de mercado para o app market_data.

Funções puras para cálculo de gaps, frequência e validação de séries históricas.
Todas as funções aceitam e retornam Decimal para consistência com o resto do projeto
(regra R5 de specs/aplicacao.md)."""

from datetime import date
from decimal import Decimal, InvalidOperation

ZERO = Decimal("0")


def _decimal(valor, campo: str) -> Decimal:
    """Converte entrada para Decimal com mensagem de erro que o campo aponta.

    Aceita Decimal, int, str (ex.: "80.50") e float (último caso, apenas por cortesia).
    """
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, bool):
        raise ValueError(f"{campo}: informe um número, não um booleano")
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, str):
        try:
            return Decimal(valor.replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(f"{campo}: {valor!r} não é um número válido") from exc
    if isinstance(valor, float):
        return Decimal(str(valor))
    raise ValueError(f"{campo}: tipo {type(valor).__name__} não é um número")


def calcular_gap_periodo(data_inicial: date, data_final: date, observacoes: list) -> dict:
    """Calcula o gap entre datas para uma série histórica.

    Regra R4: gap é calculado antes do fetch para saber se já temos dados ou
    se precisamos pesquisar novo período.

    Retorna:
    - tem_dados: bool indicando se há observações no período
    - gap_dias: int com o número de dias de gap
    - inicio_real: date da primeira observação disponível
    - fim_real: date da última observação disponível
    """
    if not observacoes:
        return {
            "tem_dados": False,
            "gap_dias": (data_final - data_inicial).days,
            "inicio_real": None,
            "fim_real": None,
        }

    # Filtrar observações no período
    observacoes_periodo = [
        obs for obs in observacoes
        if data_inicial <= obs.data <= data_final
    ]

    if observacoes_periodo:
        # Tem dados no período, gap é zero
        datas = [obs.data for obs in observacoes_periodo]
        return {
            "tem_dados": True,
            "gap_dias": 0,
            "inicio_real": min(datas),
            "fim_real": max(datas),
        }
    else:
        # Não tem dados no período, calcular gap até o último dado
        todas_datas = [obs.data for obs in observacoes]
        fim_real = max(todas_datas)
        inicio_real = min(todas_datas)

        # Gap começa após a última observação
        gap_dias = (data_inicial - fim_real).days if data_inicial > fim_real else 0

        return {
            "tem_dados": False,
            "gap_dias": gap_dias,
            "inicio_real": inicio_real,
            "fim_real": fim_real,
        }


def frequencia_para_str(freq: str) -> str:
    """Converte código de frequência para string legível."""
    frequencias = {
        "diario": "Diário",
        "semanal": "Semanal",
        "mensal": "Mensal",
        "anual": "Anual",
    }
    return frequencias.get(freq, freq)


def str_para_frequencia(freq_str: str) -> str:
    """Converte string para código de frequência validado."""
    freq_str = freq_str.lower().strip()
    validas = {"diario": "diario", "semanal": "semanal", "mensal": "mensal", "anual": "anual"}
    if freq_str not in validas:
        raise ValueError(f"Frequência inválida: {freq_str}. Use: {list(validas.keys())}")
    return validas[freq_str]


def data_para_chave(data: date) -> str:
    """Converte date para chave de string no formato YYYY-MM-DD."""
    return data.isoformat()


def chave_para_data(chave: str) -> date:
    """Converte chave de string YYYY-MM-DD para date."""
    from datetime import datetime
    return datetime.strptime(chave, "%Y-%m-%d").date()


def validar_data_intervalo(data_inicial: date, data_final: date, max_anos: int = 10) -> bool:
    """Valida se o intervalo de data está dentro dos limites permitidos.

    Regra: BCB/SGS máx. 10 anos por requisição, Yahoo Finance sem limite prático.
    """
    diff = (data_final - data_inicial).days
    max_dias = max_anos * 365
    return diff <= max_dias, diff


def decimal_para_porcentagem(valor: Decimal, casas: int = 2) -> str:
    """Formata Decimal como porcentagem string."""
    return f"{float(valor):.{casas}f}%"


def decimal_para_moeda(valor: Decimal, moeda: str = "BRL", simbolo: str = "R$") -> str:
    """Formata Decimal como string de moeda."""
    return f"{simbolo} {float(valor):,.2f}"
