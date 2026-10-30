"""Extração de texto de documento recebido (texto, PDF ou imagem).

Três caminhos, nesta ordem:

1. TXT/CSV → decodifica em UTF-8 (com fallback latin-1).
2. PDF → camada de texto via `pypdf`. Se a página não tiver texto (documento
   digitalizado), rasteriza com `pypdfium2` e passa cada página pelo OCR.
3. Imagem (PNG/JPEG/TIFF/BMP/WEBP) → OCR direto.

O OCR usa `pytesseract` + o binário `tesseract`. O binário **não** é uma
dependência Python: é procurado em `TESSERACT_CMD`, no `PATH` e no prefixo local
`~/ocr/env/bin/tesseract` (instalação sem root via micromamba). Faltando
qualquer peça, o erro diz exatamente o que instalar — o sistema nunca finge que
leu o documento.

P5/R13: `pypdf`, `pypdfium2`, `pytesseract` e `Pillow` são dependências
**opcionais** de leitura de arquivo, listadas em `requirements-ocr.txt`. O parser
de domínio continua sem terceiro: ele recebe texto e devolve lançamentos.
"""

import io
import os
import shutil
from importlib.util import find_spec
from pathlib import Path

# Rasterização em 300 dpi: abaixo disso o Tesseract perde dígito em tabela densa.
_DPI_OCR = 300
_CONFIG_OCR = "--psm 6"  # bloco uniforme de texto — preserva a linha da nota


class ErroExtracao(ValueError):
    """Falha de extração no envelope padrão `{erro, campo, sugestao}`."""

    def __init__(self, campo: str, mensagem: str, sugestao: str = "") -> None:
        super().__init__(f"{campo}: {mensagem}")
        self.campo = campo
        self.mensagem = mensagem
        self.sugestao = sugestao


def comando_tesseract() -> str | None:
    """Localiza o binário do Tesseract sem depender de instalação no sistema."""
    candidatos = (
        os.environ.get("TESSERACT_CMD"),
        shutil.which("tesseract"),
        str(Path.home() / "ocr" / "env" / "bin" / "tesseract"),
    )
    for candidato in candidatos:
        if candidato and Path(candidato).is_file():
            return candidato
    return None


def ocr_disponivel() -> tuple[bool, str]:
    """Diz se o OCR pode rodar agora: `(disponível, motivo quando não está)`."""
    faltando = []
    if find_spec("pytesseract") is None:
        faltando.append("pytesseract")
    if find_spec("PIL") is None:
        faltando.append("Pillow")
    if comando_tesseract() is None:
        faltando.append("binário tesseract")
    if faltando:
        return False, "faltando: " + ", ".join(faltando)
    return True, ""


def extrair_texto(arquivo, nome: str = "") -> str:
    """Devolve o texto do documento enviado (texto, PDF — com ou sem camada — ou imagem)."""
    bruto = arquivo.read() if hasattr(arquivo, "read") else bytes(arquivo)
    if not bruto:
        raise ErroExtracao("arquivo", "arquivo vazio", "Reenvie o documento com conteúdo.")

    sufixo = Path(nome or getattr(arquivo, "name", "") or "").suffix.lower()

    if _eh_pdf(bruto, sufixo):
        texto = _texto_de_pdf(bruto)
        if texto.strip():
            return texto
        return _ocr_de_pdf(bruto)

    if _eh_imagem(bruto, sufixo):
        return _ocr_de_imagem(bruto)

    return _texto_de_bytes(bruto)


def _eh_pdf(bruto: bytes, sufixo: str) -> bool:
    return sufixo == ".pdf" or bruto[:4] == b"%PDF"


_MAGIC_IMAGEM = (
    (b"\x89PNG\r\n\x1a\n", ""),
    (b"\xff\xd8\xff", ""),
    (b"II*\x00", ""),
    (b"MM\x00*", ""),
    (b"BM", ""),
)


def _eh_imagem(bruto: bytes, sufixo: str) -> bool:
    if sufixo in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        return True
    return any(bruto.startswith(assinatura) for assinatura, _ in _MAGIC_IMAGEM)


def _texto_de_bytes(bruto: bytes) -> str:
    for codificacao in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return bruto.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise ErroExtracao(
        "arquivo",
        "não consegui decodificar o arquivo como texto",
        "Envie um .txt em UTF-8, um PDF (com texto ou digitalizado) ou uma imagem da nota.",
    )


