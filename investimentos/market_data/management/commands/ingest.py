"""Comando `manage.py ingest` — baixa a PTAX do BCB preenchendo só o gap.

Fluxo (regras de `specs/fontes-de-dados.md`):

1. **R4** — calcula a janela que falta com `janela_de_ingestão`; se já está tudo
   coberto, não faz nenhuma chamada de rede.
2. **R7** — conferem-se as chamadas de hoje contra a cota da fonte antes de pedir.
3. **R5** — o transporte é HTTP da stdlib (`urllib`), sem biblioteca nova (P5) e
   sem LLM no meio: este script faz a requisição, o parse e a gravação.
4. **R9** — a resposta bruta vai para `raw_payloads` com a URL de origem.
5. **R1/R2** — gravação idempotente por `(série, data)`; divergência não sobrescreve.
6. **R7/R11** — tudo termina com linha em `fetch_log`, inclusive erro e bloqueio.

Uso::

    python manage.py seed_fontes                     # cadastro (uma vez)
    python manage.py ingest --serie PTAX --de 2016-09-01   # backfill
    python manage.py ingest --serie PTAX                     # incremental
"""

import time
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from investimentos.market_data.ingest import (
    janela_de_ingestao,
    parsear_ptax_periodo,
    persistir_observacoes,
)
from investimentos.market_data.models import FetchLog, RawPayload, Serie

BCB_PTAX_BASE = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo"
    "(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
)
USER_AGENT = "investimentos-pessoal/1.0 (uso pessoal, sem redistribuicao)"


class Command(BaseCommand):
    help = "Busca a PTAX do BCB para a janela em falta e grava de forma idempotente."

    def add_arguments(self, parser):
        parser.add_argument("--serie", default="PTAX", help="código da série (padrão: PTAX)")
        parser.add_argument("--de", dest="de", help="início do backfill, AAAA-MM-DD")
        parser.add_argument("--ate", dest="ate", help="fim da janela, AAAA-MM-DD (padrão: hoje)")

    def handle(self, *args, **opcoes):
        serie = Serie.objects.filter(codigo=opcoes["serie"]).select_related("source").first()
        if serie is None:
            codigos = ", ".join(Serie.objects.values_list("codigo", flat=True)) or "nenhuma"
            raise CommandError(f"Série {opcoes['serie']!r} não existe. Cadastradas: {codigos}")
        if "bcb" not in serie.source.nome.lower():
            raise CommandError(
                f"Esta versão só ingere PTAX do BCB; a série {serie.codigo!r} vem de "
                f"{serie.source.nome}. Registre o bloqueio em fetch_log antes de nova fonte."
            )

        ate = date.fromisoformat(opcoes["ate"]) if opcoes["ate"] else timezone.localdate()
        de = date.fromisoformat(opcoes["de"]) if opcoes["de"] else None

        # R7 — cota conferida antes de qualquer requisição.
        usadas_hoje = FetchLog.objects.filter(source=serie.source, dia=timezone.localdate()).count()
        if serie.source.cota is not None and usadas_hoje >= serie.source.cota:
            raise CommandError(
                f"Cota de {serie.source.nome} estourada hoje ({usadas_hoje}/{serie.source.cota})."
            )

        # R4 — gap primeiro: sem janela aberta, não há rede.
        inicio, fim = janela_de_ingestao(serie, ate, de)
        if inicio > fim:
            self.stdout.write(
                self.style.WARNING(
                    f"Série {serie.codigo} já coberta até {ate} — nenhuma requisição feita (R4)."
                )
            )
            return

        url = (
            # A API Olinda da PTAX aceita data em MM-DD-AAAA (formato americano):
            # mandar DD-MM-AAAA devolve HTTP 500. Conferido em 28/10/2026 com a
            # resposta real do serviço.
            f"{BCB_PTAX_BASE}?@dataInicial='{inicio.strftime('%m-%d-%Y')}'"
            f"&@dataFinalCotacao='{fim.strftime('%m-%d-%Y')}'&$format=json"
        )
        self.stdout.write(f"Buscando PTAX de {inicio} a {fim} em {serie.source.nome}...")

        inicio_relogio = time.monotonic()
        try:
            requisicao = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(requisicao, timeout=30) as resposta:
                texto = resposta.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            FetchLog.objects.create(
                source=serie.source,
                dia=timezone.localdate(),
                endpoint="ingest_ptax",
                status="erro",
                itens=0,
                latencia=f"{time.monotonic() - inicio_relogio:.1f}s",
            )
            raise CommandError(f"Falha de rede na PTAX: {exc} — registrado em fetch_log (R11)") from exc

        latencia = f"{time.monotonic() - inicio_relogio:.1f}s"

        # R9 — resposta bruta guardada para auditoria/reprocessamento.
        RawPayload.objects.create(serie=serie, periodo=f"{inicio}..{fim}", url=url, resposta_bruta=texto)

        pontos = parsear_ptax_periodo(texto)
        contagem = persistir_observacoes(serie, pontos)

        status_log = "divergencia" if contagem["divergentes"] else "ok"
        FetchLog.objects.create(
            source=serie.source,
            dia=timezone.localdate(),
            endpoint="ingest_ptax",
            status=status_log,
            itens=contagem["criadas"],
            latencia=latencia,
        )

        self.stdout.write(
            f"  criadas={contagem['criadas']} repetidas={contagem['iguais']} "
            f"divergentes={contagem['divergentes']} ({latencia})"
        )
        if contagem["divergentes"]:
            self.stdout.write(self.style.WARNING(
                "  ⚠ Divergência: a linha antiga foi mantida (R1). Correção é decisão humana."
            ))
        self.stdout.write(self.style.SUCCESS(f"fetch_log gravado com status {status_log!r}."))
