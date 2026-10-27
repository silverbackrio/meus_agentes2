---
name: alocacao-de-carteira
description: "Monte, avalie e rebalanceie uma carteira de investimentos: perfil, horizonte, reserva de emergência, classes de ativo, núcleo-satélite, métricas de risco (volatilidade, correlação, Sharpe, Sortino, drawdown, VaR), testes de estresse e política de rebalanceamento. Use quando pedirem para montar carteira, distribuir percentual, medir risco, comparar portfólios ou planejar aportes e resgates."
metadata:
  category: investimentos
  classe_de_ativo: carteira
  pais: brasil
---
# Alocação de Carteira

Do objetivo ao percentual: primeiro se define para quanto e quando, depois a classe de ativo, e
só então o produto. O percentual é consequência de risco, não de opinião sobre o mercado.

## Quando usar

- Montar ou revisar uma carteira.
- Definir faixas de alocação e regra de rebalanceamento.
- Medir risco e retorno de um portfólio.
- Planejar aportes, resgates e uso da reserva.

## Conhecimento

### 1. Sequência obrigatória

1. **Objetivo** — para quanto, até quando, em termos reais ou nominais.
2. **Reserva** — meses de custo em ativo liquido e sem volatilidade relevante, antes de tudo.
3. **Horizonte e liquidez** — define a capacidade de suportar marcação a mercado.
4. **Perfil** — tolerância (quanto suporta cair) ≠ capacidade (quanto pode perder sem falhar no
   objetivo).
5. **Restrições** — isenção de IR, liquidez mínima, valores mínimos, exposição proibida.
6. **Classes → produtos → percentual** — nesta ordem.

### 2. Classes e o fator de risco que cada uma expõe

| Classe | Fator principal | O que quebra |
|---|---|---|
| Renda fixa prefixada | taxa de juros | alta de juros (marcação a mercado) |
| Renda fixa atrelada a IPCA | inflação + juros reais | choque de juros reais |
| Ações | ciclo e prêmio de risco | recessão, choque de crédito |
| Crédito privado | default e liquidez | estresse bancário |
| Câmbio/dólar | par cambial | fluxo e juro diferencial |
| Imóveis/FII | inadimplência e vacância | crédito e vacância |
| Alternativos | liquidez e opacidade | crise de liquidez |

Diversificação é de **fator**, não de nome: doze CDBs do mesmo banco são uma aposta só.

### 3. Estruturas

- **Núcleo-satélite:** 70–90% replicando referência de baixo custo + 10–30% de escolhas
  ativas com tese.
- **Barbell:** extremos de liquidez e de prazo, evitando a média; útil para objetivos binários.
- **Buckets por horizonte:** cada objetivo tem sua carteira; o que é para 3 meses não pode cair.
- **Rebalanceamento por faixa:** corrigir quando o peso sair de ±3–5 p.p. da faixa-alvo; por
  calendário (semestral) quando o custo operacional importa mais que a precisão.

### 4. Métricas — fórmula e aviso

```
retorno médio         μ = Σ r_t / n
volatilidade          σ = √[ Σ (r_t − μ)² / (n − 1) ]      (anualizar: × √12 mensal, × √252 diário)
correlação            ρ = cov(r_a, r_b) / (σ_a × σ_b)
beta                  β = cov(r_p, r_m) / σ²_m
Sharpe                (r_p − rf) / σ_p        → rf na mesma base (ex-post CDI ou Selic)
Sortino               (r_p − rf) / σ_downside  → só o risco de queda
drawdown máximo       menor (pico − vale) / pico
VaR                   quantil da distribuição de perda; declare horizonte e método
                      (histórico, paramétrico ou Monte Carlo) — VaR não é o pior caso
```

- Toda série declara **período, frequência e data-base**; não compare volatilidade de janelas
  diferentes.
- Retorno sempre **líquido** e, para cruzar classes, em base **real** quando o objetivo for
  real.
- Correlação histórica **colapsa em crise**; use estresse, não só a matriz média.

### 5. Teste de estresse por cenário

Para cada cenário, aplique o choque ao fator e reponha o impacto na carteira:

| Cenário | Choque típico a modelar |
|---|---|
| Alta de juros | +2 p.p. na Selic → queda em NTN-F/LTN e RF longa |
| Queda do dólar | −10% → perda em exposição cambial, ganho em importadoras |
| Crise de crédito | spread +2 p.p. e liquidez seca → debêntures e FII |
| Recessão | ações −25%, inflação e Selic em queda |
| Inflação acima | IPCA +2 p.p. e juros reais altos |

Devolva **impacto em reais e em %** por classe e no total, com a data das premissas.

### 6. O que nunca fazer

- Sugerir percentual sem objetivo, horizonte, reserva e dívidas.
- Tratar cenário como previsão.
- Esconder custo, prazo de carência, IR e liquidez de uma troca.
- Chamar aposta em derivativo de "proteção" sem mostrar o payoff.
- Recomendar compra, venda ou alocação obrigatória: apresente política, cenários e
  consequências; a decisão é do usuário (`specs/compliance-e-avisos.md`).

## Instruções

1. Extraia objetivo, horizonte, reserva, perfil, restrições e o que já existe na carteira.
2. Proponha a política: classes, faixa-alvo e tolerância por classe, com a justificativa de risco
   e a regra de rebalanceamento.
3. Monte os pesos com conta visível e diga o que acontece com o peso atual fora da faixa.
4. Calcule as métricas pedidas com fórmula, entradas, período e data-base; declare a fonte dos
   preços.
5. Rode pelo menos dois cenários de estresse e indique o que quebra a carteira.
6. Feche com monitoramento (o que olhar, com que frequência) e os avisos de
   `specs/compliance-e-avisos.md`.

## Referências

- CVM — dados de mercado: https://www.gov.br/cvm
- B3 — séries e estatísticas: https://www.b3.com.br
- BCB — Séries Temporais: https://www3.bcb.gov.br/sgspub