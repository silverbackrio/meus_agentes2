---
status: ativa
atualizada_em: 2026-10-27
---
# Spec: Fundos, ETFs e FIIs

## Escopo

**Dentro:** fundos de investimento registrados na CVM, ETFs, fundos imobiliários, custo total,
liquidez, tributação dos veículos e critérios de comparação.
**Fora:** fundos exclusivos para investidor qualificado detalhados, FII de tijolo por setor
imobiliário, gestão ativa contratada.

## Modelo

| Entidade | Campos obrigatórios |
|---|---|
| `Fundo` | CNPJ/registro CVM, espécie, classe, gestor, patrimônio, taxa de admin., taxa de performance, benchmark, liquidez (D+n), data-base |
| `ETF` | ticker, índice de referência, taxa, tracking difference, tracking error, volume médio, spread |
| `FII` | ticker, tipo (renda/tijolo), vacância, contrato médio, inadimplência, distribuição/cota, alavancagem, preço por m² |
| `Tributacao` | enquadramento, come-cotas, alíquota no resgate, base, norma e vigência |
| `Comparacao` | horizonte, retorno líquido com custo e imposto, risco, data-base |

## Regras

**R1.** Classificação tributária pelo **prazo médio da carteira**: longo prazo acima de 365 dias,
curto prazo até 365 dias (Lei 14.754/2023). O nome comercial do fundo não determina a alíquota.

**R2.** Come-cotas no último dia útil de **maio** e **novembro**: 15% no regime de longo prazo e
20% no de curto, com complemento no resgate até a alíquota da faixa do prazo.

**R3.** Fundo de curto prazo: 22,5% até 180 dias e 20% acima de 180 dias. Fundo de longo prazo:
tabela regressiva (22,5 / 20 / 17,5 / 15). *Vigente em 2026.*

**R4.** Fundo de ações: enquadramento com pelo menos 67% em ações elegíveis, alíquota de 15% no
resgate, sem come-cotas periódico.

**R5.** ETF de índice de mercado (exceto renda fixa), no regime da Lei 14.754/2023: 15% em
distribuição, amortização, resgate ou alienação, sem come-cotas. ETF de renda fixa (Lei
13.043/2014): 25% (repactuação até 180 dias), 20% (181 a 720), 15% (acima de 720).

**R6.** Venda de ETF de ações: 15% comum, 20% day trade, **sem** isenção de R$ 20 mil. Isenção de
R$ 20 mil vale para ações e ouro financeiro.

**R7.** FII: rendimento isento exige cotas negociadas em bolsa ou balcão organizado, **pelo menos
100 cotistas**, e cotista com menos de 10% das cotas e de menos de 10% dos rendimentos. Ganho na
venda de cotas: **20%**, sem isenção mensal (Lei 8.668/1993; Lei 11.033/2004). *Vigente em 2026.*

**R8.** Isenção de ativo dentro da carteira **não** se transmite automaticamente ao cotista de
fundo ou ETF.

**R9.** Comparação exige custo total e retorno líquido no mesmo horizonte, com come-cotas e taxa
simulados. Proibido comparar ranking de retorno bruto.

**R10.** Taxa de performance depende de benchmark contratado — citar índice, período e regra de
apuração conforme o regulamento.

## Cálculos obrigatórios

```
custo anual   = taxa adm. + performance + trading + spread   (% a.a. do patrimônio)
líquido       = VI × (1 + retorno_bruto − custo)^n × (1 − IR_aplicavel) − come-cotas
tracking diff = retorno do índice − retorno do ETF   (em p.p., no período)
tracking error= σ(retorno_do_fundo − retorno_do_índice)   (anualizada)
TIR líquida   = taxa que iguala aporte, fluxos e valor final líquido
```

## Critérios de aceite

- [ ] Espécie e classificação tributária identificadas antes de qualquer alíquota.
- [ ] Custo total em % a.a. e efeito composto no horizonte do usuário.
- [ ] Retorno líquido com come-cotas/taxa e data-base, sempre com conta visível.
- [ ] Benchmark nomeado e desempenho relativo no período.
- [ ] Liquidez, volume e spread informados para ETF e FII.
- [ ] Para FII: vacância, contrato, inadimplência, distribuição vs. geração de caixa.
- [ ] Norma e data de vigência em cada regra tributária.
- [ ] Sem recomendação de produto (`compliance-e-avisos.md`).

## Lacunas

- ETF de câmbio: tratamento depende do enquadramento — verificar o regulamento do fundo.
- Rentabilidade histórica de fundos depende de série disponível (mínimo de 12 meses úteis para
  divulgação); se faltar, declarar.
- Dados de FIIs (vacância e inadimplência) mudam por divulgação trimestral: datar sempre.