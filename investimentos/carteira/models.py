"""
Modelos do app carteira.

Segue specs/carteira-e-risco.md e specs/dominio-e-fontes.md para o modelo
de carteira: objetivo, perfil, política, posições e operações.
V1 sem login: campo owner já nasce no schema para a v2 não exigir migração.
"""

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    """Modelo base abstrato com owner, para todos os modelos não abstratos
    do app carteira. Herdar dele garante que todo mundo tem `owner`.
    """

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


class Objetivo(BaseModel):
    """Objetivo financeiro: valor-alvo, unidade (real/nominal), horizonte."""

    nome = models.CharField(max_length=200)
    valor_alvo = models.DecimalField(max_digits=20, decimal_places=2)
    unidade = models.CharField(
        max_length=20,
        choices=[
            ("reais", "Reais"),
            ("nominais", "Nominais"),
        ],
        default="reais",
    )
    horizonte_dias = models.PositiveIntegerField(default=360)
    liquidez_necessary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "objetivo"
        verbose_name_plural = "objetivos"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} — {self.valor_alvo} {self.unidade}"


class Perfil(BaseModel):
    """Perfil de investidor: tolerância, capacidade, restrições."""

    tolerancia = models.CharField(
        max_length=20,
        choices=[
            ("baixa", "Baixa"),
            ("media", "Média"),
            ("alta", "Alta"),
        ],
        default="media",
    )
    capacidade_risco = models.CharField(
        max_length=20,
        choices=[
            ("baixa", "Baixa"),
            ("media", "Média"),
            ("alta", "Alta"),
        ],
        default="media",
    )
    restricoes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfis"
        ordering = ["tolerancia"]

    def __str__(self):
        return f"Perfil {self.tolerancia}/{self.capacidade_risco}"


class Politica(BaseModel):
    """Política de alocação: classe, peso alvo, faixa mínima e máxima."""

    classe = models.CharField(
        max_length=20,
        choices=[
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
        ],
    )
    peso_alvo = models.DecimalField(max_digits=6, decimal_places=2)
    faixa_min = models.DecimalField(max_digits=6, decimal_places=2)
    faixa_max = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        verbose_name = "política"
        verbose_name_plural = "políticas"
        ordering = ["classe"]

    def __str__(self):
        return f"{self.classe}: {self.peso_alvo}%"


class Classe(models.Model):
    """Classe de ativo para fins de risco e alocação."""

    nome = models.CharField(max_length=200, unique=True)
    fator_risco = models.CharField(max_length=100, default="")
    liquidez = models.CharField(
        max_length=50,
        choices=[
            ("alta", "Alta"),
            ("media", "Média"),
            ("baixa", "Baixa"),
        ],
        default="alta",
    )

    class Meta:
        verbose_name = "classe"
        verbose_name_plural = "classes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Posicao(BaseModel):
    """Posição em um ativo: quantidade, custo médio, moeda, instituição."""

    ativo = models.CharField(max_length=300)
    classe = models.CharField(max_length=200, default="acoes")
    quantidade = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    preco_medio = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    moeda = models.CharField(max_length=10, default="BRL")
    instituicao = models.CharField(max_length=200, blank=True, default="")
    # Campos próprios da classe (CDB tem indexador/vencimento, fundo tem CNPJ e
    # taxa, ouro tem gramatura...). O esquema fica em `carteira/esquemas.py` e é
    # validado por `carteira/validacao.py` antes de gravar — JSON aqui, não 40
    # colunas nulas, para classe nova não exigir migração (P4).
    atributos = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("ativa", "Ativa"), ("encerrada", "Encerrada")],
        default="ativa",
    )
    data_entrada = models.DateField(null=True, blank=True)
    data_encerramento = models.DateField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "posição"
        verbose_name_plural = "posições"
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"{self.ativo} — {self.quantidade} {self.moeda}"


class Operacao(models.Model):
    """Operação de carteira: aplicação, resgate, venda, distribuição, etc.

    Campos: evento, data, valor, base_de_calculo, aliquota_ir, ir_ja_retido, iof, observacao.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="operacoes",
        null=True,
        blank=True,
        default=None,
    )
    posicao = models.ForeignKey(
        "carteira.Posicao",
        on_delete=models.CASCADE,
        related_name="operacoes",
        null=True,
        blank=True,
        default=None,
    )
    evento = models.CharField(
        max_length=30,
        choices=[
            ("aplicacao", "Aplicação"),
            ("resgate", "Resgate"),
            ("venda", "Venda"),
            ("distribuicao", "Distribuição"),
            ("beneficio", "Benefício"),
            ("amortizacao", "Amortização"),
        ],
        default="aplicacao",
    )
    data = models.DateField()
    valor = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    quantidade = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    base_de_calculo = models.CharField(max_length=50, default="")
    aliquota_ir = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    ir_ja_retido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iof = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Custos do evento discriminados (corretagem, emolumentos, custódia, IR, IOF...).
    # `custo_total` é a soma e `valor_efeito` é o caixa do evento já com custos —
    # calculados por `validacao.efeito_financeiro`, nunca na view (R4).
    custos = models.JSONField(default=dict, blank=True)
    custo_total = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    valor_efeito = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    observacao = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "operação"
        verbose_name_plural = "operações"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.evento} {self.data}: {self.valor}"
