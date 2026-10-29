"""
Testes do app analise.

Valida apenas que os modelos configurados estão salvos corretamente.
Não tenta calcular métricas — os cálculos ficam em modules Python puros.
"""

from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from .calculos import (
    novo_preco_medio,
    pnl,
    projecao_renda_passiva,
    resumo_simulacao,
    yield_on_cost,
)
from .models import Cenario, Dossie, Metrica


class CalculosPrecoMedioTest(SimpleTestCase):
    """Testes dourados do Bloco 1 (regra R6 de `specs/aplicacao.md`).

    Entrada explícita, fórmula da spec, resultado esperado — sem banco, porque
    `calculos.py` é função pura (princípio P3).
    """

    def test_novo_preco_medio_exemplo_do_glossary(self):
        # GLOSSARY (exemplo corrigido em 28/10/2026): 100 títulos a R$ 30,00 +
        # 100 títulos a R$ 24,00 -> (3000 + 2400) / 200 = R$ 27,00
        resultado = novo_preco_medio(
            preco_medio_atual=Decimal("30.00"),
            quantidade_atual=Decimal("100"),
            preco_nova_compra=Decimal("24.00"),
            quantidade_nova=Decimal("100"),
        )
        self.assertEqual(resultado, Decimal("27.00"))

    def test_primeira_compra_preco_medio_e_o_preco_pago(self):
        resultado = novo_preco_medio(
            preco_medio_atual=Decimal("0"),
            quantidade_atual=Decimal("0"),
            preco_nova_compra=Decimal("22.10"),
            quantidade_nova=Decimal("100"),
        )
        self.assertEqual(resultado, Decimal("22.10"))

    def test_venda_parcial_nao_muda_preco_medio(self):
        resultado = novo_preco_medio(
            preco_medio_atual=Decimal("30.00"),
            quantidade_atual=Decimal("100"),
            preco_nova_compra=Decimal("24.00"),
            quantidade_nova=Decimal("-50"),
        )
        self.assertEqual(resultado, Decimal("30.00"))

    def test_entrada_invalida_levanta_erro_com_nome_do_campo(self):
        casos = [
            {"preco_medio_atual": Decimal("30"), "quantidade_atual": Decimal("100"),
             "preco_nova_compra": Decimal("24"), "quantidade_nova": Decimal("0")},
            {"preco_medio_atual": Decimal("30"), "quantidade_atual": Decimal("100"),
             "preco_nova_compra": Decimal("0"), "quantidade_nova": Decimal("10")},
            {"preco_medio_atual": Decimal("-30"), "quantidade_atual": Decimal("100"),
             "preco_nova_compra": Decimal("24"), "quantidade_nova": Decimal("10")},
        ]
        for entradas in casos:
            with self.assertRaises(ValueError) as capturado:
                novo_preco_medio(**entradas)
            self.assertIn(":", str(capturado.exception))

    def test_yield_on_cost_e_fracao_sobre_o_custo(self):
        # GLOSSARY: R$ 2,10/ação ÷ R$ 27,60 = 7,6%
        resultado = yield_on_cost(
            proventos_12m_por_acao=Decimal("2.10"),
            preco_medio=Decimal("27.60"),
        )
        self.assertEqual(resultado.quantize(Decimal("0.0001")), Decimal("0.0761"))

    def test_pnl_calcula_valor_e_percentual(self):
        valor, percentual = pnl(
            quantidade=Decimal("200"),
            preco_medio=Decimal("27.60"),
            preco_atual=Decimal("22.10"),
        )
        self.assertEqual(valor, Decimal("-1100.00"))
        # (22,10 / 27,60) - 1 = -19,93%
        self.assertAlmostEqual(float(percentual), -0.1992753623, places=8)

    def test_projecao_renda_passiva_multiplica_quantidade_por_provento(self):
        renda, yoc = projecao_renda_passiva(
            quantidade=Decimal("200"),
            proventos_12m_por_acao=Decimal("2.10"),
            preco_medio=Decimal("27.60"),
        )
        self.assertEqual(renda, Decimal("420.00"))
        self.assertIsNotNone(yoc)

    def test_resumo_simulacao_preenche_bloco_inteiro(self):
        resumo = resumo_simulacao(
            quantidade_atual=Decimal("100"),
            preco_medio_atual=Decimal("30.00"),
            quantidade_nova=Decimal("100"),
            preco_nova_compra=Decimal("24.00"),
            preco_atual_tela=Decimal("22.10"),
            proventos_12m_por_acao=Decimal("2.10"),
        )
        self.assertEqual(resumo["preco_medio_novo"], Decimal("27.00"))
        self.assertEqual(resumo["quantidade_total"], Decimal("200"))
        self.assertEqual(resumo["custo_novo_total"], Decimal("2400.00"))
        self.assertEqual(resumo["projecao_renda_passiva"], Decimal("420.00"))
        self.assertIsNotNone(resumo["pnl"])

    def test_resumo_simulacao_com_jcp_zerado_somente_provento(self):
        # Caso 1 do grill: JCP explícito zero, só provento entra no cálculo.
        resumo = resumo_simulacao(
            quantidade_atual=Decimal("100"),
            preco_medio_atual=Decimal("30.00"),
            quantidade_nova=Decimal("100"),
            preco_nova_compra=Decimal("24.00"),
            preco_atual_tela=Decimal("22.10"),
            proventos_12m_por_acao=Decimal("2.10"),
            jcp_anual_por_acao=Decimal("0"),
        )
        self.assertEqual(resumo["preco_medio_novo"], Decimal("27.00"))
        self.assertEqual(resumo["projecao_renda_passiva"], Decimal("420.00"))
        self.assertIsNotNone(resumo["yield_on_cost_novo"])
        self.assertAlmostEqual(
            float(resumo["yield_on_cost_novo"]), 2.10 / 27.00, places=8
        )

    def test_resumo_simulacao_sem_jcp_omite_o_campo(self):
        # Caso 2 do grill: JCP omitido -> contrato aceita e usa zero no cálculo.
        resumo = resumo_simulacao(
            quantidade_atual=Decimal("100"),
            preco_medio_atual=Decimal("30.00"),
            quantidade_nova=Decimal("100"),
            preco_nova_compra=Decimal("24.00"),
            preco_atual_tela=Decimal("22.10"),
            proventos_12m_por_acao=Decimal("2.10"),
        )
        self.assertEqual(resumo["preco_medio_novo"], Decimal("27.00"))
        self.assertEqual(resumo["projecao_renda_passiva"], Decimal("420.00"))
        self.assertIsNotNone(resumo["yield_on_cost_novo"])
        self.assertAlmostEqual(
            float(resumo["yield_on_cost_novo"]), 2.10 / 27.00, places=8
        )


