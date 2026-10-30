"""Testes do app carteira — modelos, resumo e registro de operações.

Regra R6 (specs/aplicacao.md): entrada explícita, fórmula da spec, resultado
esperado. Aqui testamos o contrato da API (R2), validação de entrada (422) e
a lógica de resumo que usa analise/calculos.py (princípio P3).
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Objetivo, Operacao, Politica, Posicao


class ObjetivoModelTest(TestCase):
    def test_objetivo_criacao(self):
        usuario = User.objects.create(username="teste")
        obj = Objetivo.objects.create(
            owner=usuario,
            nome="Reserva emergencial",
            valor_alvo=50000,
            unidade="reais",
            horizonte_dias=360,
        )
        self.assertEqual(obj.nome, "Reserva emergencial")


class PosicaoModelTest(TestCase):
    def test_posicao_criacao(self):
        pos = Posicao.objects.create(
            owner=None,
            ativo="BBAS3",
            classe="acoes",
            quantidade=100,
            preco_medio=80,
            moeda="BRL",
        )
        self.assertEqual(pos.quantidade, 100)


class CarteiraResumoTest(TestCase):
    """GET /api/v1/carteira/resumo/ — posições, custo médio, pesos vs política."""

    url = "/api/v1/carteira/resumo/"

    def test_resumo_sem_posicoes_devolve_estrutura_vazia(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total_posicoes"], 0)
        self.assertEqual(corpo["posicoes"], [])
        self.assertIn("as_of", corpo)

    def test_resumo_com_posicao_sem_operacoes_usa_valor_direto(self):
        Posicao.objects.create(
            ativo="BBAS3",
            classe="acoes",
            quantidade=100,
            preco_medio=Decimal("30.00"),
            moeda="BRL",
        )
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(corpo["total_posicoes"], 1)
        pos = corpo["posicoes"][0]
        self.assertEqual(pos["ativo"], "BBAS3")
        self.assertAlmostEqual(pos["quantidade"], 100.0, places=2)
        self.assertAlmostEqual(pos["preco_medio"], 30.0, places=2)
        self.assertAlmostEqual(pos["custo_total"], 3000.0, places=2)
        self.assertAlmostEqual(corpo["custo_total_geral"], 3000.0, places=2)

    def test_resumo_com_posicao_e_operacoes_recalcula_preco_medio(self):
        # Posição inicial: 100 ações a R$ 30,00
        pos = Posicao.objects.create(
            ativo="BBAS3",
            classe="acoes",
            quantidade=100,
            preco_medio=Decimal("30.00"),
            moeda="BRL",
        )
        # Operação de compra: +100 ações a R$ 24,00
        Operacao.objects.create(
            posicao=pos,
            evento="aplicacao",
            data=date.today(),
            valor=Decimal("2400.00"),
            quantidade=Decimal("100"),
        )
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        pos_data = corpo["posicoes"][0]
        # Custo médio recalculado: (100*30 + 100*24) / 200 = R$ 27,00
        self.assertAlmostEqual(pos_data["quantidade"], 200.0, places=2)
        self.assertAlmostEqual(pos_data["preco_medio"], 27.0, places=2)
        self.assertAlmostEqual(pos_data["custo_total"], 5400.0, places=2)

    def test_resumo_com_politica_calcula_pesos(self):
        # Duas posições em classes diferentes
        Posicao.objects.create(
            ativo="BBAS3",
            classe="acoes",
            quantidade=100,
            preco_medio=Decimal("30.00"),
        )
        Posicao.objects.create(
            ativo="CDB Banco X",
            classe="renda_fixa",
            quantidade=1,
            preco_medio=Decimal("10000.00"),
        )
        # Política: 60% ações, 40% renda fixa
        Politica.objects.create(classe="acoes", peso_alvo=60, faixa_min=50, faixa_max=70)
        Politica.objects.create(classe="renda_fixa", peso_alvo=40, faixa_min=30, faixa_max=50)

        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertEqual(len(corpo["pesos_vs_politica"]), 2)
        # Total = 3000 + 10000 = 13000; ações = 3000/13000 = 23.08%
        pesos = {p["classe"]: p for p in corpo["pesos_vs_politica"]}
        self.assertAlmostEqual(pesos["acoes"]["peso_atual"], 23.08, places=2)
        self.assertFalse(pesos["acoes"]["dentro_faixa"])  # 23% < 50%


class OperacaoCreateTest(TestCase):
    """POST /api/v1/carteira/operacoes/ — registro e validação de operações."""

    url = "/api/v1/carteira/operacoes/"

    def _payload(self, **extras):
        payload = {
            "evento": "aplicacao",
            "data": "2026-10-28",
            "valor": "2400.00",
            "quantidade": "100",
        }
        payload.update(extras)
        return payload

    def test_operacao_valida_retorna_201_com_dados(self):
        resposta = self.client.post(
            self.url, self._payload(), content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 201)
        corpo = resposta.json()
        self.assertEqual(corpo["evento"], "aplicacao")
        self.assertEqual(corpo["data"], "2026-10-28")
        self.assertEqual(corpo["valor"], "2400.00")
        self.assertEqual(corpo["quantidade"], "100.00000000")

    def test_campos_obrigatorios_ausentes_retornam_422(self):
        payload = self._payload()
        del payload["valor"]
        resposta = self.client.post(self.url, payload, content_type="application/json")
        self.assertEqual(resposta.status_code, 422)
        corpo = resposta.json()
        self.assertEqual(corpo["campo"], "valor")
        self.assertIn("sugestao", corpo)

    def test_evento_invalido_retorna_422(self):
        resposta = self.client.post(
            self.url, self._payload(evento="compra_especulativa"), content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "evento")

    def test_data_invalida_retorna_422(self):
        resposta = self.client.post(
            self.url, self._payload(data="28/10/2026"), content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "data")

    def test_valor_negativo_retorna_422(self):
        resposta = self.client.post(
            self.url, self._payload(valor="-100"), content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 422)
        self.assertEqual(resposta.json()["campo"], "valor")

    def test_operacao_com_posicao_inexistente_retorna_404(self):
        resposta = self.client.post(
            self.url, self._payload(posicao_id=999), content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.json()["campo"], "posicao_id")

    def test_operacao_com_posicao_valida_retorna_201(self):
        pos = Posicao.objects.create(ativo="BBAS3", classe="acoes", quantidade=100)
        resposta = self.client.post(
            self.url,
            self._payload(posicao_id=pos.id),
            content_type="application/json",
        )
        self.assertEqual(resposta.status_code, 201)
        corpo = resposta.json()
        self.assertEqual(corpo["posicao"], pos.id)
        self.assertEqual(corpo["posicao_nome"], "BBAS3")


class CarteiraListTest(TestCase):
    """GET /api/v1/carteira/ — lista de posições."""

    def test_lista_vazia(self):
        resposta = self.client.get("/api/v1/carteira/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), [])

    def test_lista_com_posicoes(self):
        Posicao.objects.create(ativo="BBAS3", classe="acoes", quantidade=100)
        Posicao.objects.create(ativo="VALE3", classe="acoes", quantidade=50)
        resposta = self.client.get("/api/v1/carteira/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json()), 2)
