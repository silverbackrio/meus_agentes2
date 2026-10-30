"""Registro declarativo das classes de investimento.

Uma única fonte de verdade para: (a) o formulário do frontend, que é **gerado** a
partir daqui; (b) a validação do backend; (c) os eventos e custos aceitos por
classe. O React não duplica regra — ele só desenha o campo que a API descreve
(R4: o front não calcula nem decide regra de domínio).

Campo novo numa classe = uma linha aqui. Classe nova = um bloco aqui. Nenhum
outro módulo precisa mudar (P4).

`tipo` do campo diz como desenhar e como validar:
`texto`, `decimal`, `percentual`, `inteiro`, `data`, `opcao`, `booleano`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Campo:
    """Campo do formulário de posição, com a regra de validação embutida."""

    nome: str
    rotulo: str
    tipo: str = "texto"
    obrigatorio: bool = False
    unidade: str = ""
    opcoes: tuple[str, ...] = ()
    ajuda: str = ""


@dataclass(frozen=True)
class Classe:
    """Classe de investimento: rótulo, campos próprios e eventos aceitos."""

    nome: str
    rotulo: str
    campos: tuple[Campo, ...]
    eventos: tuple[str, ...]
    nota: str = ""


# Nomes de evento que a carteira entende (iguais aos de `Operacao.evento`).
EVENTOS = {
    "aplicacao": "Aplicação / compra",
    "venda": "Venda (bolsa)",
    "resgate": "Resgate",
    "amortizacao": "Amortização",
    "distribuicao": "Distribuição / rendimento",
    "beneficio": "Benefício",
    "provento": "Provento (dividendo/JCP)",
    "ir_pago": "IR pago",
    "taxa": "Taxa / custo avulso",
    "encerramento": "Encerramento da posição",
}

# Eventos de saída: reduzem a posição e podem encerrá-la.
EVENTOS_DE_SAIDA = ("venda", "resgate", "amortizacao", "encerramento")

EVENTOS_BOLSA = ("aplicacao", "venda", "provento", "ir_pago", "taxa", "encerramento")
EVENTOS_FUNDO = ("aplicacao", "resgate", "distribuicao", "ir_pago", "taxa", "encerramento")
EVENTOS_RENDA_FIXA = ("aplicacao", "resgate", "amortizacao", "ir_pago", "taxa", "encerramento")

_INDEXADOR = Campo(
    "indexador",
    "Indexador",
    "opcao",
    obrigatorio=True,
    opcoes=("CDI", "SELIC", "IPCA", "prefixado", "IGP-M", "outro"),
    ajuda="CDI/SELIC/IPCA para pós-fixado; 'prefixado' para taxa fixa.",
)
_EMISSOR = Campo("emissor", "Emissor", "texto", obrigatorio=True, ajuda="Banco, securitizadora ou tesouro.")
_TAXA = Campo("taxa", "Taxa contratada", "percentual", obrigatorio=True, unidade="% a.a.", ajuda="Taxa efetiva anual.")
_VENCIMENTO = Campo("vencimento", "Vencimento", "data", obrigatorio=True)
_CARENCIA = Campo("carencia_dias", "Carência", "inteiro", unidade="dias", ajuda="Dias sem resgate.")
_LIQUIDEZ = Campo("liquidez_diaria", "Liquidez diária", "booleano")
_FGC = Campo("fgc", "Coberto pelo FGC", "booleano", ajuda="Até o limite vigente do FGC; confirme a regra atual.")
_CUSTODIA_B3 = Campo(
    "custodia_b3",
    "Custódia B3",
    "percentual",
    unidade="% a.a.",
    ajuda="0,20% a.a. com exceções — confirme a tabela vigente.",
)

CLASSES: dict[str, Classe] = {
    "acoes": Classe(
        nome="acoes",
        rotulo="Ações",
        eventos=EVENTOS_BOLSA,
        campos=(
            Campo("tipo_acao", "Tipo", "opcao", obrigatorio=True, opcoes=("ON", "PN", "UNT", "BDR")),
            Campo("corretora", "Corretora", "texto"),
            Campo("proventos_12m", "Proventos 12m", "decimal", unidade="R$/ação", ajuda="Base do yield on cost."),
        ),
    ),
    "etf": Classe(
        nome="etf",
        rotulo="ETF",
        eventos=EVENTOS_BOLSA,
        campos=(
            Campo("indice_referencia", "Índice de referência", "texto", obrigatorio=True),
            Campo("taxa_admin", "Taxa de administração", "percentual", unidade="% a.a."),
            Campo("corretora", "Corretora", "texto"),
        ),
    ),
    "fiis": Classe(
        nome="fiis",
        rotulo="FII / FI-Infra",
        eventos=EVENTOS_BOLSA,
        campos=(
            Campo(
                "tipo_fii",
                "Segmento",
                "opcao",
                obrigatorio=True,
                opcoes=("tijolo", "papel", "fundo_de_fundos", "hibrido", "infra"),
            ),
            Campo("taxa_admin", "Taxa de administração", "percentual", unidade="% a.a."),
            Campo("rendimento_mensal", "Rendimento mensal", "decimal", unidade="R$/cota"),
        ),
    ),
    "fundo": Classe(
        nome="fundo",
        rotulo="Fundo de investimento",
        eventos=EVENTOS_FUNDO,
        campos=(
            Campo("cnpj", "CNPJ do fundo", "texto", obrigatorio=True),
            Campo("cota_atual", "Cota atual", "decimal", unidade="R$/cota"),
            Campo("taxa_admin", "Taxa de administração", "percentual", unidade="% a.a."),
            Campo("taxa_performance", "Taxa de performance", "percentual", unidade="% do excedente"),
            Campo("come_cotas", "Sujeito a come-cotas", "booleano", ajuda="Aplicável a fundos de renda fixa/DIM."),
            Campo("prazo_resgate_dias", "Prazo de resgate", "inteiro", unidade="dias"),
            Campo("carencia_dias", "Carência", "inteiro", unidade="dias"),
        ),
    ),
    "cdb": Classe(
        nome="cdb",
        rotulo="CDB",
        eventos=EVENTOS_RENDA_FIXA,
        campos=(_EMISSOR, _INDEXADOR, _TAXA, _VENCIMENTO, _CARENCIA, _LIQUIDEZ, _FGC),
    ),
    "lci_lca": Classe(
        nome="lci_lca",
        rotulo="LCI / LCA",
        eventos=EVENTOS_RENDA_FIXA,
        nota="Isento de IR para pessoa física (Lei 11.033/2004) — vigente em 2026.",
        campos=(_EMISSOR, _INDEXADOR, _TAXA, _VENCIMENTO, _CARENCIA, _FGC),
    ),
    "cri_cra": Classe(
        nome="cri_cra",
        rotulo="CRI / CRA",
        eventos=EVENTOS_RENDA_FIXA,
        nota="Isento de IR para pessoa física; risco é do emissor/devedor, sem FGC.",
        campos=(
            Campo("emissor", "Securitizadora", "texto", obrigatorio=True),
            Campo("devedor", "Devedor do lastro", "texto"),
            _INDEXADOR,
            _TAXA,
            _VENCIMENTO,
            Campo("rating", "Rating", "texto"),
        ),
    ),
    "debenture": Classe(
        nome="debenture",
        rotulo="Debênture",
        eventos=EVENTOS_RENDA_FIXA,
        nota="Só é incentivada com emissão enquadrada na Lei 12.431/2011 — confirme no material de oferta.",
        campos=(
            _EMISSOR,
            _INDEXADOR,
            _TAXA,
            _VENCIMENTO,
            Campo("incentivada", "Incentivada (Lei 12.431)", "booleano"),
            Campo("rating", "Rating", "texto"),
        ),
    ),
    "tesouro_direto": Classe(
        nome="tesouro_direto",
        rotulo="Tesouro Direto",
        eventos=EVENTOS_RENDA_FIXA,
        nota="IR incide sobre o rendimento; no NTN-B o principal é isento (renda-fixa.md R4).",
        campos=(
            Campo(
                "titulo",
                "Título",
                "opcao",
                obrigatorio=True,
                opcoes=(
                    "Tesouro Selic",
                    "Tesouro Prefixado",
                    "Tesouro IPCA+",
                    "Tesouro IPCA+ com juros semestrais",
                ),
            ),
            _INDEXADOR,
            _TAXA,
            _VENCIMENTO,
            _CUSTODIA_B3,
        ),
    ),
    "ouro": Classe(
        nome="ouro",
        rotulo="Ouro",
        eventos=EVENTOS_BOLSA,
        campos=(
            Campo("forma", "Forma", "opcao", obrigatorio=True, opcoes=("fisico", "etf", "fracionado", "conta")),
            Campo("gramatura", "Gramatura", "decimal", unidade="g"),
            Campo("pureza", "Pureza", "decimal", unidade="0-1"),
            Campo("custodia", "Custódia", "decimal", unidade="R$/mês"),
        ),
    ),
    "previdencia": Classe(
        nome="previdencia",
        rotulo="Previdência",
        eventos=EVENTOS_FUNDO,
        campos=(
            Campo("tipo_plano", "Tipo de plano", "opcao", obrigatorio=True, opcoes=("PGBL", "VGBL")),
            Campo("plano", "Plano / seguradora", "texto", obrigatorio=True),
            Campo("regime_tributario", "Regime", "opcao", obrigatorio=True, opcoes=("progressivo", "regressivo")),
            Campo("taxa_carregamento", "Carregamento", "percentual", unidade="%"),
            Campo("taxa_admin", "Taxa de administração", "percentual", unidade="% a.a."),
        ),
    ),
    "cambio": Classe(
        nome="cambio",
        rotulo="Câmbio / moeda estrangeira",
        eventos=("aplicacao", "venda", "ir_pago", "taxa", "encerramento"),
        campos=(
            Campo("moeda_estrangeira", "Moeda", "opcao", obrigatorio=True, opcoes=("USD", "EUR", "GBP", "outra")),
            Campo("forma", "Forma", "opcao", obrigatorio=True, opcoes=("conta", "especie", "cartao")),
        ),
    ),
}

# Custos e impostos aceitos em qualquer evento. Valor em BRL (R5: Decimal).
CUSTOS: tuple[Campo, ...] = (
    Campo("corretagem", "Corretagem", "decimal", unidade="R$"),
    Campo("emolumentos", "Emolumentos", "decimal", unidade="R$"),
    Campo("taxas_bolsa", "Taxas B3", "decimal", unidade="R$"),
    Campo("custodia", "Custódia", "decimal", unidade="R$"),
    Campo("ir", "IR retido/pago", "decimal", unidade="R$"),
    Campo("iof", "IOF", "decimal", unidade="R$"),
    Campo("outros", "Outros custos", "decimal", unidade="R$"),
)


def classe(nome: str) -> Classe | None:
    """Devolve a classe pelo nome, ou `None` se não existir."""
    return CLASSES.get(nome)


def campo(classe_nome: str, campo_nome: str) -> Campo | None:
    """Devolve um campo específico de uma classe."""
    achada = CLASSES.get(classe_nome)
    if achada is None:
        return None
    for item in achada.campos:
        if item.nome == campo_nome:
            return item
    return None
