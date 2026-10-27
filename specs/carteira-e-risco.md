---
status: ativa
atualizada_em: 2026-10-27
---
# Spec: Carteira e Risco

## Escopo

**Dentro:** definição de objetivo e perfil, alocação entre classes, rebalanceamento, métricas de
risco e retorno, cenários de estresse, derivativos e câmbio como ferramentas de gestão.
**Fora:** gestão contratada, alocador regulado, previsão de mercado, derivativo como alavancagem
apresentada como estratégia, cripto.

## Modelo

| Entidade | Campos obrigatórios |
|---|---|
| `Objetivo` | valor-alvo, unidade (real/nominal), horizonte, liquidez necessária |
| `Perfil` | tolerância, capacidade, horizonte, restrições (isenção, mínimo, liquidez) |
| `Classe` | nome, fator de risco, custo, liquidez, tratamento tributário |
| `Politica` | peso alvo por classe, faixa de tolerância, regra de rebalanceamento |
| `Metrica` | valor, fórmula, período, frequência, base (bruta/líquida, nominal/real), data-base |
| `Cenario` | choque por fator, premissa, impacto em R$ e em %, data da premissa |

## Regras

**R1.** Sequência obrigatória: objetivo → reserva → horizonte → perfil → restrições → classes →
produtos → percentual. Percentual sem objetivo é resposta inválida.

**R2.** Reserva de emergência em ativo líquido é pré-requisito, não uma classe opcional.

**R3.** Diversificação medida por **fator de risco** (juros, inflação, crédito, câmbio, ações),
não por quantidade de produtos. Mesma instituição em 12 emissores é concentração.

**R4.** Toda métrica declara fórmula, período, frequência e base; anualização explícita
(× √12 mensal, × √252 diário) e sem misturar janelas diferentes.

**R5.** Sharpe e Sortino usam taxa livre de risco na mesma base e mesma data do retorno.

**R6.** VaR só com método e horizonte declarados, com o aviso de que **não** é o pior caso.

**R7.** Correlação histórica não se sustenta em crise: sempre acompanhar de teste de estresse.

**R8.** Retorno líquido de IR e custo; para objetivos reais, em base real com IPCA datado.

**R9.** Derivativo entra como proteção ou alavancagem deliberada, sempre com custo, margem, prazo
e payoff em números.

**R10.** Câmbio com PTAX e data; IOF cambial **não** é afirmado sem verificar ato normativo e
situação judicial da data da operação (lacuna registrada em `dominio-e-fontes.md`).

**R11.** Troca de alocação sempre mostra custo, prazo de carência, IR e liquidez do antes e do
depois.

**R12.** O projeto entrega **política de carteira com faixas**, nunca percentual obrigatório ou
ordem de compra (`compliance-e-avisos.md`).

## Cálculos obrigatórios

```
σ        = √[ Σ (r_t − μ)² / (n − 1) ]      anualizar conforme a frequência
ρ        = cov(r_a, r_b) / (σ_a σ_b)
β        = cov(r_p, r_m) / σ²_m
Sharpe   = (r_p − rf) / σ_p
Sortino  = (r_p − rf) / σ_downside
drawdown = (pico − vale) / pico   → máximo no período
impacto  = peso_da_classe × choque_da_classe    → somar por cenário
```

## Critérios de aceite

- [ ] Objetivo, horizonte, reserva e restrições explicitados antes dos percentuais.
- [ ] Política com faixa-alvo, tolerância e regra de rebalanceamento.
- [ ] Justificativa de risco por classe (fator exposto e o que a quebra).
- [ ] Métricas com fórmula, entradas, período e data-base.
- [ ] Ao menos dois cenários de estresse com impacto em R$ e %.
- [ ] Custo, liquidez e tributação de qualquer troca mostrados.
- [ ] Monitoramento definido: o que olhar e com que frequência.
- [ ] Nenhuma recomendação de compra, venda ou alocação obrigatória.

## Lacunas

- Séries de preço com data e fonte exigem pesquisa web; sem data-base, não se calcula risco.
- VaR e volatilidade históricas subestimam caudas — declarar a limitação sempre.
- Cenários são exercícios, não previsões; o texto nunca os apresenta como previsão.