class SimularApiTest(TestCase):
    """POST /api/v1/analise/simular/ — contrato da API (R2, R4 e R9)."""

    url = "/api/v1/analise/simular/"

    def _payload(self, **extras):
        payload = {
            "ativo": "BBAS3",
            "moeda": "BRL",
            "quantidade_atual": "100",
            "preco_medio_atual": "30.00",
            "quantidade_nova": "100",
            "preco_nova_compra": "24.00",
            "preco_atual_tela": "22.10",
            "proventos_12m_por_acao": "2.10",
            "data_base": "2026-10-28",
        }
        payload.update(extras)
        return payload

    def test_simulacao_valida_devolve_numero_datado_com_formula_e_aviso(self):
        resposta = self.client.post(self.url, self._payload(), content_type="application/json")
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()

        novo = corpo["resultado"]["preco_medio_novo"]
        self.assertAlmostEqual(novo["valor"], 27.00, places=2)
        self.assertEqual(novo["unidade"], "BRL/ação")
        self.assertEqual(novo["data_base"], "2026-10-28")
        self.assertEqual(corpo["data_base"], "2026-10-28")
        self.assertIn("novo_preco_medio", corpo["formula"]["preco_medio_novo"])
        self.assertIn("não é garantia", corpo["aviso"])
        # R9: nada de recomendação na resposta
        texto = str(corpo).lower()
        self.assertNotIn("compre", texto)
        self.assertNotIn("venda", texto)

    def test_campos_obrigatorios_ausentes_retornam_422_com_campo(self):
        payload = self._payload()
        del payload["quantidade_nova"]
        resposta = self.client.post(self.url, payload, content_type="application/json")
        self.assertEqual(resposta.status_code, 422)
        corpo = resposta.json()
        self.assertEqual(corpo["campo"], "quantidade_nova")
        self.assertIn("sugestao", corpo)

    def test_api_somente_provento_omitindo_jcp_gera_200(self):
        # Caso 2 do grill: JCP omitido na requisição -> backend usa zero.
        resposta = self.client.post(
            self.url,
            self._payload(jcp_anual_por_acao=None),
            content_type="application/json",
        )
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertAlmostEqual(
            corpo["resultado"]["yield_on_cost_novo"]["valor"],
            2.10 / 27.00,
            places=2,
        )
        self.assertAlmostEqual(
            corpo["resultado"]["projecao_renda_passiva"]["valor"],
            420.00,
            places=2,
        )
        self.assertIsNotNone(corpo["resultado"]["jcp_anual_por_acao"])

    def test_api_com_jcp_zerado_gera_200(self):
        # Caso 1 do grill: JCP explícito zero, só provento entra no cálculo.
        resposta = self.client.post(
            self.url,
            self._payload(jcp_anual_por_acao="0"),
            content_type="application/json",
        )
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertAlmostEqual(
            corpo["resultado"]["yield_on_cost_novo"]["valor"],
            2.10 / 27.00,
            places=2,
        )
        self.assertAlmostEqual(
            corpo["resultado"]["projecao_renda_passiva"]["valor"],
            420.00,
            places=2,
        )
        self.assertIsNotNone(corpo["resultado"]["jcp_anual_por_acao"])

    def test_entrada_invalida_retorna_422_e_nao_calcula(self):
        resposta = self.client.post(
            self.url, self._payload(preco_nova_compra="0"), content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "preco_nova_compra")

    def test_get_nao_e_permitido(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 405)


