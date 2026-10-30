"""Modelos do app documentos.

Um **Documento** é o arquivo recebido (nota de corretagem, extrato, ...) com o
texto guardado para auditoria e reprocessamento. Um **Lancamento** é a linha de
negócio extraída dele — a ponte entre o documento e a `carteira`.

Regras desta app (ver `specs/aplicacao.md`, R14):
- leitura é determinística: o que não está escrito no documento não é inventado;
- `(documento, linha)` é único — reprocessar o mesmo arquivo não duplica linha;
- promoção para a carteira é idempotente: cada lançamento aponta para a operação
  que gerou, e só lançamento **sem** operação é promovido de novo.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

MOEDA_PADRAO = "BRL"

STATUS_CHOICES = (
    ("recebido", "Recebido"),
    ("extraido", "Extraído"),
    ("erro", "Erro"),
    ("promovido", "Promovido para a carteira"),
)

TIPO_CHOICES = (
    ("nota_corretagem", "Nota de corretagem"),
    ("extrato", "Extrato"),
    ("outro", "Outro"),
)

LADO_CHOICES = (
    ("C", "Compra"),
    ("V", "Venda"),
)


class Documento(models.Model):
    """Documento recebido, com o texto extraído e o resultado da leitura."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="documentos",
        null=True,
        blank=True,
        default=None,
    )
    nome_original = models.CharField(max_length=300, blank=True, default="")
    sha256 = models.CharField(max_length=64, blank=True, default="", db_index=True)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default="nota_corretagem")
    layout = models.CharField(max_length=100, blank=True, default="")
    confianca = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="recebido")
    as_of = models.DateField(null=True, blank=True)
    numero_nota = models.CharField(max_length=50, blank=True, default="")
    corretora = models.CharField(max_length=200, blank=True, default="")
    texto = models.TextField(blank=True, default="")
    avisos = models.TextField(blank=True, default="")
    erro = models.TextField(blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.tipo} {self.as_of or '-'} ({self.status})"


class Lancamento(models.Model):
    """Linha de negócio extraída de um documento."""

    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name="lancamentos")
    linha = models.PositiveIntegerField()
    data = models.DateField()
    ativo = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, blank=True, default="")
    mercado = models.CharField(max_length=50, blank=True, default="")
    prazo = models.CharField(max_length=50, blank=True, default="")
    especificacao = models.CharField(max_length=300, blank=True, default="")
    lado = models.CharField(max_length=1, choices=LADO_CHOICES, default="C")
    quantidade = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal("0"))
    preco = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal("0"))
    valor = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"))
    debito_credito = models.CharField(max_length=1, blank=True, default="")
    avisos = models.TextField(blank=True, default="")
    operacao = models.ForeignKey(
        "carteira.Operacao",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        verbose_name = "lançamento"
        verbose_name_plural = "lançamentos"
        ordering = ["documento", "linha"]
        # Idempotência da leitura: a mesma linha do mesmo documento não entra duas vezes.
        unique_together = (("documento", "linha"),)

    def __str__(self) -> str:
        return f"{self.ativo} {self.lado} {self.quantidade} @ {self.preco}"
