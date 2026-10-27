---
name: renda-fixa-brasil
description: "Calcule, compare e explique renda fixa no Brasil (CDB, LCI/LCA, CRI/CRA, letras, debêntures e títulos públicos do Tesouro): taxa equivalente, rendimento liquido de IR e IOF, marcação a mercado, duration e comparação em base liquida. Use sempre que a pergunta envolver CDI, Selic, IPCA, juros reais, prefixado, liquidez de título ou escolha entre produtos de renda fixa."
metadata:
  category: investimentos
  classe_de_ativo: renda-fixa
  pais: brasil
---
# Renda Fixa Brasil

Guia para calcular, comparar e explicar produtos de renda fixa brasileiros. O leitor precisa sair
com um número líquido, a conta que produziu esse número e a data-base das regras usadas.

## Quando usar

- Comparar dois ou mais produtos (CDB × LCI × Tesouro IPCA+).
- Traduzir uma taxa contratada em retorno líquido, anual ou equivalente.
- Explicar o que acontece se o investidor resgatar antes do prazo.
- Avaliar sensibilidade a juros, inflação ou preço de mercado de um título.

## Conhecimento

### 1. Instrumentos, em uma tabela

| Instrumento | Remunera por | Liquidez | IR | Risco principal |
|---|---|---|---|---|
| LFT / Tesouro Selic | Selic over | vencimento (resgate em D+1 com marcação) | regressivo | taxa |
| LTN / NTN-F | prefixada | idem | regressivo | taxa (marcação) |
| NTN-B / NTN-B Principal | IPCA + juro real | idem | só sobre rendimentos | taxa e inflação |
| CDB / RDB | CDI, prefixada ou híbrida | prazo ou D+0/D+30 conforme produto | regressivo | crédito + FGC |
| LCI / LCA | CDI, prefixada ou IPCA | prazo (geralmente longo) | **isento** | crédito + FGC |
| Letra Financeira (LF) | prefixada/CDI | prazo | regressivo | crédito |
| Letra de câmbio (LC) | prefixada/CDI | prazo | regressivo | crédito |
| CRI / CRA | IPCA ou prefixada | prazo | **isenso** | crédito (sem FGC) |
| Debênture | prefixada ou híbrida | prazo | regressivo | crédito |
| Debênture incentivada (Lei 12.431/2011) | prefixada/híbrida | prazo | **0%** para PF elegível | crédito |

- LCI, LCA, CRI e CRA são isentos de IR para pessoa física (Lei 11.033/2004, art. 3º); não há
  limite de rendimento ou de titulares para essa isenção. **LF e LC não são isentas.**
- Debênture incentivada só tem 0% se a emissão preencher os requisitos legais — verifique o
  material de oferta, não o rótulo do mercado.
- FGC cobre até R$ 250 mil por CPF por instituição; CRI/CRA e debêntures não têm FGC.

### 2. Tributação (vigente em 2026 — Lei 11.033/2004)

| Prazo da aplicação | Alíquota |
|---|---|
| Até 180 dias | 22,5% |
| 181 a 360 dias | 20% |
| 361 a 720 dias | 17,5% |
| Acima de 720 dias | 15% |

- IOF em resgate antes do 30º dia: regressivo sobre o rendimento e limitado a ele
  (Decreto 6.306/2007), zerando no 30º dia. Não é 1% sobre o principal.
- Títulos públicos: o IR incide sobre os **rendimentos**; no Tesouro IPCA+ o principal é isento.
- Taxa de custódia do Tesouro Direto: 0,20% a.a. (há exceções; confirme na B3).

### 3. Fórmulas

- **Valor futuro**: `VF = VI × (1 + i)^n` (i e n na mesma base de tempo).
- **Taxa equivalente**: `(1 + i_origem)^n_origem = (1 + i_destino)^n_destino`.
- **De mensal para anual efetiva**: `i_a = (1 + i_m)^12 − 1`.
- **Rendimento líquido**: `Líquido = VF − VI − (IR × rendimento) − IOF`.
- **IR pelo prazo**: `IR = rendimento_bruto × alíquota_da_faixa(prazo_em_dias)`.
- **Desconto de fluxo (marcação)**: `P = Σ CF_t / (1 + i_t)^t`, com o dia fracionário do período
  expondo a taxa na base correta.
- **Duration modificada**: sensibilidade aproximada do preço a 1 p.p. de taxa:
  `ΔP/P ≈ −D_mod × Δi`.

### 4. Comparação justa

Antes de comparar dois produtos, **equivalente-os**: mesmo prazo, mesmo risco de crédito, mesma
liquidez e **base líquida**. Um CDB isento de 90% do CDI não se compara a um CDB tributado de 95%
do CDI sem passar ambos pelo IR.

Equação padrão de comparação, sempre mostrada ao usuário:

```
líquido = VI × [(1 + taxa)^prazo] × (1 − IR) − IOF
```

Para pós-fixados, trabalhe em fração do CDI sobre a projeção da curva de juros e declare que a
projeção é cenário, não garantia.

### 5. Erros comuns que este guia evita

1. Tratar taxa nominal como efetiva (o CDI é taxa **efetiva** anual).
2. Usar 360 dias para títulos que usam 252 dias úteis, ou vice-versa, sem dizer qual usou.
3. Esquecer o IOF na simulação de resgate curto.
4. Comparar isento com tributado sem líquido.
5. Ignorar marcação a mercado em venda antes do vencimento.
6. Assumir que liquidez D+0 existe em todo CDB.

## Instruções

1. Confirme o instrumento exato, a taxa, o prazo, a data-base e a convenção de dias (252 úteis
   ou 360 corridos).
2. Escreva a fórmula, substitua as entradas e só então o resultado, com unidade (a.a., a.m.,
   % do CDI).
3. Calcule bruto e líquido, informando qual faixa de IR e o IOF quando couber.
4. Compare em base líquida, equivalenciando prazo, risco e liquidez.
5. Liste os riscos que mudam o resultado: liquidez, crédito, marcação a mercado, inflação.
6. Cite a norma e a data de vigência de toda regra tributária; se não houver confirmação
   oficial, declare a incerteza em vez de estimar.

## Fontes oficiais

- Receita Federal — Tributação de 2026: https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026
- Planalto — Lei 11.033/2004: https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l11033.htm
- Planalto — Lei 12.431/2011 (debêntures incentivadas): https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12431.htm
- Planalto — Decreto 6.306/2007 (IOF): https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/decreto/d6306compilado.htm
- Tesouro Direto: https://www.tesourodireto.com.br
- B3 — tarifas do Tesouro Direto: https://www.b3.com.br/pt_br/produtos-e-servicos/tarifas/tarifas-de-tesouro-direto/