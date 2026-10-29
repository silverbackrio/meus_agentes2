---
atualizado_em: 2026-10-27
---
# CONTEXT — escopo, objetivo e estado atual

Registro vivo da entrevista de escopo (`grill-with-docs`). Data em cada mudança.

## Objetivo principal

Ferramenta de **análise e apoio à decisão de investimentos para pessoa física no Brasil**, cobrindo
todas as classes de ativo (renda fixa, ações, fundos/FIIs, previdência, câmbio, carteira): coletar
dado oficial **e histórico** uma vez, guardar em banco local, e calcular/explicar cenários a partir
daí — sem recomendação personalizada.

**Confirmado em entrevista (2026-10-27): são três objetivos, não um.** Todos entram no produto:

1. **Decidir aporte** — iniciar, aumentar ou reduzir em um ativo (novo ou possuído), com dado
   datado e cenário montado; a decisão é do usuário.
2. **Monitorar a carteira existente** — o que mudou, alocação vs. política com faixas, custo
   médio, o que saiu do trilho.
3. **Aprender** — dossiês explicados, fórmula mostrada, comparativos pedagógicos.

**Fora:** virar produto para outros investidores — sem usuários finais, sem cobrança, sem suporte
(27/10/2026).

## Quem usa

| Personagem | O que faz hoje | Status |
|---|---|---|
| Investidor PF (dono do projeto) | Decide aportes com base em números e fontes datadas | assumido, a confirmar em entrevista |

## Escopo da v1 (decidido em 27/10/2026)

**Dentro:**
- Banco histórico de séries (`market_data`), com ingestão via CLI e export CSV.
- Carteira local: objetivo, perfil, política com faixas, posições, operações — **sem login**.
- Análise: métricas, cenários, dossiês datados, comparativo em base líquida.
- Frontend React + Vite servindo 7 telas (painel, dados, carteira, análise, dossiê, comparar, config).

**Fora da v1:**
- Multiusuário e autenticação (o campo `owner` já existe no schema para a v2).
- Recomendação de compra/venda/alocação obrigatória (proibido por `compliance-e-avisos.md`).
- Derivativos como alavancagem, cripto, gestão contratada.

## Modelo técnico atual

| Camada | Decisão | Origem |
|---|---|---|
| Backend | Python 3.14 (faixa `>=3.12,<3.15`), Django 5.2 LTS + DRF, `uv`, pytest | `specs/ambiente-e-versoes.md`, `specs/aplicacao.md` |
| Banco | SQLite agora → Postgres depois (schema portável, `Decimal`, ISO-8601) | `specs/aplicacao.md` R5 |
| Frontend | React + Vite, sem cálculo de domínio no JS | `specs/aplicacao.md` R4 |
| Dados | APIs oficiais com licença registrada, ingestão só por CLI, fato passado imutável | `specs/fontes-de-dados.md` |
| Produção | Ubuntu 26.04 remoto (dev em Windows 10), nginx + cloudflared + gunicorn | `.agents/skills/infra-linux` |
| Qualidade | Portátil/modular/de dependência mínima (P1–P5), testes dourados por cálculo, gates `revisor-de-codigo` e `revisor-de-compliance` | `specs/aplicacao.md` |

## Estrutura de conhecimento existente

13 agentes, 11 skills, 10 specs (`specs/README.md` é o índice). `specs/aplicacao.md` manda na
estrutura do produto; a spec da classe manda no cálculo; `specs/fontes-de-dados.md` manda na
origem do dado.

## Definição de pronto da v1 (rodada 2 — 27/10/2026)

A v1 **termina** quando responder, para um ativo que você escolher, a pergunta
**"entro, aumento ou reduzo o aporte?"** com:

- dado coletado e guardado no banco local (histórico, não só o dia), com fonte e data-base;
- o que mudou desde a última análise, se a tese original ainda se sustenta;
- preço vs. seu custo médio, se já é posse;
- risco, custo, liquidez e tributação mostrados em base líquida;
- o cenário montado — e **sem** recomendação de compra ou venda (limite de `compliance-e-avisos.md`).

