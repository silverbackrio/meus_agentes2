"""Serviços do app documentos: ler documento e promover para a carteira.

Duas fronteiras, nesta ordem:

1. `processar(texto)` — função pura de leitura: escolhe o layout, chama o parser
   e devolve o resultado. Sem banco.
2. `promover(documento)` — grava `Operacao` na `carteira`. Compra vira
   `aplicacao`; venda vira `venda`, que **reduz** posição e nunca cria uma nova
   (decisão do usuário em 30/10/2026). Promoção é idempotente: só entra
   lançamento sem operação, então clicar duas vezes não dobra a carteira.
"""

from decimal import Decimal

from django.db import transaction

from investimentos.carteira.models import Operacao, Posicao

from .layouts import CONFIANCA_MINIMA, melhor_layout
from .layouts.nota_corretagem import ErroLayout, NotaExtraida
from .models import MOEDA_PADRAO, Documento, Lancamento


def processar(texto: str, tipo: str | None = None) -> tuple[NotaExtraida, Decimal, str]:
    """Lê o texto com o melhor layout e devolve (resultado, confiança, layout)."""
    layout, confianca = melhor_layout(texto, tipo)
    if confianca < CONFIANCA_MINIMA:
        raise ErroLayout(
            "layout",
            "não reconheci o documento",
            "Formatos suportados hoje: nota de corretagem da B3. "
            "Envie o texto da seção 'Negociações' ou o PDF com camada de texto.",
        )
    return layout.parse(texto), confianca, layout.nome


def registrar(
    *,
    texto: str,
    nome_original: str = "",
    sha256: str = "",
    tipo: str = "nota_corretagem",
    owner=None,
) -> tuple[Documento, bool]:
    """Cria o documento com seus lançamentos. Devolve (documento, criado).

    Reprocessar o mesmo conteúdo (mesmo `sha256`) devolve o documento existente
    em vez de duplicar a leitura.
    """
    if sha256:
        existente = Documento.objects.filter(sha256=sha256, status__in=["extraido", "promovido"]).first()
        if existente is not None:
            return existente, False

    resultado, confianca, layout_nome = processar(texto, tipo)

    with transaction.atomic():
        documento = Documento.objects.create(
            owner=owner,
            nome_original=nome_original[:300],
            sha256=sha256,
            tipo=tipo,
            layout=layout_nome,
            confianca=confianca,
            status="extraido",
            as_of=resultado.data_pregao,
            numero_nota=resultado.numero_nota[:50],
            corretora=resultado.corretora[:200],
            texto=texto,
            avisos="\n".join(resultado.avisos),
        )
        Lancamento.objects.bulk_create(
            [
                Lancamento(
                    documento=documento,
                    linha=negocio.linha,
                    data=negocio.data,
                    ativo=negocio.ativo,
                    codigo=negocio.codigo,
                    mercado=negocio.mercado,
                    especificacao=negocio.especificacao,
                    lado=negocio.lado,
                    quantidade=negocio.quantidade,
                    preco=negocio.preco,
                    valor=negocio.valor,
                    debito_credito=negocio.debito_credito,
                    avisos="\n".join(negocio.avisos),
                )
                for negocio in resultado.negocios
            ]
        )
    return documento, True


def promover(documento: Documento) -> dict:
    """Leva os lançamentos pendentes para `Posicao`/`Operacao` da carteira."""
    pendentes = list(documento.lancamentos.filter(operacao__isnull=True).order_by("linha"))
    criadas: list[dict] = []
    ignorados: list[dict] = []

    with transaction.atomic():
        for lancamento in pendentes:
            posicao = Posicao.objects.filter(
                ativo__iexact=lancamento.ativo, owner=documento.owner
            ).first()

            if lancamento.lado == "V":
                if posicao is None:
                    ignorados.append(
                        {
                            "linha": lancamento.linha,
                            "ativo": lancamento.ativo,
                            "motivo": "venda sem posição cadastrada — gera baixa, não inclusão",
                        }
                    )
                    continue
                evento = "venda"
            else:
                evento = "aplicacao"
                if posicao is None:
                    posicao = Posicao.objects.create(
                        owner=documento.owner,
                        ativo=lancamento.ativo,
                        classe="acoes",
                        quantidade=Decimal("0"),
                        preco_medio=Decimal("0"),
                        moeda=MOEDA_PADRAO,
                        instituicao=documento.corretora,
                    )

            operacao = Operacao.objects.create(
                owner=documento.owner,
                posicao=posicao,
                evento=evento,
                data=lancamento.data,
                valor=lancamento.valor,
                quantidade=lancamento.quantidade,
                base_de_calculo=documento.layout or documento.tipo,
                observacao=f"documento {documento.id}, linha {lancamento.linha}",
            )
            lancamento.operacao = operacao
            lancamento.save(update_fields=["operacao"])
            criadas.append(
                {
                    "linha": lancamento.linha,
                    "ativo": lancamento.ativo,
                    "evento": evento,
                    "operacao_id": operacao.id,
                    "posicao_id": posicao.id,
                }
            )

        documento.status = "promovido"
        documento.save(update_fields=["status", "atualizado_em"])

    data_base = documento.as_of.isoformat() if documento.as_of else None
    return {
        "documento": documento.id,
        "as_of": data_base,
        "criadas": criadas,
        "ignorados": ignorados,
        "total_criadas": len(criadas),
        "total_ignorados": len(ignorados),
        # R2: número sai com valor, unidade e data-base.
        "valor_total": {
            "valor": float(sum((lancamento.valor for lancamento in pendentes), Decimal("0"))),
            "unidade": MOEDA_PADRAO,
            "data_base": data_base,
        },
        "quantidade_total": {
            "valor": float(sum((lancamento.quantidade for lancamento in pendentes), Decimal("0"))),
            "unidade": "títulos",
            "data_base": data_base,
        },
    }
