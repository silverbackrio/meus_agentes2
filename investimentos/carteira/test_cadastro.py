"""Testes do cadastro manual de posição e dos eventos com custo.

Cobrem a regra que o usuário pediu em 30/10/2026: o formulário é **mutável por
classe** (CDB pede indexador/vencimento, fundo pede CNPJ/taxa, ouro pede
gramatura) e a posição é controlada até a baixa, com custos e IR registrados.
"""

from decimal import Decimal

from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from .esquemas import CLASSES, CUSTOS, EVENTOS
from .models import Operacao, Posicao
from .validacao import efeito_financeiro, total_custos, validar_atributos


class EsquemaTest(SimpleTestCase):
    """O registro de classes é a fonte única: campos, eventos e custos."""

    def test_toda_classe_tem_campos_e_eventos_validos(self):
        self.assertGreaterEqual(len(CLASSES), 10)
        for nome, classe in CLASSES.items():
            with self.subTest(classe=nome):
                self.assertTrue(classe.campos, f"{nome} sem campos")
                self.assertTrue(classe.eventos, f"{nome} sem eventos")
                for evento in classe.eventos:
                    self.assertIn(evento, EVENTOS)

    def test_classes_exigidas_estao_registradas(self):
        for nome in ("acoes", "etf", "fiis", "fundo", "cdb", "lci_lca", "cri_cra", "debenture", "ouro"):
            self.assertIn(nome, CLASSES)

    def test_cdb_sem_atributos_lista_os_obrigatorios(self):
        _, erros = validar_atributos("cdb", {})

        campos = {erro["campo"] for erro in erros}
        self.assertEqual(campos, {"emissor", "indexador", "taxa", "vencimento"})

    def test_cdb_normaliza_atributos(self):
        normalizado, erros = validar_atributos(
            "cdb",
            {
                "emissor": "Banco A",
                "indexador": "CDI",
                "taxa": "11,5",
                "vencimento": "2028-10-29",
                "liquidez_diaria": "sim",
            },
        )

        self.assertEqual(erros, [])
        self.assertEqual(normalizado["taxa"], "11.5")
        self.assertEqual(normalizado["vencimento"], "2028-10-29")
        self.assertIs(normalizado["liquidez_diaria"], True)

    def test_campo_de_outra_classe_e_recusado(self):
        _, erros = validar_atributos(
            "cdb",
            {
                "emissor": "Banco A",
                "indexador": "CDI",
                "taxa": "11",
                "vencimento": "2028-10-29",
                "cnpj": "00.000.000/0001-00",
            },
        )

        self.assertIn("cnpj", {erro["campo"] for erro in erros})

    def test_percentual_acima_de_cem_e_recusado(self):
        _, erros = validar_atributos(
            "cdb",
            {"emissor": "Banco A", "indexador": "CDI", "taxa": "150", "vencimento": "2028-10-29"},
        )

        self.assertIn("taxa", {erro["campo"] for erro in erros})

    def test_compra_soma_custo_e_venda_subtrai(self):
        custos = {"corretagem": "4.90", "emolumentos": "0.50"}

        self.assertEqual(total_custos(custos), Decimal("5.40"))
        self.assertEqual(efeito_financeiro("aplicacao", Decimal("1000"), custos), Decimal("1005.40"))
        self.assertEqual(efeito_financeiro("venda", Decimal("1000"), custos), Decimal("994.60"))

    def test_provento_nao_soma_custo_dois_vezes(self):
        custos = {"ir": "15.00"}

        self.assertEqual(efeito_financeiro("provento", Decimal("100"), custos), Decimal("100"))

    def test_custos_disponiveis_incluem_ir_e_iof(self):
        nomes = {campo.nome for campo in CUSTOS}

        self.assertTrue({"corretagem", "emolumentos", "custodia", "ir", "iof"} <= nomes)


