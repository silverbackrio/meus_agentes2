---
name: analise-de-acoes
description: "Analise empresas e ações com método: leitura de DRE, DFC e balanço, indicadores (P/L, P/VP, EV/EBITDA, ROE, ROIC, margens, endividamento), valuation por fluxo de caixa descontado e múltiplos, tese de investimento, riscos e catalisadores. Use quando pedirem fundamentos, balanço, valor justo, alvo de preço, qualidade do resultado ou análise de uma empresa listada."
metadata:
  category: investimentos
  classe_de_ativo: renda-variavel
  pais: brasil
---
# Análise de Ações

Método de análise fundamentalista de companhias listadas, do balanço ao valor justo, com o número
visível em cada etapa. O objetivo é produzir uma **leitura defendável**, não uma recomendação.

## Quando usar

- "Analise a empresa X", "como está os fundamentos de Y".
- Calcular múltiplos, valor justo ou alvo de preço.
- Comparar empresas do mesmo setor.
- Escrever ou revisar uma tese de investimento.

## Conhecimento

### 1. Etapas obrigatórias

1. **O negócio** — o que vende, quem compra, como ganha dinheiro, o que barre entrada, qual o
   ciclo e qual a alavancagem operacional.
2. **Histórico de 5 exercícios** — receita, EBIT, lucro líquido, margens, dívida líquida, ROIC
   e geração de caixa, sempre com o ano-base declarado.
3. **Qualidade do resultado** — convergência entre lucro contábil e fluxo de caixa livre
   acumulado; capitalização de despesas; mudanças de critério; diluição; auditoria.
4. **Retorno ao acionista** — dividendos e JCP, recompras, emissões, ROE desfeito em margem ×
   giro × alavancagem (DuPont).
5. **Valor** — faixa por ao menos dois métodos, e o preço implícito nas premissas de mercado.
6. **Tese** — 3 a 5 premissas verificáveis, catalisadores, horizonte e o que invalida a tese.

### 2. Indicadores

| Grupo | Fórmula |
|---|---|
| Valuation | `P/L = preço / LPA` · `P/VP = preço / VPA` · `EV/EBITDA = (valor de mercado + dívida − caixa) / EBITDA` |
| Retorno | `ROE = lucro líquido / patrimônio líquido` · `ROIC = NOPAT / capital investido` |
| Margem | `margem líquida = lucro / receita` · `margem EBIT = EBIT / receita` |
| Solvência | `dívida líquida / EBITDA` · `cobertura = EBIT / despesa financeira` · `LC = ativo circulante / passivo circulante` |
| Caixa | `FCO = operação − investimento` · `FC livre = FCO − capex de manutenção` |

- Use **média de 3 a 5 anos** para ROE, margens e ROIC: um ano único mente.
- Para **bancos**, troque EV/EBITDA por P/L e P/VP, e analise carteira, inadimplência, *spread*
  e capital (Basileia) — dívida e EBITDA não significam o mesmo.
- Para **empresas cíclicas**, valorize sobre ciclo médio: EV/EBIT normalizado, não EBIT do pico.

### 3. Valuation

**Fluxo de caixa descontado**
```
VA = Σ FCF_t / (1 + WACC)^t  +  [FCF_n × (1 + g)] / [(WACC − g) × (1 + WACC)^n]
valor por ação = (VA − dívida líquida + caixa) / ações diluídas
```
- WACC com custo de capital e estrutura de capital atuais; `g` ≤ crescimento nominal da
  economia e, no mínimo, coerente com a inflação.
- Mostre sensibilidade: faixa de WACC e de g gerando uma **matriz de valor**, não um número só.

**Múltiplos comparáveis**
- Compare com pares do mesmo setor, porte e fase de ciclo; use mediana e faixa, não média.
- Sempre informe o ano-base do múltiplo e se é sobre lucro reportado ou projetado.
- Dobre a apuração: `valor = múltiplo aplicado à métrica fundamental × ações`.

**Outros:** dividend discount model para empresas maduras; *sum-of-the-parts* para holdings e
conglomerados; "earnings yield" (1/P/L) para comparar com a taxa de juros — no Brasil, o
atrativo é lido contra a taxa real, não só contra o CDI.

### 4. Checklist de tese

- [ ] Em 5 frases, o que a empresa faz e por que lucra.
- [ ] ROIC consistente acima do custo de capital, em 5 anos.
- [ ] Caixa convergindo com o lucro.
- [ ] Dívida suportada em cenário de juros altos.
- [ ] Múltiplo atual vs. histórico e vs. pares, com ano-base.
- [ ] 3 premissas verificáveis com prazo.
- [ ] 3 riscos, incluindo um de governança.
- [ ] Catalisadores com horizonte.
- [ ] Preço, valor e a distância entre os dois, com data-base.

### 5. Erros que este método impede

- Tratar EBITDA como caixa livre.
- Usar múltiplo de ano encerrado sem dizer qual.
- Comparar empresas de setores ou ciclos diferentes.
- Ignorar diluição e emissão de ações.
- Confundir preço cair com valor barato.
- Dar alvo de preço sem premissas.
- Recomendar compra ou venda: apresente valor, preço, riscos e cenários; quem decide é o usuário.

## Instruções

1. Confirme ticker, tipo de ação (ON/PN), setor e a data dos dados; se faltar dado, identifique a
   fonte oficial (CVM, B3, central de resultados da companhia) e diga que precisa ser buscado.
2. Monte a série de 5 exercícios com a conta visível e a fonte.
3. Calcule os indicadores com fórmula e entradas, informando ano-base e unidade.
4. Rode ao menos dois métodos de valuation e entregue a **faixa de valor** e o preço com
   data-base.
5. Separe explicitamente: fato verificado × estimativa × dado que precisa de pesquisa web.
6. Feche com tese, premissas, catalisadores, riscos e o limite de responsabilidade de
   `specs/compliance-e-avisos.md`.

## Referências

- CVM — demonstrações financeiras: https://www.gov.br/cvm
- B3 — informações de mercado: https://www.b3.com.br
- Portal do Investidor: https://www.gov.br/investidor