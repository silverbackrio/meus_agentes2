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
from .renda_fixa import (
    aliquota_ir,
    comparar_produtos,
    taxa_equivalente,
    valor_futuro,
)


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


class RendaFixaCalculosTest(SimpleTestCase):
    """Testes dourados de `specs/renda-fixa.md` (regra R6).

    Entrada explícita, fórmula da spec, resultado esperado — sem banco, porque
    `renda_fixa.py` é função pura (princípio P3).
    """

    def test_aliquota_de_ir_pela_faixa_do_prazo(self):
        # renda-fixa.md R2 — tabela regressiva, Lei 11.033/2004, vigente 2026:
        # 22,5% até 180 dias; 20% de 181 a 360; 17,5% de 361 a 720; 15% acima.
        self.assertEqual(aliquota_ir(180), (Decimal("0.225"), "até 180 dias"))
        self.assertEqual(aliquota_ir(181), (Decimal("0.20"), "de 181 a 360 dias"))
        self.assertEqual(aliquota_ir(360), (Decimal("0.20"), "de 181 a 360 dias"))
        self.assertEqual(aliquota_ir(361), (Decimal("0.175"), "de 361 a 720 dias"))
        self.assertEqual(aliquota_ir(720), (Decimal("0.175"), "de 361 a 720 dias"))
        self.assertEqual(aliquota_ir(721), (Decimal("0.15"), "acima de 720 dias"))

    def test_valor_futuro_formula_da_spec(self):
        # VF = VI * (1 + i)^n  ->  10000 * (1 + 0.10)^(360/360) = 11000
        self.assertEqual(valor_futuro("10000", "0.10", 360), Decimal("11000"))
        # 720 dias: 10000 * 1.10^2 = 12100
        self.assertEqual(valor_futuro("10000", "0.10", 720), Decimal("12100"))

    def test_equivalencia_de_taxas(self):
        # (1 + 0.10)^720 = (1 + i)^360  ->  i = 1.10^2 - 1 = 0.21
        self.assertEqual(taxa_equivalente("0.10", 720, 360), Decimal("0.21"))

    def test_tributado_360_dias_golden(self):
        # Entradas: CDB 10% a.a., 360 dias corridos, VI = R$ 10.000,00.
        resultado = comparar_produtos(
            [{"nome": "CDB Banco A", "taxa": "10", "prazo_dias": 360, "isento": False}],
            valor_inicial="10000",
        )
        item = resultado["itens"][0]
        self.assertEqual(item["valor_futuro"], Decimal("11000"))  # VF = 10000 * 1.10
        self.assertEqual(item["imposto"], Decimal("200"))  # IR = 1000 * 20%
        # Fórmula literal da spec: líquido = VF - VI - IR - IOF
        self.assertEqual(item["rendimento_liquido"], Decimal("800"))
        # O que volta ao final: VF - IR = 10800
        self.assertEqual(item["valor_recebido"], Decimal("10800"))
        # Taxa líquida anualizada: (10800/10000)^(360/360) - 1 = 8% a.a.
        self.assertEqual(item["taxa_liquida_aa"], Decimal("0.08"))
        self.assertEqual(resultado["prazo_comum_dias"], 360)

    def test_isento_nao_paga_ir_golden(self):
        # Mesmas entradas do golden anterior, marcando LCI (isento — art. 3º).
        resultado = comparar_produtos(
            [{"nome": "LCI Banco B", "taxa": "10", "prazo_dias": 360, "isento": True}],
            valor_inicial="10000",
        )
        item = resultado["itens"][0]
        self.assertEqual(item["aliquota_ir"], Decimal("0"))
        self.assertEqual(item["imposto"], Decimal("0"))
        self.assertEqual(item["rendimento_liquido"], Decimal("1000"))
        self.assertEqual(item["valor_recebido"], Decimal("11000"))
        self.assertEqual(item["taxa_liquida_aa"], Decimal("0.10"))

    def test_tributado_720_dias_golden(self):
        resultado = comparar_produtos(
            [{"nome": "CDB Banco C", "taxa": "10", "prazo_dias": 720, "isento": False}],
            valor_inicial="10000",
        )
        item = resultado["itens"][0]
        self.assertEqual(item["valor_futuro"], Decimal("12100"))  # 10000 * 1.10^2
        self.assertEqual(item["aliquota_ir"], Decimal("0.175"))  # faixa 361-720
        self.assertEqual(item["imposto"], Decimal("367.5"))  # 2100 * 17,5%
        self.assertEqual(item["rendimento_liquido"], Decimal("1732.5"))
        self.assertEqual(item["valor_recebido"], Decimal("11732.5"))

    def test_prazo_antes_do_30_dia_e_recusado_por_iof(self):
        # Decreto 6.306/2007: IOF regressivo antes do 30º dia — o módulo não
        # memoriza a tabela, recusa e explica (incerteza declarada).
        with self.assertRaises(ValueError) as capturado:
            comparar_produtos(
                [{"nome": "CDB 20d", "taxa": "10", "prazo_dias": 20, "isento": False}],
                valor_inicial="10000",
            )
        self.assertIn("prazo_dias:", str(capturado.exception))
        self.assertIn("IOF", str(capturado.exception))


