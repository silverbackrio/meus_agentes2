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


class Metrica(MetaMixin):
    """Métrica calculada: valor, fórmula, período, frequência, base, data-base."""

    nome = models.CharField("nome", max_length=200)
    valor = models.DecimalField("valor", max_digits=20, decimal_places=8)
    formulacao = models.TextField("formula usada", default="")
    periodo = models.CharField("período", max_length=100, default="")
    frequencia = models.CharField(
        "frequência", max_length=50, default="diario",
        choices=[("diario", "Diário"), ("semanal", "Semanal"), ("mensal", "Mensal")],
    )
    base = models.CharField(
        "base", max_length=50, default="bruta",
        choices=[("bruta", "Bruta"), ("liquida", "Líquida")],
    )
    data_base = models.DateField("data base", default=None, null=True, blank=True)
    posicao = models.ForeignKey(
        "carteira.Posicao",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="metricas",
    )

    def __str__(self):
        return f"{self.nome}: {self.valor}"


class Cenario(MetaMixin):
    """Cenário de estresse: choque por fator, premissa datada, impacto."""

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

    def __str__(self):
        return f"{self.nome}: {self.impacto_reais} R$"


class Dossie(MetaMixin):
    """Dossiê datado: data, ativos, texto com fontes.

    Persistido em dados/<classe>/<ativo>/<AAAA-MM-DD>.md (convenção dados/README.md),
    e aqui como registro no banco para consulta rápida.
    """
    data = models.DateField("data")
    titulo = models.CharField("título", max_length=300, default="")
    conteudo = models.TextField("conteúdo", default="")
    ativos = models.TextField("ativos", default="", help_text="Lista de ativos cobertos")

    def __str__(self):
        return f"Dossiê {self.data} — {self.titulo}"