class CadastroApiTest(TestCase):
    """API do cadastro manual: posição por classe e evento com custos."""

    def setUp(self):
        self.client = APIClient()

    def _criar_posicao(self, classe="acoes", ativo="BBAS3", atributos=None, **extra):
        # Ação exige `tipo_acao`; o helper já preenche o obrigatório da classe.
        if atributos is None:
            atributos = {"tipo_acao": "ON"} if classe == "acoes" else {}
        base = {"ativo": ativo, "classe": classe, "atributos": atributos}
        base.update(extra)
        return self.client.post("/api/v1/carteira/posicoes/", base, format="json")

    def test_classes_endpoint_descreve_formulario(self):
        resposta = self.client.get("/api/v1/carteira/classes/")

        self.assertEqual(resposta.status_code, 200, resposta.content)
        nomes = {item["nome"] for item in resposta.data["classes"]}
        self.assertIn("cdb", nomes)
        self.assertIn("fundo", nomes)
        self.assertIn("ouro", nomes)
        cdb = next(item for item in resposta.data["classes"] if item["nome"] == "cdb")
        indexador = next(campo for campo in cdb["campos"] if campo["nome"] == "indexador")
        self.assertTrue(indexador["obrigatorio"])
        self.assertIn("CDI", indexador["opcoes"])
        self.assertIn("ir", {campo["nome"] for campo in resposta.data["custos"]})

    def test_cadastrar_cdb_completo(self):
        resposta = self._criar_posicao(
            classe="cdb",
            ativo="CDB Banco A 2028",
            atributos={
                "emissor": "Banco A",
                "indexador": "CDI",
                "taxa": "11.5",
                "vencimento": "2028-10-29",
                "fgc": True,
            },
            quantidade="1000",
            preco_medio="1.00",
            data_entrada="2026-10-29",
        )

        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(resposta.data["classe"], "cdb")
        self.assertEqual(resposta.data["status"], "ativa")
        self.assertEqual(resposta.data["atributos"]["indexador"], "CDI")
        self.assertEqual(resposta.data["data_entrada"], "2026-10-29")

    def test_cdb_sem_indexador_responde_422(self):
        resposta = self._criar_posicao(
            classe="cdb",
            ativo="CDB sem indexador",
            atributos={"emissor": "Banco A", "taxa": "11", "vencimento": "2028-10-29"},
        )

        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.data["campo"], "indexador")
        self.assertIn("erros", resposta.data)

    def test_classe_inexistente_responde_422(self):
        resposta = self._criar_posicao(classe="cripto", ativo="BTC")

        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.data["campo"], "classe")

    def test_posicao_sem_ativo_responde_422(self):
        resposta = self.client.post("/api/v1/carteira/posicoes/", {"classe": "acoes"}, format="json")

        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.data["campo"], "ativo")

    def test_operacao_com_custos_calcula_total_e_efeito(self):
        posicao_id = self._criar_posicao(ativo="PETR4", atributos={"tipo_acao": "PN"}).data["id"]

        resposta = self.client.post(
            "/api/v1/carteira/operacoes/",
            {
                "posicao_id": posicao_id,
                "evento": "venda",
                "data": "2026-10-29",
                "valor": "1000.00",
                "quantidade": "100",
                "custos": {"corretagem": "4.90", "emolumentos": "0.50", "ir": "15.00"},
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(resposta.data["custo_total"], 20.40)
        self.assertEqual(resposta.data["valor_efeito"], 979.60)
        self.assertEqual(Operacao.objects.get(id=resposta.data["id"]).ir_ja_retido, Decimal("15.00"))

    def test_evento_incompativel_com_a_classe_responde_422(self):
        posicao_id = self._criar_posicao(
            classe="cdb",
            ativo="CDB Banco A",
            atributos={"emissor": "Banco A", "indexador": "CDI", "taxa": "11", "vencimento": "2028-10-29"},
        ).data["id"]

        resposta = self.client.post(
            "/api/v1/carteira/operacoes/",
            {"posicao_id": posicao_id, "evento": "provento", "data": "2026-10-29", "valor": "10"},
            format="json",
        )

        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.data["campo"], "evento")

    def test_custo_desconhecido_responde_422(self):
        posicao_id = self._criar_posicao().data["id"]

        resposta = self.client.post(
            "/api/v1/carteira/operacoes/",
            {
                "posicao_id": posicao_id,
                "evento": "aplicacao",
                "data": "2026-10-29",
                "valor": "100",
                "custos": {"taxa_inexistente": "1"},
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.data["campo"], "taxa_inexistente")

    def test_encerramento_da_baixa_na_posicao(self):
        posicao_id = self._criar_posicao(ativo="VALE3", atributos={"tipo_acao": "ON"}).data["id"]

        resposta = self.client.post(
            "/api/v1/carteira/operacoes/",
            {
                "posicao_id": posicao_id,
                "evento": "encerramento",
                "data": "2026-10-29",
                "valor": "100",
                "custos": {"corretagem": "1.00"},
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, 201, resposta.content)
        posicao = Posicao.objects.get(id=posicao_id)
        self.assertEqual(posicao.status, "encerrada")
        self.assertEqual(posicao.data_encerramento.isoformat(), "2026-10-29")
