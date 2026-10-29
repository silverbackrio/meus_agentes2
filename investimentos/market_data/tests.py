"""
Testes do app market_data.

A gente não cria teste de ingestão ainda — só valida que os models estão com
os campos esperados e que um Source/ Serie criados pelo setup do time dão
para consultar retornam querys corretos. O script de ingestão é testado
manualmente pelo time (painel do time) e depois por teste reais via script.
"""

import json
from datetime import date
from decimal import Decimal

from django.db.utils import IntegrityError
from django.test import SimpleTestCase, TestCase

from .gaps import calcular_gaps, cobertura, datas_esperadas
from .ingest import janela_de_ingestao, parsear_ptax_periodo, persistir_observacoes
from .models import FetchLog, Observation, Serie, Source


class GapsTest(SimpleTestCase):
    """Testes dourados do cálculo de gap (regra R4 de `fontes-de-dados.md`).

    Sem banco: `gaps.py` é função pura (princípio P3).
    """

    def test_diario_pula_fim_de_semana(self):
        # 24/10/2026 = sábado, 25 = domingo, 26 = segunda.
        esperadas = list(datas_esperadas(date(2026, 10, 24), date(2026, 10, 26), "diario"))
        self.assertEqual(esperadas, [date(2026, 10, 26)])

    def test_furo_interno_vira_um_intervalo(self):
        existentes = [date(2026, 10, 26), date(2026, 10, 27), date(2026, 10, 30)]
        gaps = calcular_gaps(existentes, date(2026, 10, 26), date(2026, 10, 30), "diario")
        self.assertEqual(gaps, [(date(2026, 10, 28), date(2026, 10, 29))])

    def test_cauda_faltante_e_gap_ate_o_fim(self):
        existentes = [date(2026, 10, 26), date(2026, 10, 27)]
        gaps = calcular_gaps(existentes, date(2026, 10, 26), date(2026, 10, 30), "diario")
        self.assertEqual(gaps, [(date(2026, 10, 28), date(2026, 10, 30))])

    def test_serie_completa_nao_tem_gap(self):
        existentes = [date(2026, 10, 26), date(2026, 10, 27), date(2026, 10, 28)]
        gaps = calcular_gaps(existentes, date(2026, 10, 26), date(2026, 10, 28), "diario")
        self.assertEqual(gaps, [])

    def test_mensal_avanca_pelo_calendario(self):
        esperadas = list(datas_esperadas(date(2026, 1, 31), date(2026, 3, 31), "mensal"))
        self.assertEqual(
            esperadas,
            [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 28)],
        )

    def test_cobertura_conta_e_devolve_fracao(self):
        existentes = [date(2026, 10, 26), date(2026, 10, 27), date(2026, 10, 30)]
        resumo = cobertura(existentes, date(2026, 10, 26), date(2026, 10, 30), "diario")
        self.assertEqual(resumo["esperadas"], 5)
        self.assertEqual(resumo["presentes"], 3)
        self.assertEqual(resumo["faltantes"], 2)
        self.assertEqual(float(resumo["fracao"]), 0.6)
        self.assertEqual(resumo["ultima"], date(2026, 10, 30))

    def test_frequencia_e_periodo_invalidos_levantam_erro_com_campo(self):
        with self.assertRaises(ValueError) as capturado:
            list(datas_esperadas(date(2026, 10, 26), date(2026, 10, 30), "hora"))
        self.assertIn("frequencia", str(capturado.exception))

        with self.assertRaises(ValueError) as capturado:
            list(datas_esperadas(date(2026, 10, 30), date(2026, 10, 26), "diario"))
        self.assertIn("periodo", str(capturado.exception))


