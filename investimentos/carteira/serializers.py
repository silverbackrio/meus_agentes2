"""
Serializers do app carteira.

Regra R2 (`specs/aplicacao.md`): toda resposta que traz número tem
`valor`, `unidade`, `data_base` e `fonte`/`as_of` — sem exceção.
Erro: `{erro, campo, sugestao}`.
"""

from rest_framework import serializers

from .models import Classe, Objetivo, Operacao, Perfil, Politica, Posicao


class PosicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Posicao
        fields = [
            "id",
            "owner",
            "ativo",
            "classe",
            "quantidade",
            "preco_medio",
            "moeda",
            "instituicao",
            "atributos",
            "status",
            "data_entrada",
            "data_encerramento",
            "data_criacao",
        ]


class OperacaoSerializer(serializers.ModelSerializer):
    posicao_nome = serializers.CharField(source="posicao.ativo", read_only=True)

    class Meta:
        model = Operacao
        fields = [
            "id",
            "owner",
            "posicao",
            "posicao_nome",
            "evento",
            "data",
            "valor",
            "quantidade",
            "base_de_calculo",
            "aliquota_ir",
            "ir_ja_retido",
            "iof",
            "custos",
            "custo_total",
            "valor_efeito",
            "observacao",
        ]


class ObjetivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Objetivo
        fields = ["id", "owner", "nome", "valor_alvo", "unidade", "horizonte_dias", "liquidez_necessaria"]


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ["id", "owner", "tolerancia", "capacidade_risco", "restricoes"]


class PoliticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Politica
        fields = ["id", "owner", "classe", "peso_alvo", "faixa_min", "faixa_max"]


class ClasseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classe
        fields = ["id", "owner", "nome", "fator_risco", "liquidez"]


class CarteiraResumoSerializer(serializers.Serializer):
    """Resumo de carteira (para uso em views que pedem resumo)."""

    posicoes = PosicaoSerializer(many=True)

    class Meta:
        fields = ["posicoes"]
