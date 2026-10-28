"""
Modelos do app analise.

Estado derivado: métricas, cenários, dossiês. Onde a spec manda cálculo,
ele vive em módulo Python puro — nunca em view, template ou JavaScript.
"""
from django.conf import settings
from django.db import models


class MetaMixin:
    """Mixin para owner (v1 sem login: null=True)."""

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


class Metrica(models.Model):
    """Métrica calculada: valor, fórmula, período, frequência, base, data-base."""

    class MetaMixin:
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

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="metricas",
        null=True,
        blank=True,
        default=None,
    )
    nome = models.CharField("nome", max_length=200)
    valor = models.DecimalField("valor", max_digits=20, decimal_places=8)
    formulacao = models.TextField("formula usada", default="")
    periodo = models.CharField("período", max_length=100, default="")
    FREQUENCIA_CHOICES = [
        ("diario", "Diário"),
        ("semanal", "Semanal"),
        ("mensal", "Mensal"),
    ]
    frequencia = models.CharField(
        "frequência", max_length=50, choices=FREQUENCIA_CHOICES, default="diario"
    )
    BASE_CHOICES = [("bruta", "Bruta"), ("liquida", "Líquida")]
    base = models.CharField(
        "base", max_length=50, choices=BASE_CHOICES, default="bruta"
    )
    data_base = models.DateField("data base", null=True, blank=True)

    class Meta:
        verbose_name = "métrica"
        verbose_name_plural = "métricas"
        ordering = ["-data_base", "-id"]

    def __str__(self):
        return f"{self.nome}: {self.valor}"


class Cenario(models.Model):
    """Cenário de estresse: choque por fator, premissa datada, impacto."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cenarios",
        null=True,
        blank=True,
        default=None,
    )
    nome = models.CharField("nome", max_length=200)
    fator = models.CharField("fator", max_length=100, default="")
    premissa = models.TextField("premissa", default="")
    premissa_data = models.DateField("data da premissa", null=True, blank=True)
    impacto_reais = models.DecimalField(
        "impacto em R$", max_digits=16, decimal_places=2, default=0
    )
    impacto_pct = models.DecimalField(
        "impacto em %", max_digits=6, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = "cenário"
        verbose_name_plural = "cenários"
        ordering = ["-premissa_data", "-id"]

    def __str__(self):
        return f"{self.nome}: {self.impacto_reais} R$"


class Dossie(models.Model):
    """Dossiê datado: data, ativos, texto com fontes."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dossies",
        null=True,
        blank=True,
        default=None,
    )
    data = models.DateField("data")
    titulo = models.CharField("título", max_length=300, default="")
    conteudo = models.TextField("conteúdo", default="")
    ativos = models.TextField("ativos", default="", help_text="Lista de ativos cobertos")

    class Meta:
        verbose_name = "dossiê"
        verbose_name_plural = "dossiês"
        ordering = ["-data", "-id"]
        # Constraint para evitar dossiês duplicados na mesma data com mesmo título
        constraints = [
            models.UniqueConstraint(
                fields=["data", "titulo"],
                name="dossie_data_titulo_unique",
            )
        ]

    def __str__(self):
        return f"Dossiê {self.data} — {self.titulo}"
