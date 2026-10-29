"""
Modelos do app analise.

Estado derivado: métricas, cenários, dossiês — os modelos que reúnem
cálculos e insights. Onde a spec manda cálculo, ele vive em módulo Python
puro, nunca em view, template ou JavaScript.
"""

from django.conf import settings
from django.db import models

DEFAULT_METRICA_CHOICES = [("P/L", "Preço / Lucro"), ("P/VP", "Preço / Valor Patrimonial")]


class BaseModel(models.Model):
    """Base com `owner`, herdada por todos os modelos do app.

    Por que existe: a decisão A8 de `ARCHITECTURE_DECISIONS.md` registra que a v1
    roda sem login, mas o schema já nasce multiusuário — ou seja, o campo `owner`
    fica no banco desde o início para a v2 não precisar de migração de dados.
    Ele é nulável de propósito: hoje ninguém preenche, amanhã todo mundo.
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


class Metrica(BaseModel):
    """Métrica calculada: valor, fórmula, período, frequência, base, data-base."""

    nome = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=20, decimal_places=8)
    formulacao = models.TextField(blank=True, default="")
    periodo = models.CharField(max_length=100, default="")
    frequencia = models.CharField(
        max_length=50,
        choices=[
            ("diario", "Diário"),
            ("semanal", "Semanal"),
            ("mensal", "Mensal"),
        ],
        default="diario",
    )
    base = models.CharField(
        max_length=50,
        choices=[
            ("bruta", "Bruta"),
            ("liquida", "Líquida"),
        ],
        default="bruta",
    )
    data_base = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "métrica"
        verbose_name_plural = "métricas"
        ordering = ["-data_base", "-id"]

    def __str__(self):
        return f"{self.nome}: {self.valor}"


class Cenario(BaseModel):
    """Cenário de estresse: choque por fator, premissa datada, impacto."""

    nome = models.CharField(max_length=200)
    fator = models.CharField(max_length=100, default="")
    premissa = models.TextField(default="")
    premissa_data = models.DateField(null=True, blank=True)
    impacto_reais = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    impacto_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        verbose_name = "cenário"
        verbose_name_plural = "cenários"
        ordering = ["-premissa_data", "-id"]

    def __str__(self):
        return f"{self.nome}: {self.impacto_reais} R$"


class Dossie(BaseModel):
    """Dossiê datado: data, ativos, texto com fontes."""

    data = models.DateField()
    titulo = models.CharField(max_length=300, default="")
    conteudo = models.TextField(default="")
    ativos = models.TextField(
        default="",
        help_text="Lista de ativos cobertos (ex: BBAS3, EWZ, ...)",
    )

    class Meta:
        verbose_name = "dossiê"
        verbose_name_plural = "dossiês"
        ordering = ["-data", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["data", "titulo"],
                name="dossie_data_titulo_unique",
            )
        ]

    def __str__(self):
        return f"Dossiê {self.data} — {self.titulo}"