Monitorar carteira e aprender entram **depois**, sobre o que já existir. Enquanto isso, nenhum
trabalho de tela desses dois objetivos é v1.

## Cenário real 0 — BBAS3 (registrado em 27/10/2026)

| Campo | Registro |
|---|---|
| Ativo | BBAS3 (Banco do Brasil), ações |
| Posição | **já era acionista** — intenção era **aportar na queda** (baixar o preço médio), não entrada nova |
| Dúvida cruel | "vale baixar meu preço médio agora, ou o risco político/fiscal aumentou a ponto de eu jogar dinheiro bom atrás de dinheiro ruim?" |
| Momento | logo após a volatilidade recente do mercado financeiro |
| O que faltou | (1) visibilidade de **risco político e fiscal**; (2) como os **price targets dos grandes bancos** mudaram (vi rebaixamento do Citi no Google, o app não mostrava); (3) **termômetro de sentimento** e consolidado de recomendações de analistas atualizado |
| Desfecho | não operou — **decisão travada** por insegurança |
| Leitura do entrevistador | a tela de decisão precisa entregar essas três coisas com fonte e data, ou o produto não destrava o caso real |

O que isso impõe à v1: além de preço/histórico, a "resposta" precisa carregar **consenso e
revisões de analistas**, **indicador de sentimento** e **monitor fiscal/político datado** — todos
com fonte, licença e data-base. Ver pendências 4, 5 e 6.

### O quadro que destravaria (definido pelo usuário em 27/10/2026)

1. **Termômetro de consenso**: X% recomenda Compra / Y% Neutro / Z% Venda.
2. **Preço-alvo médio** do mercado com o **upside** em relação ao preço de tela atual.
3. **Fonte**: consenso de grandes bancos e corretoras (o usuário citou **Investing.com e
   TradingView** como exemplos do que espera — não são fontes confirmadas, ver pendência 4).
4. **Data obrigatória D-0** no bloco inteiro.
5. **Limite de compliance:** o app dá o *norte do mercado*; a decisão de aceitar risco político
   e macro é **100% do usuário** — nada de "compre"/"venda" na tela, coerente com
   `compliance-e-avisos.md`.
6. **Regra de staleness (decidida em 27/10/2026):** o bloco mostra **sempre a data do dado**
   (`consenso de 10/10 · coletado em 27/10`) e ganha um **selo "desatualizado"** quando a
   data-base passar do limite (limite a definir — exemplo chutado: 10 dias úteis). Nunca
   ocultar o bloco e nunca deixar dado velho parecer fresco.

### O que o usuário pediu em 29/10/2026 (confirmação da pergunta 2 do grill)

**Querido terminar:** o **termômetro é de mercado** — o consolidado da concorrência de grandes
bancos, corretoras e plataformas como Investing/TradingView — e o app mostra ele para o usuário não
ter que sair do app e buscar no Google.

**Diferencial que o usuário quer em cima do consenso:** além de X% compra / Y% neutro / Z% venda
e do preço-alvo médio, a tela tem **alerta visual de revisão recente de price target**
("revisado nos últimos X dias"). Exemplo: "Citi revisou o preço-alvo de BBAS3 para baixo nas
últimas 48h". O usuário tem essa informação na hora, entende o motivo da queda e decide se concorda
com o analista ou aproveita o barato — sem que o app tome a posição por ele.

### Bloco 1 da v1 — Gestão de Posição (decidido em 27/10/2026)

O usuário é **acionista** e quer **aportar na queda**. A v1 não começa com tela de descoberta de
ativo: começa em **gestão de posição + preço médio + projeção de renda passiva**.

1. **Posição atualizada** — preço médio vs. preço de tela, P&L acumulado.
2. **Simulador de preço médio (o diferencial)** — digito a quantidade pretendida: novo preço
   médio e **yield on cost projetado** calculados na hora.
3. **Consenso de mercado** — termômetro (compra / neutro / venda) + preço-alvo médio + alerta
   de revisão recente do price target.
4. **Data sem sair do app, em duas camadas:** a **data da carga** (o app puxou a foto mais
   recente do banco) e a **cotação em tempo real** na tela. Nenhum número pode ter frescura que
   o usuário precise checar fora do app.
