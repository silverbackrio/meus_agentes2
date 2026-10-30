"""Extração de texto de documento recebido (PDF ou texto puro).

Regra P5 (`specs/aplicacao.md`): o parser de domínio não depende de pacote de
terceiro. O PDF é o único formato que exige biblioteca, e ela entra como
dependência **opcional** — sem `pypdf` instalado o endpoint continua aceitando
o texto da nota, e o erro diz exatamente o que fazer.

OCR de imagem não entra na v1: exigiria `tesseract` no sistema, o que quebra a
portabilidade da P2 e não pode ser verificado aqui. Fica declarado como
limitação, não como suposição.
"""

import io
from pathlib import Path


class ErroExtracao(ValueError):
    """Falha de extração no envelope padrão `{erro, campo, sugestao}`."""

    def __init__(self, campo: str, mensagem: str, sugestao: str = "") -> None:
        super().__init__(f"{campo}: {mensagem}")
        self.campo = campo
        self.mensagem = mensagem
        self.sugestao = sugestao


def extrair_texto(arquivo, nome: str = "") -> str:
    """Devolve o texto do documento enviado (PDF com camada de texto ou txt)."""
    bruto = arquivo.read() if hasattr(arquivo, "read") else bytes(arquivo)
    if not bruto:
        raise ErroExtracao("arquivo", "arquivo vazio", "Reenvie o documento com conteúdo.")

    sufixo = Path(nome or getattr(arquivo, "name", "") or "").suffix.lower()
    if sufixo == ".pdf" or bruto[:4] == b"%PDF":
        return _texto_de_pdf(bruto)
    return _texto_de_bytes(bruto)


def _texto_de_bytes(bruto: bytes) -> str:
    for codificacao in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return bruto.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise ErroExtracao(
        "arquivo",
        "não consegui decodificar o arquivo como texto",
        "Envie um .txt em UTF-8, um PDF com camada de texto, ou cole o texto da nota.",
    )


def _texto_de_pdf(bruto: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ErroExtracao(
            "arquivo",
            "PDF precisa da dependência opcional 'pypdf', que não está instalada",
            "Instale com `uv pip install pypdf` ou envie o texto da nota no campo 'texto'.",
        ) from exc

    try:
        leitor = PdfReader(io.BytesIO(bruto))
        paginas = [(pagina.extract_text() or "") for pagina in leitor.pages]
    except Exception as exc:  # PDF corrompido é erro de entrada, não bug do app
        raise ErroExtracao(
            "arquivo",
            f"não consegui ler o PDF ({exc})",
            "Verifique se o arquivo abre normalmente; se for digitalizado, envie o texto da nota.",
        ) from exc

    texto = "\n".join(paginas).strip()
    if not texto:
        raise ErroExtracao(
            "arquivo",
            "o PDF não tem camada de texto (documento digitalizado)",
            "OCR ainda não é suportado: envie o texto da nota no campo 'texto'.",
        )
    return texto
