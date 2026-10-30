"""Parser puro de nota de corretagem da B3.

Aprendizado inicial: a nota de 29/10/2026 usada como referência traz, na seção
"Negociações", uma linha por negócio no formato

    1-BOVESPA C D2S BBAS BBAS3 ON NM 90 16,60 1.494,00 D

e, logo abaixo de cada ativo, uma linha de total ("Quantidade Total: ...").
O parser lê **só as linhas de negócio** — a linha de total é conferência, nunca
lançamento. Nada aqui toca Django nem banco: é função pura (P3), testada com
fixture dourada (R6).

Números vêm em pt-BR ("1.494,00"): ponto é separador de milhar, vírgula é
decimal. Quantidade/preço/valor são `Decimal` (R5), nunca `float`.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

LAYOUT = "nota_corretagem_b3"

_NUMERO = r"\d{1,3}(?:\.\d{3})*,\d{2,4}"
_RE_LINHA = re.compile(
    rf"^(?P<negociacao>\d+-[A-ZÀ-Ú]+)\s+(?P<lado>[CV])\s+(?P<mercado>\S+)\s+"
    rf"(?P<especificacao>.+?)\s+(?P<quantidade>\d{{1,3}}(?:\.\d{{3}})*)\s+"
    rf"(?P<preco>{_NUMERO})\s+(?P<valor>{_NUMERO})\s+(?P<dc>[DC])$"
)
_RE_DATA = re.compile(r"Data\s+preg[ãa]o\s*:?\s*(?P<data>\d{2}/\d{2}/\d{4})", re.IGNORECASE)
_RE_NOTA = re.compile(r"N[º°o]?\s*\.?\s*Nota\s*:?\s*(?P<numero>\d+)", re.IGNORECASE)
_RE_TOTAL = re.compile(
    r"Quantidade\s+Total\s*:\s*(?P<quantidade>[\d.]+)\s+Pre[çc]o\s+M[ée]dio\s*:\s*(?P<preco>[\d.,]+)",
    re.IGNORECASE,
)
_RE_CORRETORA = re.compile(
    r"Agente\s+de\s+compensa[çc][ãa]o\s*:?\s*(?P<nome>[^\n]{3,})", re.IGNORECASE
)

TOLERANCIA_DIVERGENCIA = Decimal("0.05")


class ErroLayout(ValueError):
    """Documento fora do layout esperado, no envelope `{erro, campo, sugestao}`."""

    def __init__(self, campo: str, mensagem: str, sugestao: str = "") -> None:
        super().__init__(f"{campo}: {mensagem}")
        self.campo = campo
        self.mensagem = mensagem
        self.sugestao = sugestao


def numero_br(texto: str) -> Decimal:
    """Converte número em pt-BR ("1.494,00") em `Decimal`."""
    limpo = texto.strip().replace(".", "").replace(",", ".")
    try:
        return Decimal(limpo)
    except InvalidOperation as exc:
        raise ErroLayout("numero", f"{texto!r} não é número no formato pt-BR") from exc


@dataclass
class Negocio:
    """Um negócio da nota."""

    linha: int
    data: date
    ativo: str
    codigo: str
    mercado: str
    especificacao: str
    lado: str
    quantidade: Decimal
    preco: Decimal
    valor: Decimal
    debito_credito: str
    avisos: list[str] = field(default_factory=list)


@dataclass
class TotalPorAtivo:
    """Linha de total que a própria nota imprime por ativo."""

    especificacao: str
    quantidade: Decimal
    preco_medio: Decimal


@dataclass
class NotaExtraida:
    """Resultado da leitura de uma nota de corretagem."""

    layout: str
    data_pregao: date
    numero_nota: str
    corretora: str
    negocios: list[Negocio]
    totais: list[TotalPorAtivo]
    avisos: list[str] = field(default_factory=list)


def detectar(texto: str) -> Decimal:
    """Confiança de 0 a 1 de que o texto é uma nota de corretagem da B3."""
    if not texto or not texto.strip():
        return Decimal("0")
    baixo = texto.lower()
    pontos = Decimal("0")
    if _RE_DATA.search(texto):
        pontos += Decimal("0.4")
    if "c/v" in baixo:
        pontos += Decimal("0.25")
    if "negocia" in baixo:
        pontos += Decimal("0.25")
    if "pre" in baixo and "ajuste" in baixo:
        pontos += Decimal("0.1")
    return min(pontos, Decimal("1"))


def parse(texto: str) -> NotaExtraida:
    """Lê o texto da nota e devolve negócios, totais e avisos."""
    if not texto or not texto.strip():
        raise ErroLayout("documento", "texto vazio", "Envie o PDF ou o texto da nota.")

    achado_data = _RE_DATA.search(texto)
    if achado_data is None:
        raise ErroLayout(
            "data_pregao",
            "não encontrei a data do pregão",
            "A nota da B3 traz 'Data pregão' no cabeçalho, no formato DD/MM/AAAA.",
        )
    dia, mes, ano = achado_data.group("data").split("/")
    data_pregao = date(int(ano), int(mes), int(dia))

    numero_nota = achado_data_nota.group("numero") if (achado_data_nota := _RE_NOTA.search(texto)) else ""
    corretora = _corretora(texto)

    negocios: list[Negocio] = []
    totais: list[TotalPorAtivo] = []
    avisos: list[str] = []

    for numero_linha, linha in enumerate(texto.splitlines(), start=1):
        limpa = linha.strip()
        if not limpa:
            continue

        total = _RE_TOTAL.search(limpa)
        if total is not None:
            totais.append(
                TotalPorAtivo(
                    especificacao=limpa[: total.start()].strip(),
                    quantidade=numero_br(total.group("quantidade")),
                    preco_medio=numero_br(total.group("preco")),
                )
            )
            continue

        negocio = _ler_negocio(limpa, numero_linha, data_pregao)
        if negocio is not None:
            negocios.append(negocio)

    if not negocios:
        raise ErroLayout(
            "negociacoes",
            "nenhum negócio reconhecido no documento",
            "A seção 'Negociações' da nota tem linhas como "
            "'1-BOVESPA C D2S PETR PETR4 PN N2 100 38,50 3.850,00 D'.",
        )

    avisos.extend(_conferir_totais(negocios, totais))
    return NotaExtraida(
        layout=LAYOUT,
        data_pregao=data_pregao,
        numero_nota=numero_nota,
        corretora=corretora,
        negocios=negocios,
        totais=totais,
        avisos=avisos,
    )


def _corretora(texto: str) -> str:
    achado = _RE_CORRETORA.search(texto)
    if achado is None:
        return ""
    nome = achado.group("nome").strip()
    # O campo pode vir vazio no formulário; nome curto não é nome de corretora.
    return nome if len(nome) >= 3 and not nome.startswith("-") else ""


def _ler_negocio(linha: str, numero_linha: int, data_pregao: date) -> Negocio | None:
    achado = _RE_LINHA.match(linha)
    if achado is None:
        return None

    especificacao = " ".join(achado.group("especificacao").split())
    partes = especificacao.split()
    codigo = partes[1] if len(partes) > 1 else partes[0]
    quantidade = numero_br(achado.group("quantidade"))
    preco = numero_br(achado.group("preco"))
    valor = numero_br(achado.group("valor"))

    avisos: list[str] = []
    calculado = quantidade * preco
    if abs(calculado - valor) > TOLERANCIA_DIVERGENCIA:
        avisos.append(
            f"divergência: quantidade x preço = {calculado:.2f}, "
            f"valor na nota = {valor:.2f} (linha {numero_linha})"
        )

    return Negocio(
        linha=numero_linha,
        data=data_pregao,
        ativo=codigo,
        codigo=codigo,
        mercado=achado.group("mercado"),
        especificacao=especificacao,
        lado=achado.group("lado"),
        quantidade=quantidade,
        preco=preco,
        valor=valor,
        debito_credito=achado.group("dc"),
        avisos=avisos,
    )


def _conferir_totais(negocios: list[Negocio], totais: list[TotalPorAtivo]) -> list[str]:
    """Confere a soma dos negócios contra o total que a própria nota imprime."""
    avisos: list[str] = []
    for total in totais:
        do_ativo = [n for n in negocios if n.especificacao == total.especificacao]
        if not do_ativo:
            continue
        quantidade = sum((n.quantidade for n in do_ativo), Decimal("0"))
        valor = sum((n.valor for n in do_ativo), Decimal("0"))
        if quantidade != total.quantidade:
            avisos.append(
                f"total da nota para {total.especificacao}: {total.quantidade}, "
                f"soma lida: {quantidade}"
            )
        if quantidade > 0:
            preco_medio = (valor / quantidade).quantize(Decimal("0.0001"))
            if preco_medio != total.preco_medio:
                avisos.append(
                    f"preço médio da nota para {total.especificacao}: {total.preco_medio}, "
                    f"calculado: {preco_medio}"
                )
    return avisos
