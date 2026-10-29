"""
Modelos do app market_data.

Segue specs/fontes-de-dados.md para o modelo de dados de mercado.
Toda escrita acontece via manage.py ingest ou script de ingestão rodado via
run_terminal_command, nunca via view ou API pública — regra R12.
"""

from django.db import models

# Regra R1 de specs/fontes-de-dados.md: fato passado é imutável. Isso se materializa
# em duas restrições abaixo: `Serie` é única por (source, codigo) e `Observation`
# é única por (serie, data) — a idempotência que faz rebuscar não duplicar linha.

TIPO_CHOICES = (
    ("api", "API"),
    ("arquivo", "Arquivo"),
    ("manual", "Manual"),
)

FREQUENCIA_CHOICES = (
    ("diario", "Diário"),
    ("semanal", "Semanal"),
    ("mensal", "Mensal"),
    ("anual", "Anual"),
)


class Source(models.Model):
    """Fonte de onde vêm os dados: API, arquivo ou entrada manual."""

    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="api")
    url_base = models.URLField(max_length=2000, blank=True, default="")
    licenca = models.CharField(max_length=300, default="")
    exige_chave = models.BooleanField(default=False)
    cota = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class Serie(models.Model):
    """Série histórica: código da fonte, nome, ativo, unidade, frequência."""

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="series")
    codigo = models.CharField(max_length=100)
    nome = models.CharField(max_length=300, default="")
    ativo = models.CharField(max_length=200, default="")
    unidade = models.CharField(max_length=100, default="")
    frequencia = models.CharField(max_length=50, choices=FREQUENCIA_CHOICES, default="diario")
    moeda = models.CharField(max_length=10, default="BRL")

    class Meta:
        # Mesma dupla-chave da spec: a mesma série não pode ser cadastrada duas vezes
        # na mesma fonte (R1/R3 — senão o gap e a idempotência ficam ambíguos).
        unique_together = (("source", "codigo"),)
        verbose_name = "série"
        verbose_name_plural = "séries"

    def __str__(self):
        return f"{self.nome} ({self.ativo})"


class Observation(models.Model):
    """Observação: valor de uma série em uma data (append-only).

    É a linha atômica do banco histórico — ex.: 2016-09-09 → 3,2638 BRL/USD
    (PTAX venda, BCB).
    Regras: R1 (fato passado não muda), R2 (idempotência por série+data) e
    R5 (a escrita só acontece por script de ingestão, nunca por API/view).
    """

    serie = models.ForeignKey(Serie, on_delete=models.CASCADE, related_name="observations")
    data = models.DateField()
    valor = models.DecimalField(max_digits=20, decimal_places=8)
    unidade = models.CharField(max_length=100, default="")
    fetched_at = models.DateTimeField(auto_now_add=True)
    payload_hash = models.CharField(max_length=64, default="", editable=False)

    class Meta:
        # Garante a idempotência exigida pela R2: rebuscar a mesma data não duplica.
        unique_together = (("serie", "data"),)
        verbose_name = "observação"
        verbose_name_plural = "observações"
        ordering = ["data"]

    def __str__(self):
        return f"{self.serie_id} {self.data} = {self.valor}"


class RawPayload(models.Model):
    """Payload bruto devolvido pela fonte, guardado para auditoria.

    Regra R9: guarda-se a resposta original para poder reprocessar sem rede e
    provar de onde veio o número (URL + hash + horário da coleta).
    """

    serie = models.ForeignKey(Serie, on_delete=models.CASCADE, related_name="raw_payloads")
    periodo = models.CharField(max_length=200, blank=True, default="")
    url = models.URLField(max_length=500, default="")
    resposta_bruta = models.TextField(default="")
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "payload bruto"
        verbose_name_plural = "payloads brutos"
        ordering = ["-fetched_at"]

    def __str__(self):
        return f"payload {self.serie_id} em {self.fetched_at:%Y-%m-%d %H:%M}"


class FetchLog(models.Model):
    """Log de uma tentativa de coleta: dia, endpoint, status, itens, latência.

    Regras R7 (respeitar cota) e R11 (bloqueio por licença/cota declarado aqui,
    não escondido): cada fetch deixa rastro, inclusive os que falharam.
    """

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="fetch_logs")
    dia = models.DateField()
    endpoint = models.CharField(max_length=500, default="")
    status = models.CharField(max_length=20, default="ok")
    itens = models.PositiveIntegerField(default=0)
    latencia = models.CharField(max_length=30, default="")

    class Meta:
        verbose_name = "log de fetch"
        verbose_name_plural = "logs de fetch"
        ordering = ["-dia"]

    def __str__(self):
        return f"{self.dia} {self.endpoint} → {self.status} ({self.itens} itens)"
