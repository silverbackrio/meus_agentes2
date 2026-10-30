"""Validação pura dos atributos de posição e dos custos de operação.

Funções sem Django (P3): servem para a view, para um `manage.py` e para teste.
Não arredondam dinheiro no meio do caminho (R5) — normalizam `Decimal` para
string canônica, que é o que o `JSONField` guarda sem perder precisão.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from .esquemas import CLASSES, CUSTOS, EVENTOS_DE_SAIDA, Campo, Classe, campo

ZERO = Decimal("0")
_MAX_DECIMAL = Decimal("999999999999.99999999")


def _erro(nome: str, mensagem: str, sugestao: str) -> dict:
    return {"campo": nome, "mensagem": mensagem, "sugestao": sugestao}


def _texto_numero(valor) -> str:
    """Normaliza a grafia do número sem trocar o significado.

    Com vírgula, o texto é pt-BR ("1.494,00" → 1494.00). Sem vírgula, o ponto já
    é o separador decimal ("1494.00" continua 1494.00).
    """
    texto = str(valor).strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return texto


def _decimal(nome: str, valor, campo_ref: Campo | None) -> tuple[Decimal | None, dict | None]:
    """Converte entrada em `Decimal` não negativo, com erro nomeando o campo."""
    try:
        numero = Decimal(_texto_numero(valor))
    except (InvalidOperation, ValueError):
        return None, _erro(
            nome,
            f"{valor!r} não é número válido",
            "Use apenas dígitos e separador decimal (ex: 1500.00).",
        )
    if not numero.is_finite():
        return None, _erro(nome, "número inválido", "Informe um valor finito.")
    if numero < ZERO:
        return None, _erro(nome, "não pode ser negativo", "Informe um valor maior ou igual a zero.")
    if numero > _MAX_DECIMAL:
        return None, _erro(nome, "valor fora da faixa suportada", "Confira a unidade do campo.")
    if campo_ref is not None and campo_ref.tipo == "percentual" and numero > Decimal("100"):
        return None, _erro(nome, "percentual acima de 100%", "Informe a taxa anual em %, por exemplo 11.5.")
    return numero, None


def _booleano(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {"1", "true", "sim", "s", "on", "yes"}


def _data(nome: str, valor) -> tuple[str | None, dict | None]:
    if valor in (None, ""):
        return None, _erro(nome, "data obrigatória", "Use o formato AAAA-MM-DD.")
    try:
        return date.fromisoformat(str(valor)).isoformat(), None
    except ValueError:
        return None, _erro(nome, f"{valor!r} não está em AAAA-MM-DD", "Use o formato ISO-8601 (ex: 2026-10-29).")


def _normalizar_campo(item: Campo, valor) -> tuple[str | bool | None, dict | None]:
    """Normaliza um valor conforme o tipo declarado no campo."""
    if item.tipo == "booleano":
        return _booleano(valor), None
    if item.tipo == "data":
        return _data(item.nome, valor)
    if item.tipo in {"decimal", "percentual", "inteiro"}:
        numero, erro = _decimal(item.nome, valor, item)
        if erro is not None:
            return None, erro
        if item.tipo == "inteiro" and numero != numero.to_integral_value():
            return None, _erro(item.nome, "precisa ser número inteiro", "Informe dias inteiros, sem casas decimais.")
        return format(numero, "f"), None
    texto = str(valor).strip()
    if item.tipo == "opcao":
        if texto not in item.opcoes:
            return None, _erro(
                item.nome,
                f"{texto!r} não é opção válida",
                f"Use uma de: {', '.join(item.opcoes)}.",
            )
        return texto, None
    return texto, None


def validar_atributos(classe_nome: str, atributos: dict | None) -> tuple[dict, list[dict]]:
    """Valida e normaliza os atributos de uma posição da classe informada."""
    achada = CLASSES.get(classe_nome)
    if achada is None:
        return {}, [
            _erro(
                "classe",
                f"{classe_nome!r} não é uma classe suportada",
                f"Use uma de: {', '.join(sorted(CLASSES))}.",
            )
        ]

    entrada = atributos if isinstance(atributos, dict) else {}
    normalizado: dict = {}
    erros: list[dict] = []

    for item in achada.campos:
        valor = entrada.get(item.nome)
        vazio = valor is None or (isinstance(valor, str) and not valor.strip())
        if vazio:
            if item.obrigatorio and item.tipo != "booleano":
                erros.append(
                    _erro(
                        item.nome,
                        f"{item.rotulo} é obrigatório para {achada.rotulo}",
                        f"Preencha '{item.rotulo}'.",
                    )
                )
            continue
        convertido, erro = _normalizar_campo(item, valor)
        if erro is not None:
            erros.append(erro)
            continue
        normalizado[item.nome] = convertido

    conhecidos = {item.nome for item in achada.campos}
    for nome in entrada:
        if nome not in conhecidos:
            erros.append(
                _erro(
                    nome,
                    "campo não pertence a esta classe",
                    f"Campos de {achada.rotulo}: {', '.join(sorted(conhecidos))}.",
                )
            )

    return normalizado, erros


def validar_custos(custos: dict | None) -> tuple[dict, list[dict]]:
    """Valida e normaliza os custos; devolve só os campos informados e não nulos."""
    entrada = custos if isinstance(custos, dict) else {}
    normalizado: dict = {}
    erros: list[dict] = []

    conhecidos = {item.nome for item in CUSTOS}
    for nome in entrada:
        if nome not in conhecidos:
            erros.append(_erro(nome, "custo desconhecido", f"Custos aceitos: {', '.join(sorted(conhecidos))}."))

    for item in CUSTOS:
        valor = entrada.get(item.nome)
        if valor in (None, ""):
            continue
        numero, erro = _decimal(item.nome, valor, item)
        if erro is not None:
            erros.append(erro)
            continue
        if numero != ZERO:
            normalizado[item.nome] = format(numero, "f")

    return normalizado, erros


def total_custos(custos: dict) -> Decimal:
    """Soma dos custos informados, em BRL."""
    total = ZERO
    for valor in custos.values():
        total += Decimal(str(valor))
    return total


def efeito_financeiro(evento: str, valor: Decimal, custos: dict) -> Decimal:
    """Quanto sai (ou entra) do bolso, já com os custos.

    Aplicação: valor **mais** custos (desembolso).
    Saída (venda, resgate, amortização, encerramento): valor **menos** custos.
    Demais eventos (provento, IR, taxa): o valor já é o efeito — somar custo de
    novo contaria duas vezes o mesmo dinheiro.
    """
    total = total_custos(custos)
    if evento == "aplicacao":
        return valor + total
    if evento in EVENTOS_DE_SAIDA:
        return valor - total
    return valor


def evento_permitido(classe_nome: str, evento: str) -> bool:
    """Diz se o evento faz sentido para a classe (ex: 'provento' não existe em CDB)."""
    achada = CLASSES.get(classe_nome)
    return achada is not None and evento in achada.eventos


def campos_da_classe(classe_nome: str) -> tuple[Campo, ...]:
    """Atalho para os campos de uma classe (usado em validação de obrigatórios)."""
    achada = CLASSES.get(classe_nome)
    return achada.campos if achada is not None else ()


__all__ = [
    "Classe",
    "campo",
    "campos_da_classe",
    "efeito_financeiro",
    "evento_permitido",
    "total_custos",
    "validar_atributos",
    "validar_custos",
]
