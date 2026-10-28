"""
Modelos do app carteira.

Segue `specs/carteira-e-risco.md` e `specs/dominio-e-fontes.md` para o modelo
de carteira: objetivo, perfil, política, posições e operações.
V1 sem login: campo owner já nasce no schema para a v2 não exigir migração.
"""
from django.conf import settings
from django.db import models


class MetaMixin:
    """Mixin para todos os modelos têm owner (user ou_none na v1)."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)s_set",
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        abstract = True


class Objetivo(MetaMixin):
    """Objetivo financeiro: valor-alvo, unidade (real/nominal), horizonte."""

    UNIDADE_REAIS = "reais"
    UNIDADE_NOMINAIS = "nominais"
    UNIDADE_CHOICES = [
        (UNIDADE_REAIS, "Reais"),
        (UNIDADE_NOMINAIS, "Nominais"),
    ]

    nome = models.CharField("nome", max_length=200)
    valor_alvo = models.DecimalField("valor alvo", max_digits=20, decimal_places=2)
    unidade = models.CharField(
        "unidade", max_length=20, choices=UNIDADE_CHOICES, default=UNIDADE_REAIS
    )
    horizonte_dias = models.PositiveIntegerField("horizonte em dias", default=360)
    liquidez_necessaria = models.DecimalField(
        "liquidez necessária", max_digits=12, decimal_places=2, default=0
    )

    def __str__(self):
        return f"{self.nome} — {self.valor_alvo} {self.unidade}"


class Perfil(MetaMixin):
    """Perfil de investidor: tolerância, capacidade, restrições."""

    tolerancia = models.CharField(
        "tolerância", max_length=20,
        choices=[
            ("baixa", "Baixa"),
            ("media", "Média"),
            ("alta", "Alta"),
        ],
        default="media",
    )
    capacidade_risco = models.CharField(
        "capacidade de risco", max_length=20,
        choices=[
            ("baixa", "Baixa"),
            ("media", "Média"),
            ("alta", "Alta"),
        ],
        default="media",
    )
    restricoes = models.TextField(
        "restrições", blank=True, default=""
    )

    def __str__(self):
        return f"Perfil {self.tolerancia}/{self.capacidade_risco}"


class Politica(MetaMixin):
    """Política de alocação: classe, peso alvo, faixa de tolerância."""

    CLASSE_CHOICES = [
        ("acoes", "Ações"),
        ("renda_fixa", "Renda Fixa"),
        ("fundo", "Fundos"),
        ("fiis", "FIIs"),
        ("previdencia", "Previdência"),
        ("caixa", "Caixa"),
        ("cambio", "Câmbio"),
        ("ouro", "Ouro"),
        ("petroleo", "Petróleo"),
        ("vetor", "Vetor (ETFs/Derivados)"),
    ]

    classe = models.CharField(
        "classe", max_length=20, choices=CLASSE_CHOICES
    )
    peso_alvo = models.DecimalField(
        "peso alvo (%)", max_digits=6, decimal_places=2
    )
    faixa_min = models.DecimalField(
        "faixa mínima (%)", max_digits=6, decimal_places=2
    )
    faixa_max = models.DecimalField(
        "faixa máxima (%)", max_digits=6, decimal_places=2
    )

    def __str__(self):
        return f"{self.get_classe_display()}: {self.peso_alvo}%"


class Classe(MetaMixin):
    """Classe de ativo para fins de risco e alocação."""

    nome = models.CharField("nome", max_length=200, unique=True)
    fator_risco = models.CharField(
        "fator de risco", max_length=100, default="",
        help_text="Fator de risco associado (juros, inflação, crédito, câmbio, etc.)"
    )
    liquidez = models.CharField(
        "liquidez", max_length=50,
        choices=[
            ("alta", "Alta"),
            ("media", "Média"),
            ("baixa", "Baixa"),
        ],
        default="alta",
    )

    def __str__(self):
        return self.nome


class Posicao(MetaMixin):
    """Posição em um ativo: quantidade, custo médio, moeda, instituição."""

    ativo = models.CharField("ativo", max_length=300)
    classe = models.CharField("classe", max_length=200, default="acoes")
    quantidade = models.DecimalField(
        "quantidade", max_digits=20, decimal_places=8, default=0
    )
    preco_medio = models.DecimalField(
        "preço médio", max_digits=20, decimal_places=8, default=0
    )
    moeda = models.CharField("moeda", max_length=10, default="BRL")
    instituicao = models.CharField(
        "instituição", max_length=200, blank=True, default=""
    )
    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)

    def __str__(self):
        return f"{self.ativo} — {self.quantidade} {self.moeda}"


class Operacao(models.Model):
    """Operação de aplicação, resgate, venda, distribuição, etc.

    Campos: evento, data, valor, base_de_calculo, aliquota, IOF, etc.
    """
    EVENTO_APLICACAO = "aplicacao"
    EVENTO_RESGATE = "resgate"
    EVENTO_VENDA = "venda"
    EVENTO_DISTRIBUICAO = "distribuicao"
    EVENTO_BENEFICIO = "beneficio"
    EVENTO_AMORTIZACAO = "amortizacao"
    EVENTO_CHOICES = [
        (EVENTO_APLICACAO, "Aplicação"),
        (EVENTO_RESGATE, "Resgate"),
        (EVENTO_VENDA, "Venda"),
        (EVENTO_DISTRIBUICAO, "Distribuição"),
        (EVENTO_BENEFICIO, "Benefício"),
        (EVENTO_AMORTIZACAO, "Amortização"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="operacoes",
        null=True,
        blank=True,
        default=None,
    )
    posicao = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="operacoes",
        null=True,
        blank=True,
        default=None,
    )
    evento = models.CharField(
        "evento", max_length=30, choices=EVENTO_CHOICES, default=EVENTO_APLICACAO
    )
    data = models.DateField("data")
    valor = models.DecimalField("valor", max_digits=20, decimal_places=2, default=0)
    base_de_calculo = models.CharField(
        "base de cálculo", max_length=50, default=""
    )
    aliquota_ir = models.DecimalField(
        "alíquota IR (%)", max_digits=6, decimal_places=2, default=0
    )
    ir_ja_retido = models.DecimalField(
        "IR já retido (R$)", max_digits=12, decimal_places=2, default=0
    )
    iof = models.DecimalField(
        "IOF (%)", max_digits=6, decimal_places=2, default=0
    )
    observacao = models.TextField("observação", blank=True, default="")

    def __str__(self):
        return f"{self.get_evento_display()} {self.data}: {self.valor} {self.posicao.ativo if self.posicao else '?'}"
