"""Views do app documentos — API v1 /api/v1/documentos/.

Nenhum cálculo aqui (R4): a leitura está em `layouts/`, a gravação de operação
em `services.promover`, e a view só valida entrada e monta a resposta.

Regra R3 não é afetada: `documentos` não escreve `observations` de mercado; a
escrita que ela faz é de `Operacao` da carteira, sob comando explícito do
usuário (`POST .../promover/`).

Entrada aceita três formas, e o erro **diz qual foi recebida**:
- multipart com `arquivo` (PDF, imagem, txt);
- JSON com `texto`;
- form-urlencoded com `texto`.
"""

import hashlib

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .extracao import ErroExtracao, diagnosticar, extrair_texto
from .layouts.nota_corretagem import ErroLayout
from .models import Documento
from .serializers import DocumentoSerializer
from .services import promover, registrar


def _erro(mensagem: str, campo: str, sugestao: str, codigo=status.HTTP_422_UNPROCESSABLE_ENTITY):
    return Response({"erro": mensagem, "campo": campo, "sugestao": sugestao}, status=codigo)


def _dados(request) -> dict:
    """Campos de formulário como dicionário — vale para JSON e para QueryDict."""
    corpo = request.data
    return corpo if hasattr(corpo, "get") else {}


def _arquivo(request):
    """Arquivo enviado em multipart (campo `arquivo`), se houver."""
    return request.FILES.get("arquivo") if request.FILES else None


def _nome(arquivo, dados: dict) -> str:
    return str(dados.get("nome_original") or (arquivo.name if arquivo is not None else ""))


@api_view(["GET", "POST"])
def documentos_list_create(request):
    """GET lista documentos; POST recebe arquivo ou texto e extrai os lançamentos."""
    if request.method == "GET":
        return Response(DocumentoSerializer(Documento.objects.all(), many=True).data)

    dados = _dados(request)
    arquivo = _arquivo(request)
    texto = str(dados.get("texto") or dados.get("conteudo") or "")
    tipo = str(dados.get("tipo") or "nota_corretagem")
    nome_original = _nome(arquivo, dados)

    if arquivo is not None:
        try:
            texto = extrair_texto(arquivo, nome_original)
        except ErroExtracao as exc:
            return _erro(str(exc), exc.campo, exc.sugestao, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    if not texto.strip():
        recebido = "arquivo" if arquivo is not None else "nada"
        return Response(
            {
                "erro": "documento: nenhum conteúdo chegou ao servidor",
                "campo": "arquivo",
                "sugestao": (
                    "No formulário, escolha o arquivo (PDF, imagem ou txt) ou cole o texto da nota. "
                    "Se o arquivo foi escolhido e o erro continua, use 'Diagnosticar arquivo' para ver "
                    "o que o servidor recebeu."
                ),
                "recebido": recebido,
                "nome_original": nome_original,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
        return Response(
            {
                "erro": str(exc),
                "campo": exc.campo,
                "sugestao": exc.sugestao,
                "diagnostico": diagnosticar(texto.encode("utf-8"), "texto_extraido.txt"),
                "previa": texto[:600],
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    corpo = DocumentoSerializer(documento).data
    corpo["duplicado"] = not criado
    return Response(corpo, status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK)


@api_view(["POST"])
def documento_diagnostico(request):
    """POST /documentos/diagnostico/ — o que o servidor vê no arquivo, sem gravar.

    Responde antes de tentar processar: tipo real, tamanho, páginas, se existe
    camada de texto, se o OCR está disponível e qual caminho será usado.
    """
    dados = _dados(request)
    arquivo = _arquivo(request)

    if arquivo is not None:
        bruto = arquivo.read()
        nome = _nome(arquivo, dados) or arquivo.name
    else:
        texto = str(dados.get("texto") or dados.get("conteudo") or "")
        if not texto.strip():
            return Response(
                {
                    "erro": "diagnostico: nenhum conteúdo recebido",
                    "campo": "arquivo",
                    "sugestao": "Envie 'arquivo' (PDF/imagem/txt) ou 'texto' para diagnosticar.",
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        bruto = texto.encode("utf-8")
        nome = str(dados.get("nome_original") or "texto_colado.txt")

    info = diagnosticar(bruto, nome)
    texto_disponivel = info.pop("texto", "")

    # Se já há texto legível, diz também se o layout é reconhecido — o que o
    # usuário realmente quer saber antes de enviar.
    if texto_disponivel.strip():
        from .layouts import melhor_layout

        layout, confianca = melhor_layout(texto_disponivel)
        info["layout_detectado"] = layout.nome
        info["confianca"] = float(confianca)
        info["layout_reconhecido"] = confianca >= 0.5
        info["previa"] = texto_disponivel[:600]
    else:
        info["layout_detectado"] = ""
        info["confianca"] = 0.0
        info["layout_reconhecido"] = False
        info["previa"] = ""

    return Response(info)


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
