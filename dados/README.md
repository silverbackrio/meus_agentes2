# dados/ — coletas de mercado

Pasta onde o `pesquisador-de-mercado` persiste o que coletou, para que ninguém gaste token
buscando o mesmo dado duas vezes. Quem lê um dossiê aqui **não refaz a coleta** — só coleta o
delta desde a data do arquivo.

## Convenção

```
dados/<classe>/<ativo>/<AAAA-MM-DD>.md
```

Exemplos:

```
dados/acoes/petr4/2026-10-27.md
dados/renda-fixa/tesouro-ipca-2029/2026-10-27.md
dados/fundos-e-fiis/hglg11/2026-10-27.md
```

- **`<classe>`** usa os nomes das specs: `renda-fixa`, `acoes`, `fundos-e-fiis`, `previdencia`,
  `carteira-e-risco`.
- **`<ativo>`** em minúsculas, sem acento, com o ticker quando existir.
- **`<AAAA-MM-DD>`** é a **data da coleta**, e é ela que define o que já foi pesquisado.
- Uma coleta nova do mesmo ativo **não substitui** a anterior: cria arquivo novo e aponta o
  anterior no cabeçalho.

## O que tem dentro

O modelo completo está na skill `pesquisa-de-mercado`. Todo item carrega **valor, unidade,
data-base e fonte** — faltando um dos quatro, o item não entra.

```markdown
# Dossiê: <ativo>
- coleta: AAAA-MM-DD (fuso) · anterior: <caminho ou "primeira">
- alimenta a decisão: iniciar | aumentar | manter | reduzir | revisão

## Dados atuais            | valor | unidade | data-base | fonte |
## Série histórica         período completo · frequência · fonte · código da série
## O que mudou desde a anterior
## Eventos e notícias      data | veículo | fato | link
## Lacunas e bloqueios
## Fontes
```

## Regras

1. Nada de número sem data-base e URL; nada de dado de memória.
2. Série histórica sempre no período inteiro pedido — recortar para favorecer conclusão é erro.
3. Notícia separa fato de leitura.
4. Bloqueio de acesso é declarado, nunca preenchido com estimativa.
5. Dossiê não recomenda: entrega evidência, cenário fica com o especialista e a decisão com o
   usuário (`specs/compliance-e-avisos.md`).
6. Arquivo é texto puro, sem segredo, token, CPF ou dado de conta.