5. **Fontes nomeadas pelo usuário** (exemplos, não confirmadas): consenso estilo
   **Investing/TradingView** e **histórico do RI do próprio Banco do Brasil** para múltiplos
   (P/L, P/VP) dos últimos 5 anos.
6. **Limite de compliance** — o app dá suporte matemático e sentimento; aceitar risco de
   governança de estatal e risco macro de inadimplência é **100% do usuário**.

Consequência: o primeiro cálculo a construir é **preço médio + simulador + yield on cost**, não
valuation genérico. Ver pendências 4, 9, 10 e 11.

### Recorte da primeira entrega (decidido em 27/10/2026)

**BBAS3 + Ibovespa.** Uma série de preço por papel, o índice para contexto, proventos de BBAS3 e
e o consenso do papel — o suficiente para reproduzir de ponta a ponta aquele travamento:
posição, simulador de aporte, consenso datado com alerta de revisão e o "foi o mercado?"
Alto fora disso entra depois.

### Aceite da primeira entrega (rodada 8 — decidido em 27/10/2026)

O usuário **reproduz o caso BBAS3 e documenta a decisão**: abre o painel, vê posição (preço médio
vs. preço de tela, P&L), digita a quantidade no simulador (novo preço médio + yield on cost),
lê o consenso datado com o alerta de revisão, confere o "foi o mercado?" com o Ibovespa — tudo
**sem sair do app para checar dado** — e anota por que decidiu aportar, reduzir ou não operar.
Se ele precisou sair do app para validar alguma informação, o aceite **falhou**.

### Regra do bloco de contexto (benchmark) — confirmada em 29/10/2026 (pergunta 4 do grill)

**Benchmark único na v1:** Ibovespa (descartados commodities, dólar e juros para manter a entrega
focada).

**Grade de janelas de tempo (retroativas a D-0):** a tela mostra lado a lado a variação percentual
de BBAS3 vs. Ibovespa em seis janelas fixas — **5D e 30D (curto prazo/pânico)**, **6M e 1A
(médio prazo/tendência)**, **2A e 5A (longo prazo/sólidez da tese)**.

**Regra de implementação:** a lógica do backend calcula essas seis janelas com datas dinâmicas
retroativas a D-0, sem armazenar horizonte fixo no banco — o cálculo usa o preço do papel e do
índice nas datas corretas ao longo desse período.

## Regra de fontes (rodada 6 — decidida em 27/10/2026)

**Só camada gratuita com cadastro.** O usuário cria as contas e coloca as chaves no `.env`.
Onde não houver fonte gratuita, a tela mostra **"não disponível"** declarado — nunca estimativa,
sem tentar puxar de fonte bloqueada ou de licença desconhecida. Vários itens das pendências 4, 9,
10 e 11 seguem essa regra: pesquisar só o que cabe em camada gratuita com chave.

## Rodada 7 — Segurança (decidida em 27/10/2026)

O dado exposto passou a ser **preço médio, P&L e intenção de aporte do usuário**. Decisão:
**bloqueio de acesso desde a v1** — antes da primeira tela, atrás de um mecanismo de autenticação
leve (Cloudflare Access, senha no túnel ou basic auth — mecanismo a escolher, ver pendência 12).
Sem multiusuário ainda (decisão 8 do `ARCHITECTURE_DECISIONS.md`), mas **sem app aberto**.

## Rodada 7b — Decisão de TI para rodar localmente (confirmada em 29/10/2026, pergunta 7 do grill)

O usuário delegou a **decisão técnica de organização** para rodar esse projeto em um servidor
doméstico.

**Decisão da v1 (própria, por mim):**

- Um **único repositório Git** contendo:
  - o frontend (`frontend/` com React + Vite),
  - o backend (`backend/` ou pasta `investimentos/` com Django),
  - as **automações/agentes** como scripts Python reutilizáveis (não como microserviços separados,
    pelo menos na v1).
- Nada de Docker na v1 — **rodar localmente como módulos do próprio projeto**, num ambiente
  Python virtual padrão.
- Backend e as competências dos agentes rodam na mesma máquina, sem deploy externo, sem dependência
  de serviços na nuvem para funcionar offline/local.

