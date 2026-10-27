---
status: ativa
atualizada_em: 2026-10-27
---
# Spec: Renda Fixa

## Escopo

**Dentro:** títulos públicos, títulos bancários, crédito privado, marcadores de juros, cálculo de
taxa equivalente, rendimento líquido e marcação a mercado no Brasil.
**Fora:** derivativos (ver `carteira-e-risco.md`), fundos de renda fixa (ver
`fundos-e-fiis.md`), debênture de infraestrutura detalhada por setor.

## Modelo

| Entidade | Campos obrigatórios |
|---|---|
| `TituloPublico` | espécie (LFT, LTN, NTN-F, NTN-B, NTN-B Principal), data-base, taxa de compra/venda, taxa de custódia, isenção do principal (IPCA+) |
| `TituloPrivado` | emissor, espécie (CDB, RDB, LCI, LCA, LF, LC, CRI, CRA, debênture), taxa contratada, marcador, prazo, liquidez, cobertura do FGC |
| `Marcador` | nome, base (252 úteis / 360 corridos), data de referência, origem da série |
| `Simulacao` | VI, taxa, prazo, data-base, faixa de IR, IOF, VF bruto, VF líquido |

## Regras

**R1.** Isentos de IR para pessoa física: LCI, LCA, CRI, CRA (Lei 11.033/2004, art. 3º) e
debêntures incentivadas elegíveis (Lei 12.431/2011). **LF e LC não são isentas.** *Vigente em
2026.*

**R2.** Tabela regressiva de renda fixa, vigente em 2026: 22,5% até 180 dias; 20% de 181 a 360;
17,5% de 361 a 720; 15% acima de 720 dias (Lei 11.033/2004).

**R3.** IOF em resgate antes do 30º dia é regressivo **sobre o rendimento** e limitado a ele,
zerando no 30º dia (Decreto 6.306/2007). Não é 1% sobre o principal.

**R4.** Em títulos públicos o IR incide sobre os **rendimentos**; no NTN-B o principal é isento.
Taxa de custódia da B3: 0,20% a.a., com exceções — confirmar tabela vigente na B3.

**R5.** Comparação entre produtos exige equivalência de prazo, risco de crédito, liquidez e
**base líquida**. Proibido comparar taxa bruta de isento com taxa bruta de tributado.

**R6.** Letra financeira e letra de câmbio não herdam a isenção de LCI/LCA; nunca apresentá-las
como isentas.

**R7.** Debênture só é "incentivada" com emissão enquadrada na Lei 12.431/2011 — verificar o
material de oferta, não a nomenclatura de mercado.

**R8.** Resgate antecipado de título de longo prazo depende de **preço de mercado**, não da taxa
contratada; a simulação precisa da taxa vigente na data-base.

**R9.** FGC: até R$ 250 mil por CPF por instituição; CRI, CRA e debêntures não têm cobertura.

**R10.** CDI é taxa **efetiva** anual; capitalização em frações do CDI segue convenção diária e
precisa ser declarada na simulação.

## Cálculos obrigatórios

```
VF            = VI × (1 + i)^n
equivalência  = (1 + i_a)^n_a = (1 + i_b)^n_b
líquido       = VF − VI − (rendimento × alíquota_faixa) − IOF
preço         = Σ CF_t / (1 + i_t)^t
ΔP/P          ≈ −D_mod × Δi          (choque de taxa, em decimal)
```

Toda simulação apresenta: entradas, fórmula, alíquota e faixa usadas, IOF quando aplicável,
data-base e o resultado líquido com unidade.

## Critérios de aceite

- [ ] Todo número sai com data-base e unidade.
- [ ] A alíquota de IR vem da faixa do prazo, com a norma citada.
- [ ] Comparação feita em base líquida e com prazos equivalenciados.
- [ ] Riscos listados: liquidez, crédito, marcação a mercado, inflação.
- [ ] Regra tributária datada (2026) e com fonte oficial.
- [ ] Nenhuma promessa de retorno e nenhuma recomendação de produto (`compliance-e-avisos.md`).

## Lacunas

- Taxa de custódia e tarifas do Tesouro Direto mudam: sempre conferir a tabela da B3.
- Prêmio/desconto de título no mercado secundário exige série com data; usar pesquisa web.
- Regras de isenção e limites passam por alteração a cada mudança de lei — reconferir a cada
  ano-calendário.