"""Comando `manage.py seed_fontes` — registra as fontes e séries iniciais.

Por que existe: a regra R3/R12 de `specs/fontes-de-dados.md` diz que dado de mercado
entra por ingestão controlada, e o script de ingestão precisa de uma `Source` e de
uma `Serie` no banco antes de rodar. Este comando é o "passo zero" — ele **não**
baixa cotação, só cria o cadastro (idempotente: rodar de novo não duplica).

Uso::

    python manage.py seed_fontes            # cria o que faltar
    python manage.py seed_fontes --listar   # só mostra o que já existe

Depois dele, `python .agents/scripts/ingest_dividendos_balances.py` já tem alvo.
"""

from django.core.management.base import BaseCommand

from investimentos.market_data.models import Serie, Source

# Cadastro inicial: (nome da fonte, tipo, url, licença, exige chave?, cota/dia)
FONTES = [
    {
        "nome": "BCB",
        "tipo": "api",
        "url_base": "https://dadosabertos.bcb.gov.br",
        "licenca": "Dados abertos do Banco Central — uso livre com atribuição",
        "exige_chave": False,
        "cota": 1000,
        "series": [
            {
                "codigo": "PTAX",
                "nome": "Taxa de câmbio PTAX USD/BRL",
                "ativo": "USD/BRL",
                "unidade": "BRL por USD",
                "frequencia": "diario",
                "moeda": "BRL",
            }
        ],
    },
    {
        "nome": "Yahoo Finance",
        "tipo": "api",
        "url_base": "https://query1.finance.yahoo.com",
        "licenca": "Uso pessoal/educacional; redistribuição comercial proibida (R8)",
        "exige_chave": True,
        "cota": 2000,
        "series": [
            {
                "codigo": "BBAS3.SA",
                "nome": "Dividendos BBAS3",
                "ativo": "BBAS3",
                "unidade": "BRL por ação",
                "frequencia": "diario",
                "moeda": "BRL",
            },
            {
                "codigo": "^BVSP",
                "nome": "Ibovespa",
                "ativo": "IBOV",
                "unidade": "pontos",
                "frequencia": "diario",
                "moeda": "BRL",
            },
        ],
    },
    {
        "nome": "Investing.com",
        "tipo": "api",
        "url_base": "https://www.investing.com",
        "licenca": "Uso pessoal; redistribuição proibida (R8)",
        "exige_chave": True,
        "cota": 80,
        "series": [
            {
                "codigo": "BBAS3-FINANCIALS",
                "nome": "Balanços BBAS3",
                "ativo": "BBAS3",
                "unidade": "BRL",
                "frequencia": "mensal",
                "moeda": "BRL",
            }
        ],
    },
]


class Command(BaseCommand):
    help = "Registra as fontes e séries iniciais do banco (idempotente, sem rede)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--listar",
            action="store_true",
            help="Apenas lista fontes e séries já cadastradas.",
        )

    def handle(self, *args, **opcoes):
        if opcoes["listar"]:
            self._listar()
            return

        criadas = 0
        for fonte in FONTES:
            source, foi_criada = Source.objects.get_or_create(
                nome=fonte["nome"],
                tipo=fonte["tipo"],
                defaults={
                    "url_base": fonte["url_base"],
                    "licenca": fonte["licenca"],
                    "exige_chave": fonte["exige_chave"],
                    "cota": fonte["cota"],
                },
            )
            if foi_criada:
                criadas += 1
                self.stdout.write(f"  + fonte {source.nome} ({source.tipo})")
            else:
                self.stdout.write(f"  = fonte {source.nome} já existia")

            for serie in fonte["series"]:
                _, serie_criada = Serie.objects.get_or_create(
                    source=source,
                    codigo=serie["codigo"],
                    defaults={
                        "nome": serie["nome"],
                        "ativo": serie["ativo"],
                        "unidade": serie["unidade"],
                        "frequencia": serie["frequencia"],
                        "moeda": serie["moeda"],
                    },
                )
                if serie_criada:
                    self.stdout.write(f"      + série {serie['codigo']} ({serie['ativo']})")

        self.stdout.write(self.style.SUCCESS(f"\nFontes novas: {criadas}."))
        self.stdout.write("Próximo passo: python .agents/scripts/ingest_dividendos_balances.py")
        self._listar()

    def _listar(self) -> None:
        self.stdout.write("\nCadastro atual:")
        for source in Source.objects.all().order_by("nome"):
            self.stdout.write(f"  {source.nome} [{source.tipo}] cota={source.cota or 's/limite'}")
            for serie in source.series.all().order_by("codigo"):
                self.stdout.write(
                    f"    - {serie.codigo} · {serie.ativo} · {serie.frequencia} · {serie.moeda}"
                )