**Princípio:** na v1, simplicidade acima de tudo. O foco é que backend + scripts de agente rodem
com `python` e `pip` na máquina local, e qualquer coisa que precise de container ou serviço
independente fica para depois — quando diera de necessidade real.

**O que isso garante:**
- Código organizado, mas sem sobrecarga de infraestrutura.
- Cada script de agente é modular e pode ser evoluido para serviço depois sem reescrever o projeto.
- Offline/local é possível desde o início.

## Rodada 9 — Confirmado em 29/10/2026 (pergunta 2 do grill)

- **Consenso que entra no app:** de **mercado**, não do próprio usuário. Termômetro público
  (distribuição compra/neutro/venda e preço-alvo médio) + preço-alvo médio com upside vs. preço
  de tela.
- **Alerta de revisão de price target:** a tela mostra, com destaque, quem revisou o alvo (ex.
Citi) e para onde, dentro de uma janela de dias a definir (ex.: "nas últimas 48h").
- **Limite de decisão:** o que o app mostra é o norte do mercado; concordar ou não com a revisão,
e aí aportar, reduzir ou não operar, continua **100% do usuário** (`compliance-e-avisos.md`).

### Regra do bloco de contexto (benchmark) — confirmada em 29/10/2026 (pergunta 4 do grill)

**Benchmark único na v1:** Ibovespa (descartados commodities, dólar e juros para manter a entrega
focada).

**Grade de janelas de tempo (retroativas a D-0):** a tela mostra lado a lado a variação percentual
de BBAS3 vs. Ibovespa em seis janelas fixas — **5D e 30D (curto prazo/pânico)**, **6M e 1A
(médio prazo/tendência)**, **2A e 5A (longo prazo/sólidez da tese)**.

**Regra de implementação:** a lógica do backend calcula essas seis janelas com datas dinâmicas
retroativas a D-0, sem armazenar horizonte fixo no banco — o cálculo usa o preço do papel e do
índice nas datas corretas ao longo desse período.

## Rodada 11 — Regras definitivas do simulador (confirmadas em 29/10/2026, perguntas 6 e complementos do grill)

**Entrada do simulador:** o backend recebe o trio completo — **quantidade simulada**, **preço de
tela atual** e **provento anual projetado por ação (R$/ação)** — e o caso de uso também aceita
**JCP anual projetado por ação (R$/ação)** como entrada separada (agora zero) para a fórmula já estar
pronta quando a fonte real ficar disponível.

**Cálculo (backend, função pura):**
1. **Média ponderada real da posição atual:** o “custo médio atual” vem da soma de todas as
   operações salvas no banco para aquele ativo, não só da última operação.
2. **Novo preço médio:** ((quantidade atual × custo médio atual) + (quantidade simulada × preço de
   tela)) ÷ (quantidade atual + quantidade simulada).
3. **Custo total do aporte:** quantidade simulada × preço de tela.
4. **Yield on cost projetado:** (provento anual + JCP anual) ÷ novo preço médio, com premissa
   datada e claro de que é projeção, não garantia.
5. **Projeção de renda passiva:** provento anual + JCP anual aplicado ao novo preço médio, como
   cenário — não previsão (compliance-e-avisos.md).

**Resumo exibido na linha de apoio (exatamente como você definiu):**
- Abaixo do novo preço médio: *“Preço médio cai X% · Custo total do aporte = R$ Y”*
  (se o preço médio cair, o delta fica verde — para o comprador é positivo).
- Abaixo do novo yield on cost: *“+X% no YoC · +R$ Y de renda passiva projetada/ano”*
  (verde para sinalizar ganho de renda passiva).

**Restrição de ação:** o simulador é puramente visual/matemático — não executa ordens, não grava
 posições no banco. O único botão no escopo da v1 é **“Resetar Simulação”** (limpa campo e volta
 para zero). Botões como “confirmar aporte” ou “abrir detalhes” ficam para depois.

