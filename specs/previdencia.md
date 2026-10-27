---
status: ativa
atualizada_em: 2026-10-27
---
# Spec: Previdência Complementar

## Escopo

**Dentro:** PGBL e VGBL, regimes tributários, escolha e portabilidade, benefício e resgate,
custo de planos e simulação de valor líquido.
**Fora:** INSS e aposentadoria pública, planejamento sucessório, contratação de plano em nome de
terceiros, tributação de investimentos fora da previdência (ver `fundos-e-fiis.md` e
`dominio-e-fontes.md`).

## Modelo

| Entidade | Campos obrigatórios |
|---|---|
| `Plano` | espécie (PGBL/VGBL), entidade, fundo, taxa de admin., carregamento, carência, regulamento e data |
| `Aporte` | data, valor, prazo acumulado até a data-base (por aporte) |
| `Regime` | progressivo ou regressivo, data da opção, base de cálculo |
| `Portabilidade` | origem, destino, espécies, tempo de acumulação transferido, data |
| `Cenario` | valor recebido bruto, imposto, líquido, alíquota efetiva, data-base |

## Regras

**R1.** PGBL: dedução de até **12% da renda bruta tributável**, limitada ao teto do INSS, apenas
quem declara em modelo completo; imposto no resgate sobre o **valor total** recebido.

**R2.** VGBL: sem dedução; imposto incidindo somente sobre **rendimentos**.

**R3.** Regressivo (Lei 11.053/2004), prazo de acumulação por aporte: 35% até 2 anos; 30% acima
de 2 até 4; 25% acima de 4 até 6; 20% acima de 6 até 8; 15% acima de 8 até 10; **10% apenas
acima de 10 anos**. *Vigente em 2026.*

**R4.** Escolha do regime: pela Lei 14.803/2024, em regra até a obtenção do benefício ou a
solicitação do primeiro resgate, **irretratável**; a lei também trata de retorno ao regime
anterior em situações específicas — não generalizar.

**R5.** Portabilidade só entre planos compatíveis; **não** se portou entre PGBL e VGBL. O tempo de
acumulação do regime regressivo é computado no plano receptor (Lei 11.053/2004).

**R6.** Portabilidade ≠ resgate ≠ benefício: cada um tem consequência tributária e regra própria
de regulamento.

**R7.** Benefício e resgate seguem o **regulamento** do plano (carência, resgate parcial, teto,
renda vitalícia ou por prazo) — a spec não substitui a leitura do contrato.

**R8.** O ganho do PGBL só existe se a alíquota marginal na dedução for maior que a alíquota
efetiva no resgate; a comparação é obrigatória em ambos os sentidos.

**R9.** Custo comparado por **TIR líquida** do fundo previdenciário, incluindo tabela de
remuneração da Fipe quando houver.

**R10.** A Lei 15.270/2025 cria apuração anual de imposto mínimo para rendimentos acima de R$
600 mil no ano-calendário 2026 (0% a 10% entre R$ 600 mil e R$ 1,2 milhão); **não** é 10% fixo
sobre resgate de previdência — citar apenas como interação, com a norma.

## Cálculos obrigatórios

```
PGBL líquido   = VI × (1 − alíquota_resgate) + (dedução × alíquota_marginal_hoje)
VGBL líquido   = VI + rendimento × (1 − alíquota_resgate)
alíquota efetiva = imposto_total / valor_recebido
ganho de esperar = valor_liquido(próximo_degrau) − valor_liquido(hoje)
```
Cada fórmula sai com prazo por aporte, alíquota, data-base e o resultado em reais.

## Critérios de aceite

- [ ] Espécie, regime e datas de aporte levantados antes de calcular.
- [ ] Comparação PGBL × VGBL com dedução tributada nos dois sentidos.
- [ ] Cenários lado a lado (resgatar / esperar degrau / portar), com líquido final.
- [ ] Custo total e TIR líquida incluídos.
- [ ] Norma e vigência citadas (Lei 11.053/2004, Lei 14.803/2024, RIR).
- [ ] Regras de contrato marcadas como dependentes do regulamento.
- [ ] Aviso de que apuração concreta passa por contador (`compliance-e-avisos.md`).

## Lacunas

- Alíquota provável no resgate é estimativa: depende da renda futura e das tabelas da época.
- Regras de benefício variam por entidade (renda, teto, portabilidade interna).
- Alterações de reforma tributária sobre a base de previdência exigem reconferência anual.