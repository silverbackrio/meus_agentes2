"""Serializers do app documentos."""

from rest_framework import serializers

from .models import Documento, Lancamento


class LancamentoSerializer(serializers.ModelSerializer):
    promovido = serializers.SerializerMethodField()

    class Meta:
        model = Lancamento
        fields = [
            "id",
            "linha",
            "data",
            "ativo",
            "codigo",
            "mercado",
            "especificacao",
            "lado",
            "quantidade",
            "preco",
            "valor",
            "debito_credito",
            "avisos",
            "operacao",
            "promovido",
        ]

    def get_promovido(self, obj: Lancamento) -> bool:
        return obj.operacao_id is not None


class DocumentoSerializer(serializers.ModelSerializer):
    lancamentos = LancamentoSerializer(many=True, read_only=True)
    total_lancamentos = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = [
            "id",
            "nome_original",
            "tipo",
            "layout",
            "confianca",
            "status",
            "as_of",
            "numero_nota",
            "corretora",
            "avisos",
            "erro",
            "lancamentos",
            "total_lancamentos",
            "criado_em",
            "atualizado_em",
        ]

    def get_total_lancamentos(self, obj: Documento) -> int:
        return obj.lancamentos.count()
