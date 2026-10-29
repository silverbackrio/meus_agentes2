"""Comando `manage.py export_series` — gera CSV datado em `dados/export/` (R10).

O frontend desenha gráfico lendo esses CSV, sem rede e sem token: o banco local é
a memória do projeto. Toda linha carrega **fonte, licença e data** (R9/R10), então
o arquivo se sustenta sozinho se sair do sistema.

Uso::

    python manage.py export_series                  # todas as séries
    python manage.py export_series --serie PTAX     # só uma
    python manage.py export_series --de 2016-01-01 --ate 2016-12-31
"""

import csv
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from investimentos.market_data.models import Observation, Serie


class Command(BaseCommand):
    help = "Exporta as séries do banco local para CSV em dados/export/."

    def add_arguments(self, parser):
        parser.add_argument("--serie", help="código da série (padrão: todas)")
        parser.add_argument("--de", help="início, AAAA-MM-DD")
        parser.add_argument("--ate", help="fim, AAAA-MM-DD")

    def handle(self, *args, **opcoes):
        series = Serie.objects.select_related("source").order_by("codigo")
        if opcoes["serie"]:
            series = series.filter(codigo=opcoes["serie"])
            if not series:
                raise CommandError(f"Série {opcoes['serie']!r} não existe.")

        de = date.fromisoformat(opcoes["de"]) if opcoes["de"] else None
        ate = date.fromisoformat(opcoes["ate"]) if opcoes["ate"] else None

        destino = Path(__file__).resolve().parents[4] / "dados" / "export"
        destino.mkdir(parents=True, exist_ok=True)

        total_linhas = 0
        for serie in series:
            observacoes = Observation.objects.filter(serie=serie).order_by("data")
            if de:
                observacoes = observacoes.filter(data__gte=de)
            if ate:
                observacoes = observacoes.filter(data__lte=ate)
            if not observacoes:
                self.stdout.write(f"  - {serie.codigo}: sem observações no período (pulado)")
                continue

            caminho = destino / f"{serie.codigo}.csv"
            with caminho.open("w", newline="", encoding="utf-8") as arquivo:
                escritor = csv.writer(arquivo)
                escritor.writerow(
                    ["data", "valor", "unidade", "serie", "fonte", "licenca", "frequencia"]
                )
                for obs in observacoes:
                    escritor.writerow(
                        [
                            obs.data.isoformat(),
                            str(obs.valor),
                            serie.unidade,
                            serie.nome,
                            serie.source.nome,
                            serie.source.licenca,
                            serie.frequencia,
                        ]
                    )
                    total_linhas += 1
            self.stdout.write(f"  + {caminho.name}: {observacoes.count()} linhas")

        if total_linhas == 0:
            self.stdout.write(self.style.WARNING("Nenhuma linha exportada."))
            return
        self.stdout.write(
            self.style.SUCCESS(f"{total_linhas} linhas em {destino} (R10 — o front lê sem rede).")
        )