class MetricaModelTest(TestCase):
    def test_metrica_criacao(self):
        m = Metrica.objects.create(
            nome="P/L BBAS3",
            valor=7.5,
            formulacao="Preço / Lucro por ação",
            periodo="2024-Q1",
        )
        self.assertAlmostEqual(m.valor, 7.5, places=2)


class CenarioModelTest(TestCase):
    def test_cenario_criacao(self):
        c = Cenario.objects.create(
            nome="Risco crédito BBAS3 +200bps",
            fator="crédito",
            premissa=(
                "A inadimplência dos grandes bancos pelo CDS e spread de "
                "crédito atingiu o pior nível da série (BCB, 27/10/2026)."
            ),
            premissa_data="2026-10-27",
            impacto_reais=-5000,
            impacto_pct=-10,
        )
        self.assertEqual(c.nome, "Risco crédito BBAS3 +200bps")


class DossieModelTest(TestCase):
    def test_dossie_criacao(self):
        d1 = Dossie.objects.create(
            data="2026-10-27",
            titulo="BBAS3 — rematrição e preço médio",
            conteudo="# Dossiê BBAS3",
            ativos="BBAS3",
        )
        self.assertEqual(d1.titulo, "BBAS3 — rematrição e preço médio")


class DossieUniqueTeste(TestCase):
    def test_dossie_data_e_titulo_unicos(self):
        Dossie.objects.create(
            data="2026-10-27",
            titulo="BBAS3 — rematrição e preço médio",
            conteudo="# Dossiê BBAS3",
            ativos="BBAS3",
        )
        # Um dossiê com mesma data e título deve falhar
        from django.db.utils import IntegrityError

        with self.assertRaises(IntegrityError):
            Dossie.objects.create(
                data="2026-10-27",
                titulo="BBAS3 — rematrição e preço médio",
                conteudo="# Dossiê BBAS3 — dup",
                ativos="BBAS3",
            )
