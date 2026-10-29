"""Cálculo de cobertura e de gaps de uma série — funções puras, sem Django.

Por que separado (princípio P3 e regra R4 de `specs/aplicacao.md`): **gap, não
escopo**. Antes de qualquer fetch, o projeto calcula o intervalo faltante e busca
só isso; período já coberto nunca é baixado de novo. Como essa regra decide o
custo de rede e a cota da fonte (R7), ela precisa ser teste dourado (R6) e
reutilizável pela view, pelo comando de export e pelo script de ingestão.

Frequência `diario` conta **dias úteis** (segunda a sexta): PTAX e cotação de
bolsa não têm valor em fim de semana, então sábado/domingo não são gap.
"""

from datetime import date, timedelta

# Frequências aceitas — o mesmo conjunto do model `Serie.frequencia`.
FREQUENCIAS = ("diario", "semanal", "mensal", "anual")


def _adiciona_mes(data: date, meses: int) -> date:
    """Soma meses respeitando o calendário (31/01 + 1 mês → 28/02 em ano comum)."""
    total = (data.year * 12 + data.month - 1) + meses
    ano, mes = divmod(total, 12)
    mes += 1
    ultimo_dia = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28,
                  31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]
    return data.replace(year=ano, month=mes, day=min(data.day, ultimo_dia))


def datas_esperadas(de: date, ate: date, frequencia: str):
    """Gera as datas que **deveriam** existir na série entre `de` e `ate` (inclusive).

    `diario` pula sábado e domingo; `semanal` repete o dia da semana de `de`;
    `mensal` e `anual` avançam pelo calendário (31/01 + 1 mês = 28/02 em ano
    comum). Frequência desconhecida levanta `ValueError` apontando o campo.
    """
    if frequencia not in FREQUENCIAS:
        raise ValueError(f"frequencia: {frequencia!r} não é uma das aceitas {FREQUENCIAS}")
    if de > ate:
        raise ValueError(f"periodo: 'de' ({de}) não pode ser posterior a 'ate' ({ate})")

    if frequencia == "diario":
        atual = de
        while atual <= ate:
            if atual.weekday() < 5:  # 0=segunda ... 6=domingo
                yield atual
            atual += timedelta(days=1)
        return

    passo = {"semanal": timedelta(days=7)}[frequencia] if frequencia == "semanal" else None
    atual = de
    while atual <= ate:
        yield atual
        if frequencia == "semanal":
            atual += passo
        elif frequencia == "mensal":
            atual = _adiciona_mes(atual, 1)
        else:  # anual
            atual = _adiciona_mes(atual, 12)


def calcular_gaps(datas_existentes, de: date, ate: date, frequencia: str) -> list[tuple[date, date]]:
    """Intervalos faltantes da série no período, como pares `(de, ate)`.

    `datas_existentes` é qualquer iterável de `date` (normalmente o `.values_list`
    da query). Furos internos e cauda faltante viram o mesmo tipo de intervalo —
    é o que a tela `/dados` mostra e o que a ingestão usa para pedir só o delta.

    Exemplo: existem 25/10 e 27/10, período 25→27 em `diario` → `[(26/10, 26/10)]`.
    """
    existentes = set(datas_existentes)
    gaps: list[tuple[date, date]] = []
    aberto: date | None = None
    anterior: date | None = None

    for esperada in datas_esperadas(de, ate, frequencia):
        if esperada in existentes:
            if aberto is not None:
                gaps.append((aberto, anterior))
                aberto = None
        else:
            if aberto is None:
                aberto = esperada
        anterior = esperada

    if aberto is not None:
        gaps.append((aberto, anterior))
    return gaps


def cobertura(datas_existentes, de: date, ate: date, frequencia: str) -> dict:
    """Resumo de cobertura do período: esperadas, presentes, faltantes e fração.

    A fração sai como `Decimal` (0,80 = 80% coberto) para a view arredondar na
    borda — aqui não existe `float` nem número pronto para tela.
    """
    from decimal import Decimal

    esperadas = list(datas_esperadas(de, ate, frequencia))
    existentes = set(datas_existentes)
    presentes = [d for d in esperadas if d in existentes]
    total = len(esperadas)
    return {
        "esperadas": total,
        "presentes": len(presentes),
        "faltantes": total - len(presentes),
        "fracao": Decimal(len(presentes)) / Decimal(total) if total else Decimal("0"),
        "primeira": min(presentes) if presentes else None,
        "ultima": max(presentes) if presentes else None,
    }
