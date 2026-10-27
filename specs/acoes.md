---
status: ativa
atualizada_em: 2026-10-27
---
# Spec: Ações

## Escopo

**Dentro:** análise fundamentalista de companhias listadas na B3 e BDRs, demonstrações
financeiras, indicadores, valuation, tese de investimento e tributação da operação.
**Fora:** análise técnica preditiva, recomendação de compra/venda, análise de empresas não
listadas, cripto (fora do escopo do projeto).

## Modelo

| Entidade | Campos obrigatórios |
|---|---|
| `Empresa` | ticker, tipo (ON/PN), setor, data da última demonstração, auditor |
| `Demonstracao` | exercício, receita, EBIT, lucro líquido, FCO, capex, dívida líquida, patrimônio, ações diluídas |
| `Indicador` | nome, fórmula, valor, período, ano-base |
| `Valuation` | método, premissas, faixa de valor, data-base, preço de referência |
| `Tese` | premissas verificáveis, catalisadores, horizonte, invalidadores |
| `Operacao` | tipo (comum/day trade), data, corretagem, liquidação, resultado, IR apurado |

## Regras

**R1.** Todo indicador sai com **ano-base** e **fórmula**; série histórica de ao menos 5
exercícios para ROE, margens e ROIC — ano único não serve de conclusão.

**R2.** Comparação de múltiplos só entre pares de mesmo setor, porte e fase de ciclo, com o ano
do múltiplo declarado.

**R3.** Para bancos e seguradoras, usar P/L e P/VP e analisar carteira, inadimplência e capital;
EV/EBITDA não é métrica adequada.

**R4.** Para cíclicas, valorizar sobre ciclo médio (EV/EBIT normalizado), não sobre o pico.

**R5.** Conferência obrigatória entre lucro contábil e geração de caixa: se divergirem por
períodos longos, apontar a causa (capitalização, mudanças de critério, estoques, receita
antecipada).

**R6.** Diluição: usar ações **diluídas** em valor por ação e registrar emissões e recompras no
retorno ao acionista.

**R7.** Valuation exige ao menos **dois métodos** e uma faixa; número único é insuficiente.
Sensibilidade obrigatória em FCD (matriz de WACC × g).

**R8.** Tributação da operação (vigente em 2026): 15% em operação comum e 20% em day trade;
isenção de vendas até R$ 20 mil por mês no mercado à vista, que **não** alcança day trade, BDRs
nem cotas de ETF de ações (Receita Federal, 2026).

**R9.** Dividendos: IRRF de 10% sobre o total pago no mês quando uma mesma empresa paga acima de
R$ 50 mil a uma mesma pessoa física, desde 01/01/2026 (Lei 15.270/2025, art. 6º-A). JCP: 17,5%
desde 01/01/2026 (LC 224/2025), imposto definitivo.

**R10.** Dado de mercado (preço, volume, dividend yield) exige data-base; não é memorizado.

**R11.** Análise separa **fato verificado**, **estimativa** e **dado pendente de pesquisa**.

## Cálculos obrigatórios

```
P/L = preço / LPA            P/VP = preço / VPA
EV/EBITDA = (valor de mercado + dívida − caixa) / EBITDA
ROIC = NOPAT / capital investido
FC livre = FCO − capex
FCD: VA = Σ FCF_t/(1+WACC)^t + [FCF_n(1+g)]/[(WACC−g)(1+WACC)^n]
valor/ação = (VA − dívida líquida + caixa) / ações diluídas
DuPont: ROE = margem líquida × giro de ativos × multiplicador de alavancagem
```

## Critérios de aceite

- [ ] Série de 5 exercícios com fonte e ano-base.
- [ ] Fórmula e entradas de cada indicador visíveis.
- [ ] Faixa de valor por dois métodos, com data-base e preço de referência.
- [ ] Tese com 3 a 5 premissas verificáveis, catalisadores e invalidadores.
- [ ] Riscos incluindo ao menos um de governança.
- [ ] Tributação datada e com norma.
- [ ] Sem recomendação de compra ou venda (`compliance-e-avisos.md`).

## Lacunas

- Dados trimestrais nem sempre estão completos fora do período de divulgação de resultados.
- Projeções de analistas são de terceiros e precisam de autoria e data se forem citadas.
- Empresas com transações relacionadas e mudanças de critério exigem leitura das notas
  explicativas — declarar quando não lidas.