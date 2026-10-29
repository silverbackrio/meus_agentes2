"""
Testes do app carteira.

Valida criação dos modelos básicos e que Posicao tem owner legado
(v1 sem pessoa). Quando formos fazer login, esse teste de owner precisa
de atualização, mas só para ter ciência antes de mexer no código.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from .models import (
    Objetivo,
    Posicao,
)


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