def _texto_de_pdf(bruto: bytes) -> str:
    """Texto da camada do PDF; vazio quando o PDF é digitalizado ou falta `pypdf`."""
    if find_spec("pypdf") is None:
        return ""
    try:
        from pypdf import PdfReader

        leitor = PdfReader(io.BytesIO(bruto))
        return "\n".join((pagina.extract_text() or "") for pagina in leitor.pages).strip()
    except Exception:  # PDF corrompido cai no OCR, que dá o erro definitivo
        return ""


def _exigir_ocr() -> None:
    disponivel, motivo = ocr_disponivel()
    if disponivel:
        import pytesseract

        comando = comando_tesseract()
        if comando:
            pytesseract.pytesseract.tesseract_cmd = comando
        return

    raise ErroExtracao(
        "arquivo",
        f"o documento precisa de OCR e o OCR não está disponível ({motivo})",
        "Instale as dependências Python com `pip install -r requirements-ocr.txt` e o binário "
        "sem root com `micromamba create -y -p ~/ocr/env -c conda-forge tesseract` "
        "(ou defina TESSERACT_CMD apontando para o executável).",
    )


def _idiomas_ocr() -> tuple[str, ...]:
    """Prefere português; cai para inglês se o traineddata `por` não existir."""
    import pytesseract

    try:
        instalados = set(pytesseract.get_languages(config=""))
    except Exception:
        return ("eng",)
    if "por" in instalados and "eng" in instalados:
        return ("por+eng", "eng")
    if "por" in instalados:
        return ("por", "eng")
    return ("eng",)


def _ocr_pil(imagem) -> str:
    import pytesseract

    if imagem.mode not in {"L", "RGB"}:
        imagem = imagem.convert("RGB")

    ultimo_erro: Exception | None = None
    for idioma in _idiomas_ocr():
        try:
            return pytesseract.image_to_string(imagem, lang=idioma, config=_CONFIG_OCR)
        except pytesseract.TesseractError as exc:  # idioma ausente, binário quebrado
            ultimo_erro = exc
    raise ErroExtracao(
        "arquivo",
        f"o OCR não conseguiu processar a imagem ({ultimo_erro})",
        "Verifique se o tesseract tem o traineddata do idioma ou cole o texto da nota.",
    )


def _ocr_de_imagem(bruto: bytes) -> str:
    _exigir_ocr()
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - coberto por _exigir_ocr
        raise ErroExtracao("arquivo", "OCR precisa do Pillow", "pip install -r requirements-ocr.txt") from exc

    try:
        imagem = Image.open(io.BytesIO(bruto))
        imagem.load()
    except Exception as exc:
        raise ErroExtracao(
            "arquivo",
            f"não consegui abrir a imagem ({exc})",
            "Envie PNG, JPEG, TIFF, BMP ou WEBP legível.",
        ) from exc

    texto = _ocr_pil(imagem).strip()
    if not texto:
        raise ErroExtracao(
            "arquivo",
            "o OCR não encontrou texto legível na imagem",
            "Envie uma foto mais nítida e sem inclinação, ou cole o texto da nota.",
        )
    return texto


def _ocr_de_pdf(bruto: bytes) -> str:
    _exigir_ocr()
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise ErroExtracao(
            "arquivo",
            "PDF digitalizado precisa de 'pypdfium2' para virar imagem antes do OCR",
            "Instale as dependências de OCR: `pip install -r requirements-ocr.txt`.",
        ) from exc

    try:
        documento = pdfium.PdfDocument(bruto)
    except Exception as exc:
        raise ErroExtracao(
            "arquivo",
            f"não consegui abrir o PDF ({exc})",
            "Verifique se o arquivo abre normalmente.",
        ) from exc

    escala = _DPI_OCR / 72
    partes: list[str] = []
    for indice in range(len(documento)):
        pagina = documento[indice]
        imagem = pagina.render(scale=escala).to_pil()
        partes.append(_ocr_pil(imagem))

    texto = "\n".join(parte for parte in partes if parte.strip()).strip()
    if not texto:
        raise ErroExtracao(
            "arquivo",
            "o OCR não encontrou texto legível no PDF",
            "Confira a qualidade do documento digitalizado ou cole o texto da nota.",
        )
    return texto