class CompararApiTest(TestCase):
    """GET /api/v1/comparar — contrato da API (R2, R4, R5, R9)."""

    url = "/api/v1/comparar/"

    def test_comparacao_devolve_base_liquida_datada_com_formula_e_aviso(self):
        resposta = self.client.get(
            self.url,
            {
                "ativos": "CDB Banco A|10|360|tributado,LCI Banco B|10|360|isento",
                "base": "liquida",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["base"], "liquida")
        self.assertEqual(corpo["convencao"]["dias_base"], 360)
        self.assertEqual(corpo["prazo_comum_dias"], 360)
        self.assertEqual(corpo["valor_inicial"]["valor"], 10000.0)
        self.assertEqual(corpo["data_base"], corpo["as_of"])

        tributado, isento = corpo["itens"]
        # Tributado: IR de 20% (faixa 181-360) com a norma datada (R2/R3)
        self.assertEqual(tributado["ir"]["aliquota"]["valor"], 20.0)
        self.assertEqual(tributado["ir"]["faixa"], "de 181 a 360 dias")
        self.assertIn("Lei 11.033/2004", tributado["ir"]["norma"])
        self.assertEqual(tributado["imposto"]["valor"], 200.0)
        self.assertEqual(tributado["valor_recebido"]["valor"], 10800.0)
        self.assertEqual(tributado["taxa_liquida"]["valor"], 8.0)
        # Isento: zero de IR com a isenção citada (renda-fixa.md R1)
        self.assertEqual(isento["ir"]["aliquota"]["valor"], 0.0)
        self.assertEqual(isento["valor_recebido"]["valor"], 11000.0)
        self.assertEqual(isento["taxa_liquida"]["valor"], 10.0)

        # Fórmula, normas, riscos e aviso obrigatório de comparação
        self.assertIn("VF = VI", corpo["formula"]["valor_futuro"])
        self.assertEqual(len(corpo["riscos"]), 4)
        self.assertEqual(corpo["aviso"], "Análise comparativa; a escolha e o aporte são seus.")
        # R9: nenhuma ordem de aporte na resposta
        texto = str(corpo).lower()
        self.assertNotIn("compre", texto)
        self.assertNotIn("venda", texto)
        self.assertNotIn("aloque", texto)

    def test_valor_inicial_opcional_entra_como_premissa_declarada(self):
        resposta = self.client.get(
            self.url, {"ativos": "CDB Banco A|10|360|tributado", "valor": "5000"}
        )
        self.assertEqual(resposta.status_code, 200)
        item = resposta.json()["itens"][0]
        self.assertEqual(item["valor_recebido"]["valor"], 5400.0)  # 5500 - 100 de IR

    def test_rota_tambem_responde_sem_barra_final(self):
        resposta = self.client.get(
            "/api/v1/comparar", {"ativos": "CDB A|10|360|tributado"}
        )
        self.assertEqual(resposta.status_code, 200)

    def test_sem_ativos_retorna_422(self):
        resposta = self.client.get(self.url, {"base": "liquida"})
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "ativos")

    def test_base_bruta_retorna_422(self):
        resposta = self.client.get(
            self.url, {"ativos": "CDB A|10|360|tributado", "base": "bruta"}
        )
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "base")

    def test_formato_errado_retorna_422_apontando_ativos(self):
        resposta = self.client.get(self.url, {"ativos": "CDB A|10|360"})
        self.assertEqual(resposta.status_code, 422)
        corpo = resposta.json()
        self.assertEqual(corpo["campo"], "ativos")
        self.assertIn("nome|taxa_a_a|prazo_dias|tipo", corpo["erro"])

    def test_tipo_invalido_retorna_422(self):
        resposta = self.client.get(self.url, {"ativos": "CDB A|10|360|meio"})
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "tipo")

    def test_prazo_curto_retorna_422_apontando_prazo(self):
        resposta = self.client.get(self.url, {"ativos": "CDB A|10|20|tributado"})
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "prazo_dias")
        self.assertIn("IOF", resposta.json()["erro"])

    def test_valor_invalido_retorna_422(self):
        resposta = self.client.get(
            self.url, {"ativos": "CDB A|10|360|tributado", "valor": "abc"}
        )
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "valor_inicial")


class DossieDetailApiTest(TestCase):
    """GET /api/v1/analise/dossies/{data} — contrato da API (R2, R9)."""

    def _criar_dossie(self, data="2026-10-27"):
        return Dossie.objects.create(
            data=data,
            titulo="BBAS3 — cenário de aporte",
            conteudo="# Cenário\nCom dado datado de 27/10/2026.",
            ativos="BBAS3",
        )

    def test_data_existente_devolve_dossies_com_aviso(self):
        self._criar_dossie()
        resposta = self.client.get("/api/v1/analise/dossies/2026-10-27")
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["data"], "2026-10-27")
        self.assertEqual(corpo["data_base"], "2026-10-27")
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["dossies"][0]["titulo"], "BBAS3 — cenário de aporte")
        self.assertIn("não é recomendação", corpo["aviso"])

    def test_data_sem_dossie_retorna_404_com_campo(self):
        resposta = self.client.get("/api/v1/analise/dossies/2026-01-01")
        self.assertEqual(resposta.status_code, 404)
        corpo = resposta.json()
        self.assertEqual(corpo["campo"], "data")
        self.assertIn("dossies/", corpo["sugestao"])

    def test_data_fora_do_formato_retorna_422(self):
        resposta = self.client.get("/api/v1/analise/dossies/27-10-2026")
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "data")
