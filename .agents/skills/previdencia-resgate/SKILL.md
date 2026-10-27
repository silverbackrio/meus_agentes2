---
name: previdencia-resgate
description: "Decida entre PGBL e VGBL, regime progressivo e regressivo, portabilidade, benefício e resgate de previdência complementar: prazo contado por aporte, alíquotas regressivas de 35% a 10%, dedução de 12% do PGBL, custo do fundo e cálculo do valor liquido recebido. Use quando pedirem sobre plano de previdência, aposentadoria privada, portar plano, resgatar VGBL ou comparar prazo de carreira."
metadata:
  category: investimentos
  classe_de_ativo: previdencia
  pais: brasil
---
# Previdência e Resgate

Decisões de previdência complementar resolvidas por conta: dedução, regime, prazo por aporte,
custo do plano e quanto chega líquido no resgate ou no benefício.

## Quando usar

- Escolher entre PGBL e VGBL, ou entre regime progressivo e regressivo.
- Simular resgate, portabilidade ou recebimento de benefício.
- Comparar planos previdenciários ou fundos de previdência.
- Responder "compensa esperar 10 anos?" ou "o que perco se trocar de plano?".

## Conhecimento

### 1. PGBL × VGBL

| | PGBL | VGBL |
|---|---|---|
| Quem pode | quem declara IR completo e tem renda tributável | qualquer pessoa |
| Dedução na declaração | até **12% da renda bruta tributável**, limitada ao teto do INSS | não deduz |
| Base do IR no resgate | **valor total** recebido | **somente os rendimentos** |
| Onde declarar | Bens e Direitos **e** Deduções | Bens e Direitos |
| Indicado quando | alíquota marginal na dedução ≥ alíquota no resgate | já deduz em outra fonte ou alíquota no resgate menor |

**Regra de ouro:** o benefício do PGBL só existe se a alíquota hoje for maior que a alíquota no
resgate. Cobre com a conta dos dois cenários, com a mesma data-base.

### 2. Regimes

- **Progressivo:** tabelas anuais de IR, com parcela a deduzir.
- **Regressivo** (Lei 11.053/2004), prazo contado por aporte e conforme a regra legal:

| Prazo de acumulação | Alíquota |
|---|---|
| Até 2 anos | 35% |
| Acima de 2 até 4 anos | 30% |
| Acima de 4 até 6 anos | 25% |
| Acima de 6 até 8 anos | 20% |
| Acima de 8 até 10 anos | 15% |
| Acima de 10 anos | 10% |

- **Escolha:** pela Lei 14.803/2024, em regra a opção pelo regime pode ser feita até a obtenção do
  benefício ou a solicitação do primeiro resgate e é **irretratável**.
- **Portabilidade:** entre planos do mesmo tipo; **não se portou de PGBL para VGBL** nem o
  contrário, e o tempo de acumulação do regime regressivo é computado no plano receptor.
- **Não confunda:** portabilidade (troca de plano, sem imposto) × resgate (imposto) × benefício
  (renda ou valor único, com as regras do regulamento).

### 3. Custo do plano

```
custo total = taxa de administração do plano
            + taxa de carregamento (se houver)
            + taxa de administração do fundo escolhido
            + spread da tabela de remuneração da Fipe
```
- Compare a **TIR líquida** dos fundos previdenciários do mesmo perfil de risco, não o retorno
  bruto.
- Para títulos públicos na previdência, some o prêmio/desconto da tabela de remuneração.

### 4. Fórmulas de decisão

```
PGBL líquido = VI × (1 + aliq_resgate) − (deducao × aliq_marginal_hoje)
VGBL líquido = VI + rendimento × (1 − aliq_resgate)      [sem dedução hoje]

alíquota efetiva no regressivo = imposto / valor recebido
benefício de esperar = (1 − aliq_t1) − (1 − aliq_t2) sobre a parcela tributável
```
- O imposto do regime regressivo incide sobre o **valor recebido** (principal + rendimento),
  enquanto o do progressivo incide sobre o valor total do benefício conforme a tabela — confirme
  a base aplicável ao caso antes de calcular.
- Simule ao menos três cenários: (a) resgatar hoje, (b) esperar o próximo degrau de prazo,
  (c) portar para plano com custo menor.

### 5. Perguntas que decidem o caso

1. Quanto renda bruta tributável existe e qual a alíquota marginal?
2. Já existe dedução de 12% em outra fonte?
3. Qual o horizonte até o benefício, por aporte?
4. Qual a alíquota provável no resgate, e o regime já foi escolhido?
5. Qual o custo total e a TIR líquida do plano?
6. Há regra de carência, resgate parcial ou carência de portabilidade no regulamento?

### 6. Erros que este guia evita

- Recomendar PGBL sem conferir a alíquota marginal e o limite de 12%.
- Contar o prazo do regressivo a partir do contrato e não por aporte.
- Dizer que se alcança 10% "em 10 anos": o degrau de 10% é **acima de 10 anos**.
- Tratar portabilidade como troca livre entre PGBL e VGBL.
- Ignorar custo e comparar só retorno.
- Decidir pelo usuário: mostre cenários com valores e deixe a escolha a ele.

## Instruções

1. Reúna: espécie (PGBL/VGBL), regime, aportes e datas, valor presente, prazo até o benefício,
   alíquota marginal atual e custo do plano.
2. Calcule os cenários lado a lado, com fórmula, entradas e resultado líquido final.
3. Cite a norma (Lei 11.053/2004, Lei 14.803/2024, RIR) e a data de vigência em cada regra.
4. Se o plano tiver carência, resgate parcial ou limite, diga que é regra do **regulamento** e
   precisa ser lido no contrato.
5. Feche com o que falta para decidir e com o aviso de que casos concretos passam por contador.

## Fontes oficiais

- SUSEP — PGBL e VGBL: https://www.gov.br/susep/pt-br/assuntos/meu-futuro-seguro/seguros-previdencia-e-capitalizacao/providencia-complementar-aberta/pgbl-vgbl
- Planalto — Lei 11.053/2004: https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l11053.htm
- Planalto — Lei 14.803/2024: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l14803.htm
- Receita Federal — Tributação de 2026: https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026