**Validação do input (regras explícitas + mensagens amigáveis):**
- Só aceita números inteiros positivos (não existe fração de cota no mercado de ações).
- Se 0: *“Digite uma quantidade maior que zero para simular.”* — limpa o resultado e não calcula.
- Se negativo: *“A quantidade de ações para o aporte deve ser positiva.”*
- Se letras ou decimal: o campo de texto rejeita a digitação ou exibe *“Insira apenas números inteiros.”*
  para não quebrar o backend com erro inesperado.

**Comportamento híbrido Web/Mobile (mesmo backend, diferente exibição):**
- **Web/desktop:** formulário completo e visível — quantidade + preço de tela + campo explícito de
  “provento anual projetado por ação”, com padrão de teste R$ 4,50. O usuário vê tudo aberto e pode
  auditar a matemática.
- **Mobile:** campo de provento fica oculto; o app injeta o provento automaticamente no fluxo, e o
  usuário só digita a quantidade. A interface fica mais limpa.
- **Backlog de automação:** hoje o R$ 4,50 é premissa de teste; quando a API de proventos estiver
  pronta, o campo vira preenchido automaticamente (na web pode ser editável se o usuário quiser
  alterar; no mobile roda totalmente oculto e automático).

**Principle:** o backend não sabe e não depende de como o front exibe — ele só calcula com o trio
 completo e o JCP opcional. Qualquer tela que evoluir depois usa o mesmo contrato.

### Regra do bloco de contexto (benchmark) — confirmada em 29/10/2026 (pergunta 4 do grill)

**Benchmark único na v1:** Ibovespa (descartados commodities, dólar e juros para manter a entrega
focada).

**Grade de janelas de tempo (retroativas a D-0):** a tela mostra lado a lado a variação percentual
de BBAS3 vs. Ibovespa em seis janelas fixas — **5D e 30D (curto prazo/pânico)**, **6M e 1A
(médio prazo/tendência)**, **2A e 5A (longo prazo/sólidez da tese)**.

**Regra de implementação:** a lógica do backend calcula essas seis janelas com datas dinâmicas
retroativas a D-0, sem armazenar horizonte fixo no banco — o cálculo usa o preço do papel e do
índice nas datas corretas ao longo desse período.

## Pendências (impedem o início do código correspondente)

| # | Pendência | Bloqueia | Status |
|---|---|---|---|
| 1 | ~~Personagem/usuário real~~ | decisões de UX da v1 | **resolvida (27/10/2026): uso individual do usuário, PF com posição em BBAS3** — reabrir se aparecer outra pessoa usando |
| 2 | ~~Ordem de prioridade entre os três objetivos~~ | ordem de implementação e definição de pronto | **resolvida (27/10/2026): norte = decidir aporte** |
| 3 | ~~Ativos-chave do primeiro dossiê~~ | primeira série a ingerir | **resolvida (27/10/2026): recorte da v1 = BBAS3 + Ibovespa** (o índice responde "foi o papel ou foi o mercado?") |
| 4 | Fonte viável, licenciada e datável para **consenso/price targets de analistas** e **sentimento** — usuário citou Investing.com e TradingView (exemplos, **não confirmados**); spec `fontes-de-dados.md` não cobre isso | tela de decisão (caso BBAS3) | aberta (27/10/2026), **com nova exigência (29/10/2026): também precisa cobrir alerta de revisão de price target recente com nome da casa** — precisa de pesquisa antes de virar spec |
| 5 | ~~BBAS3 é posse ou entrada?~~ | quais cálculos a tela de decisão precisa ter | **resolvida (27/10/2026): é posse, intenção de aportar na queda** |
| 6 | Dado de risco fiscal/político: qual série ou indicador datado substitui "clima" por número (ex.: resultado primário, dívida/PIB, Focus, CDS) | tela de decisão | aberta (27/10/2026) |
| 7 | Vue: confirmar React ou trocar a spec | scaffold do frontend | React definido em 27/10/2026, reabrir só com motivo |
| 8 | ~~Staleness do consenso~~ | regra de exibição da tela de decisão | **parcialmente resolvida (27/10/2026): data do dado sempre visível + selo "desatualizado" após o limite; resta definir o número do limite e o texto do selo** — reaberta em 29/10/2026 por causa do threshold da janela de revisão (ex.: 48h) |
| 9 | **Cotação em tempo real de ação da B3** — spec de fontes diz que a página da B3 proíbe coleta automatizada; confirmar alternativa licenciada (brapi? outra?) e latência | bloco "posição atualizada" e simulador | aberta (27/10/2026) — precisa de pesquisa |
| 10 | **Histórico de proventos (dividendos/JCP) de BBAS3** para o yield on cost projetado | simulador de preço médio + projeção de renda passiva | aberta (27/10/2026) — fonte não definida (RI, B3, CVM, brapi?) |
| 11 | **Múltiplos históricos P/L e P/VP (5 anos)** a partir do RI do banco, com fonte e licença | painel de valuation | aberta (27/10/2026) — RI é dado institucional, checar licença e frequência |
| 12 | **Mecanismo do bloqueio de acesso** (já é decisão: vai ter) | primeiro deploy em produção | aberta (27/10/2026) — decidir com `infra-linux` (A9) |

