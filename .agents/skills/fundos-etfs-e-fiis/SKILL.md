---
name: fundos-etfs-e-fiis
description: "Compare e escolha fundos de investimento, ETFs e FIIs com critério: taxa de administração e performance, come-cotas, classificação tributária, benchmark, tracking, liquidez, histórico de gestão, vacância e distribuição. Use quando pedirem para comparar fundos, analisar um ETF, avaliar um fundo imobiliário, entender a taxa de um fundo ou saber quanto sobra líquido em um veículo coletivo."
metadata:
  category: investimentos
  classe_de_ativo: fundos-etfs-fiis
  pais: brasil
---
# Fundos, ETFs e FIIs

Método para comparar veículos coletivos de investimento no Brasil em três dimensões: **custo,
comportamento e o que chega líquido ao cotista**.

## Quando usar

- Comparar dois ou mais fundos, ETFs ou FIIs.
- Explicar taxa, performance, come-cotas ou liquidez de um produto.
- Decidir entre ativo e passivo, ou entre fundo e ativo avulso.
- Simular o retorno líquido de um cotista em determinado horizonte.

## Conhecimento

### 1. O que separa cada veículo

| | Fundo de investimento | ETF | FII |
|---|---|---|---|
| Negociação | resgate na instituição (D+0 a D+30) | em bolsa, intradiário | em bolsa, intradiário |
| Gestão | ativa ou indexada | indexada | ativa (perfil renda ou tijolo) |
| Tributação | come-cotas semestral + tabela por prazo | regime próprio (Lei 14.754/2023); renda fixa tem regra da Lei 13.043/2014 | rendimento isento nas condições legais; venda de cotas a 20% |
| Custo | taxa de admin. + performance + trading | taxa de admin. + spread + tracking error | taxa de admin. + alavancagem |
| Divulgação | regulamento, balancete, valor da cota | indíbase, composição diária | balanço, portfolio de imóveis, vacância |

### 2. Tributação resumida (vigente em 2026)

- **Come-cotas:** último dia útil de maio e novembro; antecipa 15% (longo prazo) e 20% (curto
  prazo), com complemento no resgate. Classificação pelo **prazo médio da carteira**: longo
  prazo acima de 365 dias, curto até 365 dias.
- **Fundo de ações:** ≥ 67% em ações elegíveis, 15% no resgate, sem come-cotas periódico.
- **Fundo de curto prazo:** 22,5% até 180 dias e 20% acima de 180 dias.
- **ETF:** 15% em distribuição/resgate/alienação no regime próprio, sem come-cotas; venda de
  ETF de ações a 15% (comum) e 20% (day trade), **sem** a isenção de R$ 20 mil.
- **ETF de renda fixa:** 25% (repactuação até 180 dias), 20% (181 a 720), 15% (acima de 720).
- **FII:** rendimento isento exige cotas em bolsa ou balcão organizado, ≥ 100 cotistas e cotista
  com menos de 10% das cotas e dos rendimentos; ganho na venda, 20%.

### 3. Custo total — a conta que quase ninguém faz

```
custo anual = taxa de administração
            + taxa de performance (quando houver, sobre o excesso sobre o benchmark)
            + custo de trading/impacto interno
            + spread de negociação (ETF/FII)  → em % a.a. do patrimônio
```
Um fundo de 2% a.a. de custo num cenário de retorno de CDI + 1,5 p.a. consome mais de metade do
excesso sobre o CDI. **Sempre mostre o efeito composto:** `VF_final = VI × (1 + r_bruto −
custo)^n`.

- **Taxa de performance** só é cobrada se houver benchmark contratado — leia o regulamento: qual
  índice, sobre qual período, com *high-water mark* ou não.
- Para fundo de ações, some taxa de corretagem de carteira e custo de rotação ao *turnover*.

### 4. Critérios de comparação

1. **Objetivo e benchmark** — o fundo mede sucesso contra o quê? CDI, Ibovespa, IPCA+?
2. **Retorno líquido e consistência** — quão frequente bate o benchmark (percentil, não média).
3. **Custo** — taxa, spread, *tracking difference* e *tracking error* do ETF.
4. **Liquidez** — D+ do resgate; no ETF/FII, volume médio diário e spread da melhor oferta.
5. **Risco** — volatilidade, drawdown, concentração da carteira, alavancagem, contraparte.
6. **Gestão** — tempo do gestor, histórico, patrimônio, concentração em gestor e turnover.
7. **Para FII** — vacância, contrato restante, inadimplência, preço por m², distribuição vs.
   geração de caixa real e alavancagem.
8. **Para ETF** — aderência ao índice, liquidez, *spread*, dividendos replicados e amostra de
   rebalanceamento.

### 5. Erros que este guia evita

- Achar que ETF de carteira isenta é isento para o cotista: **a isenção do ativo não passa
  automaticamente ao fundo**.
- Comparar retorno bruto entre fundos com taxas e riscos diferentes.
- Tratar come-cotas como imposto dobrado (é adiantamento com juros sobre imposto).
- Ignorar que a cota de fundo marca a mercado e pode cair mesmo quando o ativo rende.
- Escolher pelo ranking de retorno do mês anterior.
- Recomendar o produto: comparar e explicar; a escolha é do usuário.

## Instruções

1. Identifique a espécie/categoria registrada na CVM e a classificação tributária — sem isso, a
   alíquota não está definida.
2. Extraia: patrimônio, taxa, liquidez, benchmark, histórico (ao menos 3 anos) e risco.
3. Calcule o retorno líquido no horizonte do usuário, com come-cotas, taxa e data-base,
   mostrando a conta.
4. Compare com o benchmark e com ao menos uma alternativa equivalente em risco, em base líquida.
5. Liste o que precisa ser conferido no regulamento ou no site do gestor antes de decidir.
6. Cite a norma e a data de vigência de toda regra tributária; declare incerteza quando não
   houver confirmação oficial.

## Fontes oficiais

- CVM — Resolução 175 (fundos): https://conteudo.cvm.gov.br/legislacao/resolucoes/resol175.html
- Planalto — Lei 14.754/2023: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14754.htm
- Planalto — Lei 13.043/2014 (ETF de renda fixa): https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l13043.htm
- Planalto — Lei 8.668/1993 (FIIs): https://www.planalto.gov.br/ccivil_03/leis/l8668.htm
- ANBIMA — transparência de fundos: https://www.anbima.com.br