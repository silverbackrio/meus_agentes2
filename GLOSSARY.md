---
atualizado_em: 2026-10-27
---
# GLOSSARY — termos e regras de negócio

Estado da entrevista de escopo (`grill-with-docs`). Termo já coberto por spec está marcado
**decidido (spec)** e não precisa ser entrevistado de novo; o que está aqui como **pendente**
impede o início do código correspondente.

## Termos de domínio

| Termo | Definição | Regra / consequência | Exemplo | Status |
|---|---|---|---|---|
| data-base | Data na qual um número é válido | Sem data-base não há número válido (`dominio-e-fontes.md`) | PTAX de 24/10/2026 | decidido (spec) |
| aporte | Aplicação de dinheiro em um ativo | A decisão de iniciar/aumentar/reduzir é do usuário; o projeto nunca recomenda (`compliance-e-avisos.md`) | aportar R$ 1.000/mês | decidido (spec) |
| custo médio | Preço médio das posições de um ativo | Calculado no backend, com data-base e unidade (`aplicacao.md` R4) | PETR4 c.m. R$ 36,12 em 27/10/2026 | decidido (spec) |
| simulador de preço médio | Projeção: se eu comprar X títulos ao preço P, qual fica meu novo preço médio | **O cálculo fica no backend** (função pura em `analise/calculos.py`, exposta por `POST /analise/simular/`) — o R4 de `aplicacao.md` proíbe o JS de calcular; ver decisão A6 | c.m. atual R$ 30,00 com 100 títulos + 100 a R$ 24,00 → novo c.m. R$ 27,00 | decidido (spec + código 28/10/2026) |
| yield on cost (YoC) | Renda passiva projetada ÷ preço médio pago | Sempre com premissa datada: proventos dos últimos 12 meses ÷ preço médio, e dizer que é **projeção**, não garantia | R$ 2,10/ação ÷ R$ 27,60 = 7,6% | definido (entrevista 27/10/2026), fonte de proventos pendente |
| projeção de renda passiva | Quanto a carteira renderia se o cenário de proventos se repetir | Cenário, não previsão (`compliance-e-avisos.md`); datar a premissa | 12 meses futuros | definido (entrevista 27/10/2026) |
| múltiplos (P/L, P/VP) | Preço ÷ lucro por ação e preço ÷ valor patrimonial por ação | Comparar sempre com histórico do **mesmo ativo** (5 anos) e com data-base; P/L negativo não vira "barato" | P/L 4,2x em 27/10/2026 | definido (entrevista 27/10/2026), fonte de RI pendente |
| data da carga × tempo real | Frescura em dois níveis: quando o **banco local** foi atualizado vs. quando a **cotação** foi puxada | Dois relógios distintos na tela; nenhum número pode exigir que o usuário cheque fora do app | "banco: 27/10 09:02 · cotação: 15s" | definido (entrevista 27/10/2026) |
| série | Sequência de observações de um mesmo indicador | `UNIQUE(source, código)`; fato passado é imutável (`fontes-de-dados.md` R1) | PTAX USD/BRL diária | decidido (spec) |
| observação | Valor de uma série em uma data | Idempotência por `(série, data)`; rebusca igual não duplica | 2016-09-09 → 3,2638 BRL/USD (PTAX venda, BCB, consultado em 28/10/2026) | decidido (spec); valor conferido na API Olinda do BCB |
| dossiê | Relatório datado de uma coleta/analise de um ativo | Guardado em `dados/<classe>/<ativo>/<AAAA-MM-DD>.md`, reutilizado sem rede | dossiê PETR4 2026-10-27 | decidido (spec) |
| política de carteira | Faixa-alvo por classe com regra de rebalanceamento | Nunca percentual obrigatório nem ordem de compra (`carteira-e-risco.md` R12) | ações 40–55% do patrimônio | decidido (spec) |
| gap | Intervalo faltante entre a maior data guardada e a data desejada | Só se busca o gap; nunca o período já coberto (`fontes-de-dados.md` R4) | 2026-10-25 → 2026-10-27 | decidido (spec) |
| consenso de recomendação | Distribuição dos analistas sobre um papel: % compra / % neutro / % venda | É **dado de mercado**, não recomendação do app; exige fonte e data-base (`aplicacao.md` R2) | 60% compra / 30% neutro / 10% venda | definido (entrevista 27/10/2026), fonte pendente |
| preço-alvo médio | Média dos alvos dos analistas sobre um papel | Sempre acompanhado do **upside** vs. preço atual e da data-base; alvo sozinho engana | alvo R$ 24,62 vs. preço R$ 22,10 = +11,4% | definido (entrevista 27/10/2026), fonte pendente |
| D-0 | Data-base do bloco exibido no dia | Data do **dado** sempre visível + selo "desatualizado" quando passar o limite; nunca ocultar bloco e nunca dado velho parecer fresco | "consenso de 10/10/2026 (coletado em 27/10)" | decidido (entrevista 27/10/2026) |

## Pendências de vocabulário

| Dúvida | Por que importa | Status |
|---|---|---|
| price target / alvo de analista | Definido como **preço-alvo médio** (linha acima); restou só a **fonte** e a licença | aberta (27/10/2026) — ver pendência 4 do CONTEXT.md |
| fonte de consenso (Investing.com / TradingView) | Citação do usuário como exemplo do que espera — **não confirmada** como API gratuita/licenciada | aberta (27/10/2026) — pesquisar antes de prometer |
| cotação em tempo real da B3 | Especificação do usuário exige cotação de tela em tempo real; a spec de fontes diz que a página da B3 proíbe coleta automatizada | aberta (27/10/2026) — ver pendência 9 do CONTEXT.md |
| proventos de BBAS3 (dividendos/JCP) | Base do yield on cost; fonte não definida (RI, B3, CVM, brapi?) | aberta (27/10/2026) — ver pendência 10 do CONTEXT.md |
| múltiplos de 5 anos (P/L, P/VP) | O usuário aponta o RI do próprio banco; checar licença, frequência e formato | aberta (27/10/2026) — ver pendência 11 do CONTEXT.md |
| termômetro de sentimento | Sentido exato: put/call da B3, Fear & Greed, volatilidade implícita? Precisa virar número com data, não "clima de mercado" | aberta (27/10/2026) |
| risco fiscal / político | Como o projeto transforma "clima" em série datada (resultado primário, dívida/PIB, Focus, CDS) sem virar opinião | aberta (27/10/2026) |
| tese de investimento | O que o usuário acredita do papel e que a análise deve testar — o caso BBAS3 precisaria de tese registrada para dizer "o que mudou" | aberta (27/10/2026) |

---

_Preenchido pelo `grill-with-docs` em 2026-10-27; próxima entrevista acrescenta linhas aqui._