"""Funções puras de renda fixa — comparação justa em base líquida.

Autoridade de cálculo: ``specs/renda-fixa.md`` (R1, R2, R5, R6) e a skill
``renda-fixa-brasil``. Princípio P3 e regra R4 de ``specs/aplicacao.md``: aqui
**não existe Django** — a view só valida a entrada e monta o envelope datado
da R2; quem chama (view, comando, teste) recebe ``Decimal`` e a fórmula.

Duas decisões que a spec exige e este módulo cumpre:

1. **Base de dias declarada**: todo cálculo usa ``DIAS_BASE = 360`` dias
   corridos por ano e a resposta diz qual é — a armadilha clássica é trocar
   252 úteis por 360 corridos sem avisar (erro 2 da skill renda-fixa-brasil).
2. **IR pela faixa do prazo** (renda-fixa.md R2): 22,5% até 180 dias; 20% de
   181 a 360; 17,5% de 361 a 720; 15% acima de 720 — Lei 11.033/2004,
   vigente em 2026. Produto isento (LCI, LCA, CRI, CRA — art. 3º da mesma
   lei, vigente em 2026) vem marcado como entrada explícita ``isento=True``:
   quem chama declara a natureza do produto, o módulo não adivinha (R6).

Comparação justa (R5): os produtos são equivalenciados para um **prazo comum
em base líquida** — cada resultado líquido é anualizado e projetado até o
prazo comum, então um CDB tributado de 720 dias e uma LCI isenta de 360 dias
ficam comparáveis de verdade. Nada de ordenar por retorno bruto.

Toda entrada inválida levanta ``ValueError`` com a mensagem no formato
``"campo: motivo"`` — a view transforma no envelope ``{erro, campo, sugestao}``.
"""

from decimal import Decimal

from .calculos import ZERO, _decimal, _positivo

UM = Decimal("1")
_EXP = Decimal("0.0001")  # arredondamento só na borda (R5)

# Convenção de dias do módulo: 360 dias corridos por ano (declarada na API).
DIAS_BASE = 360

# IOF regressivo zera no 30º dia (Decreto 6.306/2007, vigente em 2026).
# Em vez de memorizar a tabela dia a dia, o módulo recusa prazo < 30 dias e
# diz por quê — incerteza declarada em vez de número inventado (R4 do
# compliance-e-avisos.md).
LIMITE_IOF_DIAS = 30

NORMA_IR = "Lei 11.033/2004 — tabela regressiva de IR de renda fixa, vigente em 2026"
NORMA_ISSENCAO = "Lei 11.033/2004, art. 3º — isenção de LCI, LCA, CRI e CRA, vigente em 2026"
NORMA_IOF = "Decreto 6.306/2007 — IOF regressivo sobre o rendimento, zera no 30º dia"

# renda-fixa.md R2: (limite do prazo em dias, alíquota, faixa).
FAIXAS_IR = (
    (180, Decimal("0.225"), "até 180 dias"),
    (360, Decimal("0.20"), "de 181 a 360 dias"),
    (720, Decimal("0.175"), "de 361 a 720 dias"),
    (None, Decimal("0.15"), "acima de 720 dias"),
)

# Critérios de aceite de renda-fixa.md: riscos listados em toda comparação.
# O texto evita verbos de ordem ("compre"/"venda"/"aloque") para a regra R9
# da aplicacao.md passar também no teste automatizado de texto.
RISCOS = (
    "liquidez: o resgate antes do prazo pode depender de preço de mercado, não da taxa contratada",
    "crédito: FGC cobre até R$ 250 mil por CPF por instituição; CRI, CRA e "
    "debêntures não têm cobertura (renda-fixa.md R9)",
    "marcação a mercado: o resgate antecipado usa o preço da taxa vigente na data-base, não a taxa contratada",
    "inflação: retorno real depende da inflação do período — taxa nominal não é retorno real",
)


def _inteiro(valor, campo: str) -> int:
    """Converte prazo/dias em ``int`` com erro que aponta o campo."""
    if isinstance(valor, bool) or valor is None:
        raise ValueError(f"{campo}: informe um número inteiro de dias")
    if isinstance(valor, int):
        return valor
    if isinstance(valor, Decimal):
        if valor != valor.to_integral_value():
            raise ValueError(f"{campo}: {valor} não é um inteiro de dias")
        return int(valor)
    if isinstance(valor, str):
        texto = valor.strip()
        try:
            return int(texto)
        except ValueError as exc:
            raise ValueError(f"{campo}: {valor!r} não é um inteiro de dias") from exc
    raise ValueError(f"{campo}: tipo {type(valor).__name__} não é um prazo em dias")


