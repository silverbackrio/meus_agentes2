"""Serializers do app market_data — contrato de leitura da API v1.

Regra R2 (`specs/aplicacao.md`): toda resposta que traz número entrega `valor`,
`unidade`, `data_base`/`as_of` e a **proveniência** (fonte e licença, regra R9 de
`specs/fontes-de-dados.md`). Aqui só modelamos a estrutura fixa; cobertura, gaps e
pontos são montados na view, porque dependem do período pedido.
"""

from rest_framework import serializers

from .models import Serie, Source


class SourceSerializer(serializers.ModelSerializer):
    """Fonte do dado — nome, tipo, URL e licença sempre visíveis (R9)."""

    class Meta:
        model = Source
        fields = ["id", "nome", "tipo", "url_base", "licenca", "exige_chave", "cota"]


class SerieSerializer(serializers.ModelSerializer):
    """Série com a fonte embutida: o leitor nunca precisa de uma segunda chamada.

    O campo sai como `fonte` (em vez de `source`) porque a API inteira fala
    português — o contrato da `specs/aplicacao.md` é em pt-BR.
    """

    fonte = SourceSerializer(source="source", read_only=True)

    class Meta:
        model = Serie
        fields = [
            "id",
            "fonte",
            "codigo",
            "nome",
            "ativo",
            "unidade",
            "frequencia",
            "moeda",
        ]
