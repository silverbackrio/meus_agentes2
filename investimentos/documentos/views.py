"""Views do app documentos — API v1 /api/v1/documentos/.

Nenhum cálculo aqui (R4): a leitura está em `layouts/`, a gravação de operação
em `services.promover`, e a view só valida entrada e monta a resposta.

Regra R3 não é afetada: `documents` não escreve `observations` de mercado; a
escrita que ela faz é de `Operacao` da carteira, sob comando explícito do
usuário (`POST .../promover/`).
"""

import hashlib

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .extracao import ErroExtracao, extrair_texto
from .layouts.nota_corretagem import ErroLayout
from .models import Documento
from .serializers import DocumentoSerializer
from .services import promover, registrar


def _erro(mensagem: str, campo: str, sugestao: str, codigo=status.HTTP_422_UNPROCESSABLE_ENTITY):
    return Response({"erro": mensagem, "campo": campo, "sugestao": sugestao}, status=codigo)


@api_view(["GET", "POST"])
def documentos_list_create(request):
    """GET lista documentos; POST recebe arquivo ou texto e extrai os lançamentos."""
    if request.method == "GET":
        documentos = Documento.objects.all()
        return Response(DocumentoSerializer(documentos, many=True).data)

    dados = request.data if isinstance(request.data, dict) else {}
    texto = str(dados.get("texto") or dados.get("conteudo") or "")
    tipo = str(dados.get("tipo") or "nota_corretagem")
    arquivo = request.FILES.get("arquivo")
    nome_original = str(dados.get("nome_original") or (arquivo.name if arquivo else ""))

    if arquivo is not None:
        try:
            texto = extrair_texto(arquivo, nome_original)
        except ErroExtracao as exc:
            codigo = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            return _erro(str(exc), exc.campo, exc.sugestao, codigo)

    if not texto.strip():
        return _erro(
            "documento: nenhum conteúdo recebido",
            "arquivo",
            "Envie 'arquivo' (PDF com camada de texto ou .txt) ou 'texto' com o conteúdo da nota.",
        )

    sha256 = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    try:
        documento, criado = registrar(
            texto=texto,
            nome_original=nome_original,
            sha256=sha256,
            tipo=tipo,
            owner=request.user if request.user.is_authenticated else None,
        )
    except ErroLayout as exc:
        return _erro(str(exc), exc.campo, exc.sugestao)

    corpo = DocumentoSerializer(documento).data
    corpo["duplicado"] = not criado
    return Response(corpo, status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK)


@api_view(["GET"])
def documento_detail(request, documento_id: int):
    """GET /documentos/{id}/ — documento com os lançamentos extraídos."""
    documento = Documento.objects.filter(id=documento_id).first()
    if documento is None:
        return _erro(
            f"documento: id {documento_id} não existe",
            "id",
            "Consulte GET /api/v1/documentos/ para ver os ids válidos.",
            status.HTTP_404_NOT_FOUND,
        )
    return Response(DocumentoSerializer(documento).data)


@api_view(["POST"])
def documento_promover(request, documento_id: int):
    """POST /documentos/{id}/promover/ — leva os lançamentos para a carteira.

    Compra vira `aplicacao`; venda vira `venda` e só reduz posição existente.
    Chamar de novo não duplica nada (idempotente por lançamento).
    """
    documento = Documento.objects.filter(id=documento_id).first()
    if documento is None:
        return _erro(
            f"documento: id {documento_id} não existe",
            "id",
            "Consulte GET /api/v1/documentos/ para ver os ids válidos.",
            status.HTTP_404_NOT_FOUND,
        )

    resultado = promover(documento)
    return Response(
        {
            **resultado,
            "documento_detalhe": DocumentoSerializer(documento).data,
            "aviso": (
                "Posições e operações foram gravadas a partir do documento. "
                "Confira os lançamentos antes de usar o número como custo médio."
            ),
        }
    )