class IngestTest(TestCase):
    """Regras R1/R2/R4/R11 da ingestão, sem rede (transporte não é testado aqui)."""

    @classmethod
    def setUpTestData(cls):
        cls.fonte = Source.objects.create(nome="BCB", tipo="api", cota=1000)
        cls.serie = Serie.objects.create(
            source=cls.fonte,
            codigo="PTAX",
            nome="PTAX USD/BRL",
            ativo="USD/BRL",
            unidade="BRL por USD",
            frequencia="diario",
            moeda="BRL",
        )

    def test_parsear_ptax_periodo_extrai_data_e_decimais(self):
        payload = json.dumps(
            {
                "value": [
                    {
                        "cotacaoCompra": 3.2632,
                        "cotacaoVenda": 3.2638,
                        "dataHoraCotacao": "2016-09-09 13:14:00.885",
                    },
                    {
                        "cotacaoCompra": 3.251,
                        "cotacaoVenda": 3.2517,
                        "dataHoraCotacao": "2016-09-12 13:10:00.123",
                    },
                ]
            }
        )
        pontos = parsear_ptax_periodo(payload)
        self.assertEqual(
            pontos,
            [
                (date(2016, 9, 9), Decimal("3.2632"), Decimal("3.2638")),
                (date(2016, 9, 12), Decimal("3.251"), Decimal("3.2517")),
            ],
        )

    def test_parsear_pula_linha_invalida_em_vez_de_gravar_zero(self):
        payload = json.dumps(
            {
                "value": [
                    {"cotacaoCompra": 3.2632, "dataHoraCotacao": "2016-09-09 13:14:00"},
                    {
                        "cotacaoCompra": 3.251,
                        "cotacaoVenda": 3.2517,
                        "dataHoraCotacao": "2016-09-12 13:10:00",
                    },
                ]
            }
        )
        pontos = parsear_ptax_periodo(payload)
        self.assertEqual(len(pontos), 1)
        self.assertEqual(pontos[0][0], date(2016, 9, 12))

    def test_janela_serie_vazia_exige_inicio(self):
        with self.assertRaises(ValueError) as capturado:
            janela_de_ingestao(self.serie, ate=date(2016, 9, 30))
        self.assertIn("janela", str(capturado.exception))

        inicio, fim = janela_de_ingestao(self.serie, ate=date(2016, 9, 30), de=date(2016, 9, 1))
        self.assertEqual((inicio, fim), (date(2016, 9, 1), date(2016, 9, 30)))

    def test_janela_comeca_um_dia_depois_da_ultima_observacao(self):
        Observation.objects.create(
            serie=self.serie, data=date(2016, 9, 9), valor=Decimal("3.2638")
        )
        # R4: o que já existe não é baixado de novo, mesmo com --de anterior.
        inicio, fim = janela_de_ingestao(self.serie, ate=date(2016, 9, 13), de=date(2016, 9, 1))
        self.assertEqual((inicio, fim), (date(2016, 9, 10), date(2016, 9, 13)))

    def test_janela_sem_gap_retorna_inicio_posterior_ao_fim(self):
        Observation.objects.create(
            serie=self.serie, data=date(2016, 9, 13), valor=Decimal("3.2638")
        )
        inicio, fim = janela_de_ingestao(self.serie, ate=date(2016, 9, 13))
        self.assertGreater(inicio, fim)

    def test_persistir_e_idempotente_e_nao_sobrescreve(self):
        ponto = (date(2016, 9, 9), Decimal("3.2632"), Decimal("3.2638"))

        primeira = persistir_observacoes(self.serie, [ponto])
        self.assertEqual(primeira, {"criadas": 1, "iguais": 0, "divergentes": 0})

        segunda = persistir_observacoes(self.serie, [ponto])
        self.assertEqual(segunda, {"criadas": 0, "iguais": 1, "divergentes": 0})
        self.assertEqual(Observation.objects.count(), 1)

        # Rebusca com valor diferente não sobrescreve (R1) — vira divergência.
        terceira = persistir_observacoes(
            self.serie, [(date(2016, 9, 9), Decimal("3.2632"), Decimal("9.9999"))]
        )
        self.assertEqual(terceira, {"criadas": 0, "iguais": 0, "divergentes": 1})
        self.assertEqual(
            Observation.objects.get(data=date(2016, 9, 9)).valor, Decimal("3.2638")
        )


