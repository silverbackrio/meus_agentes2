"""Testes do app documentos.

A nota de corretagem de 29/10/2026 (B3, conta do usuário) é a fixture dourada:
entrada explícita, resultado esperado (R6). Os testes da API cobrem leitura,
idempotência da promoção e a regra de que **venda gera baixa, não inclusão**.
"""

from decimal import Decimal

from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from investimentos.carteira.models import Operacao, Posicao

from .layouts.nota_corretagem import ErroLayout, detectar, parse
from .models import Documento

TEXTO_NOTA = """\
Data pregão 29/10/2026
Nº Nota 0
Bovespa - Depósito / Vista
Negociações
Q Negociação C/V Tipo mercado Prazo Especificação do título Quantidade Preço Valor D/C
1-BOVESPA C D2S BBAS BBAS3 ON NM 90 16,60 1.494,00 D
BBAS BBAS3 ON NM Quantidade Total: 90 Preço Médio: 16,6000
1-BOVESPA C D2S BBDC BBDC4F PN N1 10 14,28 142,80 D
1-BOVESPA C D2S BBDC BBDC4F PN N1 4 14,34 57,36 D
BBDC BBDC4F PN N1 Quantidade Total: 14 Preço Médio: 14,2971
1-BOVESPA C D2S ITUB ITUB4F PN N1 10 39,70 397,00 D
ITUB ITUB4F PN N1 Quantidade Total: 10 Preço Médio: 39,7000
"""


class NotaCorretagemParserTest(SimpleTestCase):
    """Leitura da nota é função pura: sem banco, sem Django."""

    def test_le_os_quatro_negocios(self):
        nota = parse(TEXTO_NOTA)

        self.assertEqual(nota.layout, "nota_corretagem_b3")
        self.assertEqual(nota.data_pregao.isoformat(), "2026-10-29")
        self.assertEqual(nota.numero_nota, "0")
        self.assertEqual(len(nota.negocios), 4)
        self.assertEqual({n.ativo for n in nota.negocios}, {"BBAS3", "BBDC4F", "ITUB4F"})
        self.assertEqual(nota.avisos, [])

    def test_primeiro_negocio_conferido_linha_a_linha(self):
        negocio = parse(TEXTO_NOTA).negocios[0]

        self.assertEqual(negocio.especificacao, "BBAS BBAS3 ON NM")
        self.assertEqual(negocio.lado, "C")
        self.assertEqual(negocio.quantidade, Decimal("90"))
        self.assertEqual(negocio.preco, Decimal("16.60"))
        self.assertEqual(negocio.valor, Decimal("1494.00"))
        self.assertEqual(negocio.debito_credito, "D")

    def test_linha_de_total_nao_vira_lancamento(self):
        # 3 ativos com total impresso não podem gerar 3 lançamentos extras.
        self.assertEqual(len(parse(TEXTO_NOTA).negocios), 4)

    def test_venda_e_marcada_como_v(self):
        nota = parse(TEXTO_NOTA.replace("C D2S", "V D2S"))

        self.assertEqual({n.lado for n in nota.negocios}, {"V"})

    def test_divergencia_entre_quantidade_preco_e_valor_gera_aviso(self):
        nota = parse(TEXTO_NOTA.replace("1.494,00", "1.500,00"))

        self.assertIn("divergência", " ".join(nota.negocios[0].avisos))

    def test_sem_data_de_pregao_recusa_leitura(self):
        with self.assertRaises(ErroLayout) as contexto:
            parse("Negociações\nnada aqui\n")

        self.assertEqual(contexto.exception.campo, "data_pregao")

    def test_nota_tem_confianca_alta(self):
        self.assertGreaterEqual(detectar(TEXTO_NOTA), Decimal("0.9"))

    def test_texto_que_nao_e_nota_tem_confianca_baixa(self):
        self.assertLess(detectar("contrato de aluguel de sala comercial"), Decimal("0.5"))


class DocumentosApiTest(TestCase):
    """API: receber documento, listar lançamentos e promover para a carteira."""

    def setUp(self):
        self.client = APIClient()

    def _enviar(self, texto: str = TEXTO_NOTA):
        return self.client.post(
            "/api/v1/documentos/",
            {"texto": texto, "tipo": "nota_corretagem", "nome_original": "nota.txt"},
            format="json",
        )

    def test_upload_extrai_lancamentos(self):
        resposta = self._enviar()

        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(resposta.data["status"], "extraido")
        self.assertEqual(resposta.data["as_of"], "2026-10-29")
        self.assertEqual(resposta.data["total_lancamentos"], 4)

    def test_reenviar_mesmo_documento_nao_duplica(self):
        self._enviar()
        resposta = self._enviar()

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.data["duplicado"])
        self.assertEqual(Documento.objects.count(), 1)

    def test_upload_sem_conteudo_responde_422(self):
        resposta = self.client.post("/api/v1/documentos/", {}, format="json")

        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.data["campo"], "arquivo")
        self.assertIn("sugestao", resposta.data)

    def test_layout_desconhecido_responde_422(self):
        resposta = self._enviar("contrato de aluguel de sala comercial")

        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.data["campo"], "layout")

    def test_promover_cria_posicoes_e_operacoes(self):
        documento_id = self._enviar().data["id"]

        resposta = self.client.post(f"/api/v1/documentos/{documento_id}/promover/")

        self.assertEqual(resposta.status_code, 200, resposta.content)
        self.assertEqual(resposta.data["total_criadas"], 4)
        self.assertEqual(Posicao.objects.count(), 3)
        self.assertEqual(Operacao.objects.count(), 4)
        self.assertEqual(resposta.data["valor_total"]["valor"], 1494.00 + 142.80 + 57.36 + 397.00)
        self.assertEqual(Documento.objects.get(id=documento_id).status, "promovido")

    def test_promover_duas_vezes_nao_duplica(self):
        documento_id = self._enviar().data["id"]
        self.client.post(f"/api/v1/documentos/{documento_id}/promover/")

        resposta = self.client.post(f"/api/v1/documentos/{documento_id}/promover/")

        self.assertEqual(resposta.data["total_criadas"], 0)
        self.assertEqual(Operacao.objects.count(), 4)

    def test_venda_sem_posicao_gera_baixa_e_nao_inclusao(self):
        documento_id = self._enviar(TEXTO_NOTA.replace("C D2S", "V D2S")).data["id"]

        resposta = self.client.post(f"/api/v1/documentos/{documento_id}/promover/")

        self.assertEqual(resposta.data["total_criadas"], 0)
        self.assertEqual(resposta.data["total_ignorados"], 4)
        self.assertEqual(Posicao.objects.count(), 0)
        self.assertEqual(Operacao.objects.count(), 0)
