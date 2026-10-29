"""
Serializers do app analise.

Regra R2 (`specs/aplicacao.md`): toda resposta que traz número tem
`valor`, `unidade`, `data_base` e `fonte`/`as_of` — sem exceção.
Erro: `{erro, campo, sugestao}`.
"""

from rest_framework import serializers

from .models import Cenario, Dossie, Metrica


class MetricaSerializer(serializers.ModelSerializer):
    """Métrica calculada."""

    data_base = serializers.DateField(source="data_base", read_only=True)

    class Meta:
        model = Metrica
        fields = [
            "id",
            "owner",
            "nome",
            "valor",
            "formulacao",
            "periodo",
            "frequencia",
            "base",
            "data_base",
        ]


class CenarioSerializer(serializers.ModelSerializer):
    """Cenário de estresse."""

    premissa_data = serializers.DateField(source="premissa_data", read_only=True)

    class Meta:
        model = Cenario
        fields = [
            "id",
            "owner",
            "nome",
            "fator",
            "premissa",
            "premissa_data",
            "impacto_reais",
            "impacto_pct",
        ]


class DossieSerializer(serializers.ModelSerializer):
    """Dossiê datado."""

    data_base = serializers.DateField(source="data", read_only=True)

    class Meta:
        model = Dossie
        fields = [
            "id",
            "owner",
            "data",
            "data_base",
            "titulo",
            "conteudo",
            "ativos",
        ]
