"""Registro de layouts de documento.

Cada layout é um par (detector, parser) registrado numa tupla. Documento novo
entra como **novo módulo + uma linha aqui**, sem tocar no parser existente
(princípio P4). O detector devolve confiança de 0 a 1; a escolha é sempre o
layout de maior confiança, e abaixo do piso a leitura é recusada em vez de
chutada (R14).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from .nota_corretagem import NotaExtraida, detectar, parse

CONFIANCA_MINIMA = Decimal("0.5")


@dataclass(frozen=True)
class Layout:
    """Layout de documento: nome, tipo, detector e parser puro."""

    nome: str
    tipo: str
    detectar: Callable[[str], Decimal]
    parse: Callable[[str], NotaExtraida]


LAYOUTS: tuple[Layout, ...] = (
    Layout(
        nome="nota_corretagem_b3",
        tipo="nota_corretagem",
        detectar=detectar,
        parse=parse,
    ),
)


def melhor_layout(texto: str, tipo: str | None = None) -> tuple[Layout, Decimal]:
    """Escolhe o layout de maior confiança, opcionalmente restrito a um `tipo`."""
    candidatos = [layout for layout in LAYOUTS if tipo in (None, "", layout.tipo)] or list(LAYOUTS)
    pontuados = [(layout, layout.detectar(texto)) for layout in candidatos]
    return max(pontuados, key=lambda par: par[1])
