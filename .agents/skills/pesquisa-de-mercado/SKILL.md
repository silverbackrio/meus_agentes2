---
name: pesquisa-de-mercado
description: "Garimpe dados atuais e históricos na web com fonte e data: cotações, taxas, PTAX, séries de indicadores, preços históricos, resultados, dividendos, notícias e normas. Use quando precisar de dado de mercado ou histórico de um ativo (novo ou já possuído) para sustentar a decisão de iniciar, aumentar, manter ou reduzir o aporte, ou para analisar um investimento passado."
metadata:
  category: investimentos
  atividade: pesquisa
  atualizado_em: 2026-10
---
# Pesquisa de Mercado

Coleta de informação **atual e histórica** com fonte, data e período declarados, para que a
decisão de investimento se apoie em evidência e não em memória do modelo.

## Quando usar

- Antes de decidir iniciar, aumentar, manter ou reduzir o aporte em um ativo.
- Quando a análise pede dado que não está no repositório: cotação, taxa, PTAX, série, resultado,
  dividendos, vacância, notícia ou norma nova.
- Para comparar o que mudou desde a última análise do mesmo ativo.

> Este agente entrega **evidência**. Quem decide o aporte é o usuário; a análise e o cenário são
> de quem especialista, e o limite está em `specs/compliance-e-avisos.md`.

## Regra de ouro

Todo dado sai com **valor + unidade + data-base + fonte (URL)**. Falhou um dos quatro, não entra
no dossiê. Cotação, taxa e spread **nunca** são decorados.

## Fontes por classe de ativo

| Classe | Fonte primária | O que buscar |
|---|---|---|
| Macro e juros | BCB — Séries Temporais/SGS, Copom, dados abertos | Selic, CDI, IPCA, TR, curva pré e pós |
| Câmbio | BCB — PTAX; B3 | dólar comercial, fechamento, PTAX do dia |
| Títulos públicos | Tesouro Direto (API pública); B3 | taxa de compra/venda, preço, vencimento |
| Ações e BDRs | B3; CVM dados abertos (DFP/ITR); RI da companhia; central de resultados | preço, volume, resultado, dividendos, diluição |
| Fundos e ETFs | CVM dados abertos; B3; site do fundo/gestor | patrimônio, taxa, carteira, cota, liquidez |
| FIIs | CVM; B3; portal/RI do FII | vacância, contratos, inadimplência, distribuição |
| Previdência | SUSEP; taxas previdenciais de referência | taxas do plano, regulamento |
| Regulação e norma | Planalto, Receita, CVM, BCB, ANBIMA, SUSEP | norma, artigo, vigência |

Ordem de preferência: **API oficial → página oficial → fonte de mercado**. Terceiro só entra se
for identificado como terceiro, ou se for confirmado pela primária.

## APIs públicas (sem chave — confirme a documentação antes de automatizar)

- **BCB SGS/Séries**: `https://api.bcb.gov.br/dados/serie/bcdatasgs.<codigo>/dados?formato=json`
  — **registre o código da série** que você usou, para ser reproduzível. Não decore códigos:
  consulte o catálogo oficial em cada coleta.
- **BCB PTAX / Olinda**: fechamento cambial do dia.
- **Tesouro Direto**: `https://api.tesourodireto.com.br/json/` — taxas e preços dos títulos.
- **CVM dados abertos**: arquivos por tipo (posições, registros, demonstrações); pesados, baixar
  sob demanda e registrar a data-base do arquivo.
- **Financeiros de terceiros**: exigem política de uso; confirme antes de automatizar e marque a
  fonte como terceira.

Se a API mudar ou bloquear, registre o bloqueio — não force e não substitua por número estimado.

## Modelo de dossiê

Persista em `dados/<classe>/<ativo>/<AAAA-MM-DD>.md` (a pasta `dados/` existe com a convenção):

```markdown
# Dossiê: <ativo>
- coleta: AAAA-MM-DD (fuso) · anterior: <caminho ou "primeira">
- alimenta a decisão: iniciar | aumentar | manter | reduzir | revisão

## Dados atuais
| valor | unidade | data-base | fonte |

## Série histórica
período completo consultado · frequência · fonte · código da série

## O que mudou desde a coleta anterior
fato → efeito possível sobre a tese (sem recomendação)

## Eventos e notícias
data | veículo | o que aconteceu | link | fato ou opinião?

## Lacunas e bloqueios
o que não foi obtido e por quê

## Fontes
URL + data de acesso de cada item
```

## Regras de coleta

1. **Confira `dados/` antes de buscar.** Coleta datada existe? Use-a, diga a data e colete só o
   delta desde então.
2. **Série completa do período pedido.** Nada de recortar o trecho que favorece a conclusão —
   declare o período inteiro que existiu e a frequência.
3. **Histórico × atual são blocos separados**, com fontes diferentes quando forem.
4. **Notícia separa fato de interpretação**: quem, o quê, quando, onde — a leitura vai no campo
   de efeito, marcada como leitura.
5. **Data-base sempre**: dado de ontem com a data de ontem, mesmo que hoje já tenha mudado.
6. **Bloqueio declarado**: página com JS, login, paywall ou anti-bot → diga que não obteve e o
   que o usuário pode fornecer. Proibido preencher a lacuna com estimativa silenciosa.
7. **Uma coleta por rodada**, fontes mais baratas primeiro (API > HTML > manual), e devolutivo
   compacto: tabela e achados, não transcrição de página.
8. **Sem recomendação**: nada de "compre", "aumente o aporte", "venda". O dossiê diz o que mudou,
   o que confirma e o que contradiz.

## Instruções

1. Carregue esta skill e verifique `dados/` por coleta anterior do mesmo ativo.
2. Feche a pergunta antes de buscar: ativo, período, indicadores e **qual decisão isso alimenta**.
3. Colete pela hierarquia de fontes, anotando URL e data de cada item.
4. Normalize (valor, unidade, data-base, fonte) e calcule o que precisar de conta visível —
   variação no período, retorno desde a última coleta.
5. Persista o dossiê com a data no nome e devolva o caminho do arquivo.
6. Responda em 5 blocos: o que foi perguntado → tabela datada → o que mudou → lacunas e
   bloqueios → fontes.

## Fontes

- BCB Séries Temporais: https://www3.bcb.gov.br/sgspub
- BCB dados abertos: https://dadosabertos.bcb.gov.br
- Tesouro Direto: https://www.tesourodireto.com.br
- CVM dados abertos: https://www.gov.br/cvm/pt-br/acesso-a-informacao/dados-abertos
- B3: https://www.b3.com.br
- Planalto: https://www.planalto.gov.br