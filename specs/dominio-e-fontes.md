---
status: ativa
atualizada_em: 2026-10-27
---
# Domínio e Fontes

Modelo comum a todas as classes de ativo: o que é um "investimento" neste projeto, quais campos
são obrigatórios em qualquer cálculo e onde a verdade oficial mora.

## Escopo

**Dentro:** pessoa física residente no Brasil, investimentos em reais, mercado local e
internacional acessível a PF, análise e educação.

**Fora:** recomendação personalizada, gestão de carteira contratada, produtos institucionais
(FIIs de tijolo corporativos, CRAs e debêntures de grande porte, estruturados para investidor
qualificado), direito
tributário contencioso e decisões de crédito.

## Modelo comum

Toda resposta que envolva um número deve ser expressável nestas entidades:

### Ativo
```
classe          renda-fixa | renda-variavel | fundo | etf | fii | previdencia | caixa | derivativo
instituicao     emissor, gestor ou corretora, com a data do dado
ticker/codigo   quando existir
moeda           BRL | USD | outra
remuneracao     prefixada | pos-fixada | hibrida, com o marcador (CDI, Selic, IPCA+, TR, Ibovespa)
prazo           em dias úteis ou corridos — sempre declarar qual
liquidez        D+0 | D+n | vencimento | bloqueio/carência
risco           credito | taxa | mercado | liquidez | inflacao | contraparte
tributacao      isento | regressivo | progressivo | fundo-come-cotas | ganho-de-capital
                + a norma e a data de vigência
```

### Operação
```
eventos         aplicacao | resgate | venda | distribuicao | portabilidade | beneficio | amortizacao
base_de_calculo valor | rendimento | ganho
aliquota        em % + faixa ou prazo que a determinou
imposto_ja_retdo em % e em R$
iof             se aplicável, com a régua de dias
data_base       obrigatória — sem data-base não há número válido
```

### Carteira
```
objetivo        valor-alvo, unidade (real ou nominal) e horizonte
classes         com peso alvo e faixa de tolerância
metricas        periodo, frequencia, base (bruta/líquida, nominal/real) e data-base
cenarios        choque por fator com a premissa datada
```

## Regras de unidade

- Taxa sempre com unidade: **a.a.**, **a.m.**, **% do CDI**, **% a.m. do CDI**.
- Dia: declarar **útil ou corrido**; CDI/Selic trabalham em base 252 úteis em várias regras.
- Valores em reais com data-base; cotação sempre com data e fonte.
- Percentual sem base (sobre patrimônio, sobre capital, sobre rendimento) é erro de spec.

## Fontes oficiais

| Assunto | Fonte | URL |
|---|---|---|
| Alíquotas e tabelas de IR | Receita Federal | https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026 |
| Legislação (leis, decretos, emendas) | Planalto | https://www.planalto.gov.br |
| Títulos públicos e custódia | Tesouro Direto / B3 | https://www.tesourodireto.com.br |
| Fundos, BDRs, ofertas | CVM | https://www.gov.br/cvm |
| Dados de mercado e negociação | B3 | https://www.b3.com.br |
| Taxa Selic, câmbio PTAX, séries | Banco Central | https://www3.bcb.gov.br/sgspub |
| Previdência e seguros | SUSEP | https://www.gov.br/susep |
| Referência de mercado e índices | ANBIMA | https://www.anbima.com.br |
| Investidor pessoa física | Portal do Investidor | https://www.gov.br/investidor |

## Regras de validação de fonte

1. Regra tributária só entra em skill com **norma + data de vigência**.
2. Se duas fontes divergirem, prevalece a norma original no Planalto e a página da Receita.
3. Dado de mercado (cotação, taxa, spread, PTAX) **nunca** é decorado: exige pesquisa web com
   data-base, ou é declarado como exemplo com a data explícita.
4. Regra recente (alterada nos últimos 12 meses) exige reconferência na fonte antes de afirmar.
5. Quando a fonte oficial estiver omissa, o texto diz **"não confirmado — verificar"** em vez
   de inferir.

## Lacunas conhecidas (2026-10-27)

- **IOF cambial:** o Decreto 12.499/2025 foi sustado e parcialmente restabelecido pelo STF, com
  desfecho em disputa. Não afirmar alíquota sem consultar o ato e a situação judicial da data da
  operação.
- **Limite de isenção de LCI/LCA:** não há teto de rendimento ou de titulares confirmado em
  fonte oficial; a formulação de "10% dos créditos de cada banco" não foi confirmada como regra
  tributária.
- **ETF de câmbio:** tratamento tributário depende do enquadramento do produto; verificar o
  regulamento.
- Toda alíquota citada aqui está datada em **2026** e precisa ser reconferida a cada virada de
  ano-calendário e a cada publicação de lei complementar da reforma tributária.