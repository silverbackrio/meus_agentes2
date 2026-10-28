"""
Serializers do app market_data.

Regra R2 (`specs/aplicacao.md`): toda resposta que traz número tem
`valor`, `unidade`, `data_base` e `fonte`/`as_of` — sem exceção.
Erro: `{erro, campo, sugestao}`.
"""
from rest_framework import serializers

from .models import FetchLog, Observation, Serie, Source


class SourceSerializer(serializers.ModelSerializer):
    """Fonte de onde vêm os dados."""

    class Meta:
        model = Source
        fields = [
            "id", "nome", "tipo", "url_base", "licenca",
            "exige_chave", "cota_por_dia", "ativo", "observacao",
        ]


class SerieSerializer(serializers.ModelSerializer):
    """Série histórica."""

    source_nome = serializers.CharField(source="source.nome", read_only=True)
    source_tipo = serializers.CharField(source="source.tipo", read_only=True)

    class Meta:
        model = Serie
        fields = [
            "id", "source", "source_nome", "source_tipo",
            "codigo", "nome", "ativo", "unidade", "frequencia", "moeda",
        ]


class ObservationSerializer(serializers.ModelSerializer):
    """Observação de uma série em uma data.

    Regra R2: inclui `data_base`, `unidade` e `fonte` via `serie__source`.
    """
    data_base = serializers.DateField(source="data", read_only=True)
    unidade = serializers.CharField(source="unidade", read_only=True)
    fonte = serializers.SerializerMethodField()

    def get_fonte(self, obj):
        """Regra R9: proveniência obrigatória — fonte e URL de origem."""
        if obj.serie and obj.serie.source:
            return {
                "nome": obj.serie.source.nome,
                "tipo": obj.serie.source.tipo,
                "url": obj.serie.source.url_base,
                "licenca": obj.serie.source.licenca,
            }
        return {"nome": "", "tipo": "", "url": "", "licenca": ""}

    class Meta:
        model = Observation
        fields = [
            "id", "serie", "data", "data_base", "valor",
            "unidade", "fetched_at", "fonte", "payload_hash",
        ]


class ObservationInputSerializer(serializers.Serializer):
    """Entrada para ingestão de observação."""
    serie_id = serializers.IntegerField()
    data = serializers.DateField()
    valor = serializers.DecimalField(max_digits=20, decimal_places=8)
    unidade = serializers.CharField(max_length=100, required=False, default="")


class FetchLogSerializer(serializers.ModelSerializer):
    """Log de ingestão: source, dia, endpoint, status, itens, latência."""

    class Meta:
        model = FetchLog
        fields = [
            "id", "source", "dia", "endpoint",
            "status", "itens", "latencia",
        ]
