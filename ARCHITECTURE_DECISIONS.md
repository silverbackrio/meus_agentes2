---
atualizado_em: 2026-10-27
---
# ARCHITECTURE_DECISIONS — decisões técnicas e trade-offs aceitos

Registro de decisões (`grill-with-docs`). Uma linha por decisão. Mudou o cenário → **não apague**:
marque a antiga como `superseded por #N` e crie a nova. Todas as decisões abaixo remetem à spec
que as torna oficiais.

| # | Decisão | Data | Contexto | Alternativas consideradas | Trade-off aceito | Consequência |
|---|---|---|---|---|---|---|
| 1 | Python 3.14 com faixa `>=3.12,<3.15` + Django 5.2 LTS | 2026-10-27 | Precisa rodar em Ubuntu 26.04 com suporte longo | Django 4.2/5.1 (EOL), Django 6.0/6.1 (ecossistema menos maduro) | Trocar de LTS quando 5.2 sair de suporte | `specs/ambiente-e-versoes.md` |
| 2 | SQLite agora, Postgres depois | 2026-10-27 | Sem servidor de banco no começo, zero configuração | Postgres desde o início (melhor concorrência) | Sem concorrência de escrita pesada na v1 | `specs/aplicacao.md`; schema sem amarra de SQLite (R5) |
| 3 | React + Vite no frontend | 2026-10-27 | Skill e agente `frontend-react-vite` já existem | Vue 3 (o pedido original mencionou "vue ou vite") | Reescrever skill e agente se a escolha mudar | `specs/aplicacao.md` (lacuna) — reabrir só com motivo |
| 4 | Três apps Django com dependência em uma direção | 2026-10-27 | `market_data` ← `carteira` ← `analise` | Um app só (monólito interno), ou app por espécie de ativo | Mais módulos para gerenciar | `specs/aplicacao.md`; import no sentido inverso é bug |
| 5 | Cálculo de domínio em função pura, sem Django | 2026-10-27 | Mesma fórmula precisa servir view, comando, teste e futura app | Cálculo dentro de view/serializer | Um pouco mais de camada de serviço | `specs/aplicacao.md` P3/R4 — o front nunca calcula |
| 6 | Ingestão só por CLI, nunca endpoint público | 2026-10-27 | Cota, licença e rastro em `fetch_log`; sem superfície de ataque | API de ingestão autenticada | Backfill manual na máquina remota | `specs/fontes-de-dados.md` R12/R5 |
| 7 | Append-only em `observations` com idempotência `(série, data)` | 2026-10-27 | Fato passado não muda; retrabalho é o inimigo | Upsert livre (sobrescreve divergência) | Divergência vira alerta e decisão humana | `specs/fontes-de-dados.md` R1/R2 |
| 8 | Sem login multiusuário na v1, campo `owner` no schema | 2026-10-27 | Entregar mais rápido; modelo já nasce multiusuário | Autenticação desde a v1 | Sem isolamento de usuário até a v2 | `specs/aplicacao.md` (lacuna). **Complementada pela decisão 12 no mesmo dia**: sem login, mas com bloqueio de acesso |
| 9 | Dinheiro em `Decimal`, datas ISO-8601, caminho relativo | 2026-10-27 | Portabilidade e exatidão (P2/P5) | `float` por conveniência | Um pouco mais de conversão na borda | `specs/aplicacao.md` R5 |
| 10 | Fronteira por módulo + dependência nova justificada (P1–P5, R13) | 2026-10-27 | Crescer sem virar bola de neve | Adotar biblioteca quando precisar | Mais disciplina no diff | `specs/aplicacao.md`; gate no `revisor-de-codigo` |
| 11 | Camada de dado: **só API gratuita com chave** | 2026-10-27 | Vários blocos da tela de decisão precisam de fonte (consenso, tempo real, proventos, múltiplos) | paga (mais cobertura) vs. manual (menos código) | Sem cobertura onde a fonte é paga; usuário digita ou aceita lacuna | `.env` com chaves; lacuna exibida como "não disponível", nunca estimativa (`fontes-de-dados.md` R11) — usuário confirmou em 27/10/2026 |
| 12 | **Bloqueio de acesso desde a v1** (sem multiusuário) | 2026-10-27 | Dado exposto passou a ser preço médio e P&L do usuário, atrás de túnel público | Cloudflare Access com e-mail vs. senha única no túnel vs. URL secreta | Autenticação de verdade fica para a v2 | Usuário confirmou em 27/10/2026; mecanismo exato ainda não escolhido (A9) |

## Pendente de decisão

| # | Questão | Alternativas na mesa | Status |
|---|---|---|---|
| A1 | Ordem da primeira entrega (dado primeiro vs. carteira primeiro) | seguir a ordem da `aplicacao.md` (passo 1–7) ou inverter | aberta (27/10/2026) |
| A2 | Primeira série a ingerir além do PTAX USD/BRL | Ibovespa, S&P 500, ouro, Selic — decidir pelo que você de fato decide hoje | aberta (27/10/2026) |
| A3 | Hospedagem da v1 | VPS própria (já prevista em `infra-linux`) vs. alternativa gerenciada | aberta (27/10/2026) |
| A4 | Como entregar consenso, preço-alvo médio e sentimento (caso BBAS3) | API com chave vs. coleta de notícias vs. entrada manual do usuário no app | aberta (27/10/2026) — usuário citou Investing.com e TradingView como desejados (**não confirmados**); precisa de pesquisa de fontes (pendência 4 do CONTEXT.md) antes de virar spec. Requisito do usuário: bloco datado **D-0** e o app só mostra o norte — a decisão é 100% dele |
| A5 | Risco fiscal/político como série datada | série oficial (BCB, Tesouro/STN, CVM) vs. proxy de mercado (CDS, câmbio) vs. mistura com regra de composição | aberta (27/10/2026) |
| A6 | Onde calcula o simulador de preço médio / YoC | endpoint do backend (respeita `aplicacao.md` R4, custa um round-trip) vs. regra pura no front (instantâneo, **quebra R4** — só mudando a spec) | aberta (27/10/2026) — inclinação: backend; confirmar se o round-trip local incomoda |
| A7 | Fonte de cotação **tempo real** da B3 | brapi/outra API com chave vs. atraso aceitável (15–20 min) vs. WebSocket de corretora | aberta (27/10/2026) — a spec de fontes já registra que a B3 proíbe coleta automatizada (pendência 9 do CONTEXT.md) |
| A8 | Fonte de proventos e múltiplos de 5 anos | RI do banco (HTML, licença a checar) vs. API com chave vs. base da CVM/B3 | aberta (27/10/2026) — pendências 10 e 11 do CONTEXT.md |
| A9 | **Mecanismo do bloqueio de acesso** (decisão 12 já é "vai ter") | Cloudflare Access (dizem ter camada gratuita — **não confirmado, verificar**) vs. senha no cloudflared vs. basic auth no nginx vs. login Django | aberta (27/10/2026) — decide com o `infra-linux`, antes do primeiro deploy |