def aliquota_ir(prazo_dias):
    """Alíquota de IR pelo prazo em dias corridos.

    Tabela regressiva de renda fixa (renda-fixa.md R2, Lei 11.033/2004,
    vigente em 2026). Devolve ``(aliquota, faixa)`` — a view publica os dois,
    porque a spec exige "a alíquota de IR vem da faixa do prazo, com a norma".

    >>> aliquota_ir(360) == (Decimal("0.20"), "de 181 a 360 dias")
    """
    prazo = _inteiro(prazo_dias, "prazo_dias")
    if prazo <= 0:
        raise ValueError(f"prazo_dias: precisa ser positivo (recebido {prazo})")
    for limite, aliquota, faixa in FAIXAS_IR:
        if limite is None or prazo <= limite:
            return aliquota, faixa
    raise AssertionError("faixa sem limite final deveria existir")  # pragma: no cover


def taxa_equivalente(taxa_origem, dias_origem, dias_destino):
    """Equivalência de taxas: ``(1 + i_origem)^n_origem = (1 + i_destino)^n_destino``.

    Fórmula da spec (renda-fixa.md, "Cálculos obrigatórios"). É o que
    permite comparar produtos de prazos diferentes sem mentir (R5).
    """
    taxa = _decimal(taxa_origem, "taxa")
    if taxa <= -UM:
        raise ValueError(f"taxa: {taxa} não pode ser menor que -100%")
    origem = _inteiro(dias_origem, "dias_origem")
    destino = _inteiro(dias_destino, "dias_destino")
    if origem <= 0 or destino <= 0:
        raise ValueError("dias: prazos precisam ser positivos para equivaler taxas")
    expoente = Decimal(origem) / Decimal(destino)
    return (UM + taxa) ** expoente - UM


def valor_futuro(vi, taxa_a_a, prazo_dias, dias_base: int = DIAS_BASE):
    """``VF = VI * (1 + i)^n`` com i e n na mesma base de tempo.

    ``taxa_a_a`` é taxa efetiva anual em decimal (0.10 = 10% a.a.),
    ``prazo_dias`` em dias corridos e ``n = prazo_dias / dias_base``.
    """
    valor = _positivo(vi, "valor_inicial")
    taxa = _decimal(taxa_a_a, "taxa")
    if taxa <= -UM:
        raise ValueError(f"taxa: {taxa} não pode ser menor que -100%")
    prazo = _inteiro(prazo_dias, "prazo_dias")
    if prazo <= 0:
        raise ValueError(f"prazo_dias: precisa ser positivo (recebido {prazo})")
    base = _inteiro(dias_base, "dias_base")
    if base <= 0:
        raise ValueError(f"dias_base: precisa ser positivo (recebido {base})")
    return valor * (UM + taxa) ** (Decimal(prazo) / Decimal(base))


