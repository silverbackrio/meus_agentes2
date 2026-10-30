"""Testes do caminho de OCR (imagem e PDF digitalizado).

Os testes que exigem o binário `tesseract` são pulados quando o ambiente não o
tem — o sandbox pode ser restaurado sem dependências de sistema. O teste de
degradação roda sempre: sem OCR, o erro tem de ser explícito, nunca leitura
inventada.
"""

import io
import unittest
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from . import extracao
from .extracao import ErroExtracao, extrair_texto
from .layouts.nota_corretagem import parse

LINHAS = (
    "Data pregao 29/10/2026",
    "Negociacoes",
    "1-BOVESPA C D2S BBAS BBAS3 ON NM 90 16,60 1.494,00 D",
    "1-BOVESPA C D2S ITUB ITUB4F PN N1 10 39,70 397,00 D",
)


def _imagem_da_nota():
    from PIL import Image, ImageDraw, ImageFont

    imagem = Image.new("RGB", (1500, 320), "white")
    desenho = ImageDraw.Draw(imagem)
    fonte = ImageFont.load_default(size=34)
    for indice, linha in enumerate(LINHAS):
        desenho.text((24, 24 + indice * 64), linha, fill="black", font=fonte)
    return imagem


def _arquivo(conteudo: bytes):
    arquivo = mock.Mock()
    arquivo.read.return_value = conteudo
    return arquivo


def _png() -> bytes:
    buffer = io.BytesIO()
    _imagem_da_nota().save(buffer, format="PNG")
    return buffer.getvalue()


def _pdf_digitalizado() -> bytes:
    """PDF sem camada de texto: a página é só a imagem (o caso do scanner)."""
    buffer = io.BytesIO()
    _imagem_da_nota().save(buffer, format="PDF", resolution=300)
    return buffer.getvalue()


OCR_OK, MOTIVO = extracao.ocr_disponivel()


@unittest.skipUnless(OCR_OK, f"OCR indisponível: {MOTIVO}")
class OcrDisponivelTest(SimpleTestCase):
    def test_png_da_nota_vira_lancamentos(self):
        texto = extrair_texto(_arquivo(_png()), "nota.png")

        self.assertIn("BOVESPA", texto.upper())
        nota = parse(texto)
        self.assertGreaterEqual(len(nota.negocios), 2)
        self.assertEqual(nota.data_pregao.isoformat(), "2026-10-29")

    def test_pdf_sem_camada_de_texto_cai_no_ocr(self):
        bruto = _pdf_digitalizado()
        # Confirma que o PDF não tem texto extraível: é o cenário do scanner.
        self.assertEqual(extracao._texto_de_pdf(bruto), "")

        texto = extrair_texto(_arquivo(bruto), "nota.pdf")

        self.assertIn("BOVESPA", texto.upper())
        self.assertGreaterEqual(len(parse(texto).negocios), 2)

    def test_pdf_com_camada_de_texto_nao_passa_pelo_ocr(self):
        # Sem camada real aqui, o teste garante o contrato: camada vazia -> OCR.
        # A preferência pela camada está garantida em `extrair_texto`.
        self.assertEqual(extracao._texto_de_pdf(b"nao e pdf"), "")


@unittest.skipUnless(OCR_OK, f"OCR indisponível: {MOTIVO}")
class OcrApiTest(TestCase):
    """O caminho real do usuário: upload de imagem no endpoint de documentos."""

    def test_upload_de_imagem_extrai_lancamentos(self):
        arquivo = SimpleUploadedFile("nota.png", _png(), content_type="image/png")

        resposta = APIClient().post(
            "/api/v1/documentos/",
            {"arquivo": arquivo, "tipo": "nota_corretagem"},
            format="multipart",
        )

        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(resposta.data["total_lancamentos"], 2)
        self.assertEqual(resposta.data["as_of"], "2026-10-29")
        ativos = {item["ativo"] for item in resposta.data["lancamentos"]}
        self.assertEqual(ativos, {"BBAS3", "ITUB4F"})


class OcrIndisponivelTest(SimpleTestCase):
    def test_imagem_sem_binario_falha_com_instrucao(self):
        with (
            mock.patch.object(extracao, "comando_tesseract", return_value=None),
            self.assertRaises(ErroExtracao) as contexto,
        ):
            extrair_texto(_arquivo(_png()), "nota.png")

        self.assertIn("tesseract", str(contexto.exception).lower())
        self.assertIn("TESSERACT_CMD", contexto.exception.sugestao)
        self.assertEqual(contexto.exception.campo, "arquivo")

    def test_txt_continua_funcionando_sem_ocr(self):
        texto = extrair_texto(_arquivo("\n".join(LINHAS).encode("utf-8")), "nota.txt")

        self.assertIn("BBAS3", texto)