class SerieApiTest(TestCase):
    """GET /api/v1/series/ — cobertura, gaps e proveniência (R2/R3/R9/R10)."""

    @classmethod
    def setUpTestData(cls):
        cls.fonte = Source.objects.create(
            nome="BCB",
            tipo="api",
            url_base="https://dadosabertos.bcb.gov.br",
            licenca="Dados abertos do Banco Central",
            cota=1000,
        )
        cls.serie = Serie.objects.create(
            source=cls.fonte,
            codigo="PTAX",
            nome="Taxa de câmbio PTAX USD/BRL",
            ativo="USD/BRL",
            unidade="BRL por USD",
            frequencia="diario",
            moeda="BRL",
        )
        for data_iso, valor in (
            ("2026-10-26", "3.2632"),
            ("2026-10-27", "3.2701"),
            ("2026-10-30", "3.2810"),
        ):
            Observation.objects.create(
                serie=cls.serie,
                data=date.fromisoformat(data_iso),
                valor=Decimal(valor),
                unidade="BRL/USD",
            )
        FetchLog.objects.create(
            source=cls.fonte,
            dia=date.today(),
            endpoint="ingest_ptax",
            status="ok",
            itens=3,
            latencia="0.4s",
        )

    def test_lista_series_com_cobertura_e_as_of(self):
        resposta = self.client.get("/api/v1/series/")
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["as_of"], "2026-10-30")

        serie = corpo["series"][0]
        self.assertEqual(serie["fonte"]["nome"], "BCB")
        self.assertIn("licenca", serie["fonte"])
        self.assertEqual(serie["cobertura"]["esperadas"], 5)
        self.assertEqual(serie["cobertura"]["gaps"], [["2026-10-28", "2026-10-29"]])
        self.assertEqual(serie["observacoes"], 3)

    def test_filtro_por_ativo(self):
        resposta = self.client.get("/api/v1/series/?ativo=usd")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["total"], 1)

        resposta_vazia = self.client.get("/api/v1/series/?ativo=PETR4")
        self.assertEqual(resposta_vazia.json()["total"], 0)

    def test_observacoes_devolve_pontos_gaps_e_proveniencia(self):
        resposta = self.client.get(
            f"/api/v1/series/{self.serie.id}/observacoes/?de=2026-10-26&ate=2026-10-30"
        )
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(len(corpo["pontos"]), 3)
        self.assertEqual(corpo["pontos"][0], ["2026-10-26", 3.2632])
        self.assertEqual(corpo["gaps"], [["2026-10-28", "2026-10-29"]])
        self.assertEqual(corpo["as_of"], "2026-10-30")
        self.assertEqual(corpo["fonte"]["nome"], "BCB")
        self.assertEqual(corpo["unidade"], "BRL por USD")

    def test_observacoes_sem_periodo_usa_tudo_o_que_existe(self):
        resposta = self.client.get(f"/api/v1/series/{self.serie.id}/observacoes/")
        corpo = resposta.json()
        self.assertEqual(corpo["periodo"]["de"], "2026-10-26")
        self.assertEqual(corpo["periodo"]["ate"], "2026-10-30")
        self.assertEqual(len(corpo["pontos"]), 3)

    def test_periodo_invalido_retorna_422_nomeando_o_campo(self):
        resposta = self.client.get(
            f"/api/v1/series/{self.serie.id}/observacoes/?de=26/10/2026&ate=2026-10-30"
        )
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "periodo")

    def test_periodo_invertido_retorna_422(self):
        resposta = self.client.get(
            f"/api/v1/series/{self.serie.id}/observacoes/?de=2026-10-30&ate=2026-10-26"
        )
        self.assertEqual(resposta.status_code, 422)

    def test_serie_inexistente_retorna_404(self):
        resposta = self.client.get("/api/v1/series/9999/observacoes/")
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json()["campo"], "serie")

    def test_export_csv_carrega_fonte_em_cada_linha(self):
        resposta = self.client.get(f"/api/v1/series/{self.serie.id}/export.csv")
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta["Content-Type"].startswith("text/csv"))
        linhas = resposta.content.decode("utf-8").splitlines()
        self.assertIn("fonte,licenca", linhas[0])
        self.assertEqual(len(linhas), 4)  # cabeçalho + 3 observações
        self.assertIn("BCB", linhas[1])

    def test_dados_status_mostra_cobertura_log_e_cota(self):
        resposta = self.client.get("/api/v1/dados/status")
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["as_of"], "2026-10-30")
        self.assertEqual(len(corpo["series"]), 1)
        self.assertEqual(corpo["fetch_log"][0]["status"], "ok")
        self.assertEqual(corpo["cota"][0]["fonte"], "BCB")
        self.assertEqual(corpo["cota"][0]["usadas_hoje"], 1)
        self.assertEqual(corpo["cota"][0]["restantes"], 999)


class SourceModelTest(TestCase):
    def test_source_criacao(self):
        s = Source.objects.create(
            nome="BCB",
            tipo="api",
            url_base="https://dadosabertos.bcb.gov.br",
            licenca="ODbL",
            exige_chave=False,
            cota=100,
        )
        # Fetch uma source pelo nome
        self.assertEqual(s.nome, Source.objects.get(id=s.id).nome)

    def test_source_com_chave(self):
        Source.objects.create(
            nome="AlphaVantage",
            tipo="api",
            url_base="https://www.alphavantage.co",
            licenca="deve ter chave",
            exige_chave=True,
        )


class SerieModelTest(TestCase):
    def test_serie_criacao(self):
        font = Source.objects.create(
            nome="BCB",
            tipo="api",
            url_base="https://dadosabertos.bcb.gov.br",
            licenca="ODbL",
        )
        ser = Serie.objects.create(
            source=font,
            codigo="PTAX",
            nome="Taxa de câmbio PTAX",
            ativo="BRL/USD",
            unidade="R$ por USD",
            frequencia="diario",
            moeda="BRL",
        )
        self.assertEqual(ser.codigo, "PTAX")

    def test_serie_unique_com_sourceombra_e_codigo(self):
        font = Source.objects.create(
            nome="BCB",
            tipo="api",
            url_base="https://dadosabertos.bcb.gov.br",
            licenca="ODbL",
        )
        Serie.objects.create(source=font, codigo="PTAX", nome="Um", ativo="BRL/USD")
        # Criar outra com mesmo source e codigo deve falhar por unique_together
        with self.assertRaises(IntegrityError):
            Serie.objects.create(
                source=font,
                codigo="PTAX",
                nome="Outro",
                ativo="BRL/USD",
            )