def comparar_produtos(produtos, valor_inicial, prazo_comum=None):
    """Compara produtos em **base líquida** com prazos equivalenciados (R5).

    Entrada: lista de ``{"nome", "taxa", "prazo_dias", "isento"}`` — taxa em
    % a.a. (10 = 10% a.a.), prazo em dias corridos, ``isento`` declara
    LCI/LCA/CRI/CRA. ``valor_inicial`` (VI) é obrigatório porque o líquido é
    calculado sobre ele; ``prazo_comum`` sem valor usa o maior prazo dos
    produtos. Taxas saem daqui em fração (0.10 = 10% a.a.) — quem formata
    para a tela é a view.

    Para cada produto, na ordem dada (sem ranking — R9):
    1. VF = VI * (1 + i)^(n/360);
    2. IR = rendimento * alíquota da faixa do prazo (zero se isento);
    3. ``rendimento_liquido`` = VF - VI - IR - IOF (fórmula literal da spec) e
       ``valor_recebido`` = VF - IR - IOF (o que volta ao final, incluindo o
       principal — é sobre ele que a comparação projeta);
    4. taxa líquida anualizada = (valor_recebido/VI)^(360/n) - 1;
    5. valor recebido projetado no prazo comum com essa taxa líquida.

    Todo o resultado vem em ``Decimal``: o arredondamento é da borda (view).
    """
    if not produtos:
        raise ValueError("ativos: informe ao menos um produto para comparar")
    vi = _positivo(valor_inicial, "valor_inicial")

    # Valida todas as entradas antes de calcular qualquer coisa.
    validados = []
    for produto in produtos:
        nome = str(produto.get("nome") or "").strip()
        if not nome:
            raise ValueError("nome: cada produto precisa de um nome")
        taxa_pct = _decimal(produto.get("taxa"), "taxa")
        if taxa_pct < ZERO:
            raise ValueError(f"taxa: {nome}: não pode ser negativa (recebido {taxa_pct} % a.a.)")
        taxa = taxa_pct / 100  # % a.a. → fração (0.10 = 10% a.a.)
        prazo = _inteiro(produto.get("prazo_dias"), "prazo_dias")
        if prazo <= 0:
            raise ValueError(f"prazo_dias: {nome}: precisa ser positivo (recebido {prazo})")
        if prazo < LIMITE_IOF_DIAS:
            raise ValueError(
                f"prazo_dias: {nome}: {prazo} dias fica antes do 30º dia e o IOF "
                f"regressivo (Decreto 6.306/2007) não está calculado neste módulo; "
                f"use prazo de ao menos {LIMITE_IOF_DIAS} dias"
            )
        validados.append(
            {"nome": nome, "taxa": taxa, "prazo_dias": prazo, "isento": bool(produto.get("isento"))}
        )

    if prazo_comum is None:
        prazo_comum = max(item["prazo_dias"] for item in validados)
    else:
        prazo_comum = _inteiro(prazo_comum, "prazo_comum_dias")
        if prazo_comum <= 0:
            raise ValueError(f"prazo_comum_dias: precisa ser positivo (recebido {prazo_comum})")

    itens = []
    for item in validados:
        if item["isento"]:
            aliquota, faixa = ZERO, "isento"
        else:
            aliquota, faixa = aliquota_ir(item["prazo_dias"])

        vf = valor_futuro(vi, item["taxa"], item["prazo_dias"])
        rendimento = vf - vi
        imposto = rendimento * aliquota
        iof = ZERO  # prazo ≥ 30º dia: IOF zerou (Decreto 6.306/2007)
        # Spec renda-fixa.md: "líquido = VF - VI - (rendimento * alíquota) - IOF".
        rendimento_liquido = vf - vi - imposto - iof
        # O que o investidor recebe de volta no final (principal + ganho líquido).
        valor_recebido = vf - imposto - iof

        # Líquido anualizado: (valor_recebido/VI)^(dias_base/prazo) - 1 — é isso
        # que torna produtos de prazos diferentes comparáveis em base líquida.
        taxa_liquida = (valor_recebido / vi) ** (Decimal(DIAS_BASE) / Decimal(item["prazo_dias"])) - UM
        valor_no_comum = vi * (UM + taxa_liquida) ** (Decimal(prazo_comum) / Decimal(DIAS_BASE))

        # Taxa bruta equivalenciada pelo mesmo prazo comum, para o leitor ver
        # as duas contas lado a lado (equivalência da spec: (1+i_a)^n_a = …).
        taxa_bruta_no_comum = taxa_equivalente(taxa, item["prazo_dias"], prazo_comum)

        itens.append(
            {
                "nome": item["nome"],
                "prazo_dias": item["prazo_dias"],
                "isento": item["isento"],
                "taxa_bruta": item["taxa"],
                "aliquota_ir": aliquota,
                "faixa_ir": faixa,
                "valor_futuro": vf,
                "rendimento": rendimento,
                "imposto": imposto,
                "iof": iof,
                "rendimento_liquido": rendimento_liquido,
                "valor_recebido": valor_recebido,
                "taxa_liquida_aa": taxa_liquida,
                "valor_recebido_no_prazo_comum": valor_no_comum,
                "taxa_bruta_no_prazo_comum": taxa_bruta_no_comum,
            }
        )

    return {"prazo_comum_dias": prazo_comum, "valor_inicial": vi, "itens": itens}