## Regra do Simulador (confirmada em 29/10/2026, perguntas 5-8 do grill)

### Entrada do simulador
O backend recebe o trio completo: **quantidade simulada**, **preço de tela atual** e **provento anual projetado por ação (R$/ação)**. O caso de uso também aceita **JCP anual projetado por ação (R$/ação)** como entrada separada (agora zero) para a fórmula já estar pronta quando a fonte real ficar disponível.

### Cálculo (backend, função pura)
1. **Média ponderada real da posição atual:** o "custo médio atual" vem da soma de todas as operações salvas no banco para aquele ativo, não só da última operação.
2. **Novo preço médio:** ((quantidade atual × custo médio atual) + (quantidade simulada × preço de tela)) ÷ (quantidade atual + quantidade simulada).
3. **Custo total do aporte:** quantidade simulada × preço de tela.
4. **Yield on cost projetado:** (provento anual + JCP anual) ÷ novo preço médio, com premissa datada e claro de que é projeção, não garantia.
5. **Projeção de renda passiva:** provento anual + JCP anual aplicado ao novo preço médio, como cenário — não previsão (compliance-e-avisos.md).

### Resumo exibido na linha de apoio (exatamente como definido)
- Abaixo do novo preço médio: "Preço médio cai X% · Custo total do aporte = R$"
  (se o preço médio cair, o delta fica verde — para o comprador é positivo).
- Abaixo do novo yield on cost: "+X% no YoC · +R$ Y de renda passiva projetada/ano"
  (verde para sinalizar ganho de renda passiva).

### Restrição de ação
O simulador é puramente visual/matemático — não executa ordens, não grava posições no banco. O único botão no escopo da v1 é "Resetar Simulação" (limpa campo e volta para zero). Botões como "confirmar aporte" ou "abrir detalhes" ficam para depois.

### Validação do input (regras explícitas + mensagens amigáveis)
- Só aceita números inteiros positivos (não existe fração de cota no mercado de ações).
- Se 0: "Digite uma quantidade maior que zero para simular." — limpa o resultado e não calcula.
- Se negativo: "A quantidade de ações para o aporte deve ser positiva."
- Se letras ou decimal: o campo de texto rejeita a digitação ou exibe "Insira apenas números inteiros." para não quebrar o backend com erro inesperado.

### Comportamento híbrido Web/Mobile (mesmo backend, diferente exibição)
- **Web/desktop:** formulário completo e visível — quantidade + preço de tela + campo explícito de "provento anual projetado por ação", com padrão de teste R$ 4,50. O usuário vê tudo aberto e pode auditar a matemática.
- **Mobile:** campo de provento fica oculto; o app injeta o provento automaticamente no fluxo, e o usuário só digita a quantidade. A interface fica mais limpa.
- **Backlog de automação:** hoje o R$ 4,50 é premissa de teste; quando a API de proventos estiver pronta, o campo vira preenchido automaticamente (na web pode ser editável se o usuário quiser alterar; no mobile roda totalmente oculto e automático).

**Princípio:** o backend não sabe e não depende de como o front exibe — ele só calcula com o trio completo e o JCP opcional. Qualquer tela que evoluir depois usa o mesmo contrato.
