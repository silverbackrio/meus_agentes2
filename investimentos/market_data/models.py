"""
Modelos do app market_data.

Segue a spec `specs/fontes-de-dados.md` para o modelo de dados de mercado.
Toda escrita acontece via script de ingestão (manage.py ingest, run_terminal_command),
nunca via view ou API pública — regra R12.
"""
from django.db import models


class Source(models.Model):
    """Fonte de onde vêm os dados: API, arquivo ou entrada manual.

    Campos obrigatórios: nome, tipo, licença. Chaves nunca aqui (só no .env).
    """
    TIPO_API = "api"
    TIPO_ARQUIVO = "arquivo"
    TIPO_MANUAL = "manual"
    TIPO_CHOICES = [
        (TIPO_API, "API"),
        (TIPO_ARQUIVO, "Arquivo"),
        (TIPO_MANUAL, "Manual"),
    ]

    nome = models.CharField("nome", max_length=200)
    tipo = models.CharField(
        "tipo", max_length=20, choices=TIPO_CHOICES, default=TIPO_API
    )
    url_base = models.URLField("URL base", blank=True, default="")
    licenca = models.CharField("licença", max_length=300, default="")
    exige_chave = models.BooleanField("exige chave de API", default=False)
    cota_por_dia = models.PositiveIntegerField(
        "cota máxima por dia", blank=True, null=True
    )
    ativo = models.CharField(
        "ativo ou classe associada", max_length=200, blank=True, default=""
    )
    observacao = models.TextField("observação", blank=True, default="")

    class Meta:
        verbose_name = "fonte de dado"
        verbose_name_plural = "fontes de dado"

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class Serie(models.Model):
    """Série histórica: código da fonte, nome, ativo, unidade, frequência.

    Unique(source, codigo) — regra R2 da spec `fontes-de-dados.md`.
    """
    source = models.ForeignKey(
        Source, on_delete=models.PROTECT, related_name="series"
    )
    codigo = models.CharField("código na fonte", max_length=200)
    nome = models.CharField("nome da série", max_length=300, default="")
    ativo = models.CharField("ativo", max_length=200, default="")
    unidade = models.CharField("unidade", max_length=100, default="")
    FREQUENCIA_CHOICES = [
        ("diario", "Diário"),
        ("semanal", "Semanal"),
        ("mensal", "Mensal"),
        ("anual", "Anual"),
    ]
    frequencia = models.CharField(
        "frequência", max_length=50, choices=FREQUENCIA_CHOICES, default="diario"
    )
    moeda = models.CharField("moeda", max_length=10, default="BRL")

    class Meta:
        verbose_name = "série"
        verbose_name_plural = "séries"
        unique_together = [("source", "codigo")]

    def __str__(self):
        return f"{self.nome} ({self.ativo})"


class Observation(models.Model):
    """Observação de uma série em uma data: valor, unidade, fetched_at, payload_hash.

    Unique(serie, data) — regra R1 e R2 da spec `fontes-de-dados.md`.
    Append-only: nunca sobrescreve, nunca exclui. Se a rebusca traz dados
    diferentes, grava divergência em `fetch_log`, não altera `valor`.
    """
    serie = models.ForeignKey(
        Serie, on_delete=models.CASCADE, related_name="observations"
    )
    data = models.DateField("data")
    valor = models.DecimalField("valor", max_digits=20, decimal_places=8)
    unidade = models.CharField("unidade", max_length=100, default="")
    fetched_at = models.DateTimeField("fetched at", auto_now_add=True)
    payload_hash = models.CharField(
        "hash do payload bruto", max_length=64, default="", editable=False
    )

    class Meta:
        verbose_name = "observação"
        verbose_name_plural = "observações"
        unique_together = [("serie", "data")]
        ordering = ["data"]

    def save(self, *args, **kwargs):
        if Observation.objects.filter(serie=self.serie, data=self.data).exists():
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.serie.ativo} {self.data}: {self.valor} {self.unidade}"


class RawPayload(models.Model):
    """Resposta bruta de ingestão para auditoria e reprocessamento.

    Regra R9: proveniência obrigatória — toda linha tem fonte, licença,
    fetched_at e URL de origem.
    """
    serie = models.ForeignKey(
        Serie, on_delete=models.CASCADE, related_name="raw_payloads"
    )
    periodo = models.CharField("período", max_length=200, blank=True, default="")
    url = models.URLField("URL de origem", max_length=500, default="")
    resposta_bruta = models.TextField("resposta bruta", default="")
    fetched_at = models.DateTimeField("fetched at", auto_now_add=True)

    class Meta:
        verbose_name = "payload bruto"
        verbose_name_plural = "payloads brutos"
        ordering = ["-fetched_at"]


class FetchLog(models.Model):
    """Log de cada chamada de ingestão: source, dia, endpoint, status, itens, latência.

    Regra R7: cota respeitada e contada — cada chamada registra fetch_log.
    Regra R11: bloqueio declarado — endpoint que falha vira fetch_log com erro.
    """
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, related_name="fetch_logs"
    )
    dia = models.DateField("dia")
    endpoint = models.CharField("endpoint", max_length=500, default="")
    status = models.CharField("status", max_length=20, default="ok")
    itens = models.PositiveIntegerField("itens coletados", default=0)
    latencia = models.CharField("latência", max_length=30, default="")

    class Meta:
        verbose_name = "log de fetch"
        verbose_name_plural = "logs de fetch"
        ordering = ["-dia"]
