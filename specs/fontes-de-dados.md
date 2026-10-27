---
status: ativa
atualizada_em: 2026-10-27
---
# Spec: Fontes de Dados

## Escopo

**Dentro:** de onde vêm os dados de mercado, como são configuradas as fontes e chaves, como entram
no banco histórico local e o que impede retrabalho.
**Fora:** a análise sobre os dados (specs de domínio) e o que pode ser afirmado ao usuário
(`specs/compliance-e-avisos.md`).

## Princípio

**Dado real passado não muda, então não se paga duas vezes.** O banco local é a memória do
projeto: coleta-se uma vez, guarda-se com fonte e data, e todo o resto é leitura local — sem
internet, sem token, sem retrabalho.

## Modelo (app `market_data` do Django)

```
sources        id, nome, tipo(api|arquivo|manual), url_base, licenca, exige_chave,
               cota_por_dia/mes, ativo, observacao
series         id, source_id, codigo(fonte), nome, ativo, unidade, frequencia, moeda,
               padrao_de_data, UNIQUE(source_id, codigo)
observations   series_id, data, valor, unidade, fetched_at, payload_hash
               UNIQUE(series_id, data)          ← a chave do sistema
raw_payloads   series_id, periodo, url, resposta_bruta, fetched_at   ← para auditoria/reprocessar
fetch_log      source_id, dia, endpoint, status, itens, latencia    ← para respeitar cota
credentials    source_id, env_var, tem_chave, testada_em            ← NUNCA o valor
```

## Regras

**R1. Fato passado é imutável.** `observations` é append-only. Rebusca que devolve o mesmo valor
é `ON CONFLICT DO NOTHING`; que devolve valor **diferente** não sobrescreve — grava divergência em
`fetch_log` e sinaliza para revisão. Corrigir dado histórico é decisão humana.

**R2. Chave de idempotência:** `(series_id, data)`. Toda ingestão é repetível sem duplicar.

**R3. Leitura local primeiro.** Toda pergunta de dado responde do banco, com `as_of` = maior data
guardada. Só vai à rede quando **não existe** a observação.

**R4. Gap, não escopo.** Antes de buscar, calcule o intervalo faltante (`data > max(data)` e
furos internos) e peça só isso. Backfill completo acontece **uma vez**; depois, só o incremental.

**R5. Transporte sem LLM.** Quem faz HTTP, parse e gravação é o **script de ingestão**, rodando
por `run_terminal_command`. O agente lê o resumo da execução — token gasto com interpretação,
não com curl.

**R6. Chave só em `.env`.** `.env.example` versionado (nomes das variáveis), `.env` ignorado pelo
git, valor nunca impresso, nunca logado, nunca em comando visível. Cadastro novo de API = variável
nova no `.env.example` + linha em `credentials`.

**R7. Cota respeitada e contada.** Cada chamada registra `fetch_log`; o script aborta antes de
estourar a cota diária/mensal da fonte.

**R8. Licença antes de automatizar.** Stooq: uso pessoal, comercial proibido. B3: página proíbe
coleta automatizada. CoinGecko: atribuição obrigatória. BCB: ODbL. Fonte que impõe restrição entra
com a nota registrada em `sources.licenca` e é usada dentro do que a licença permite.

**R9. Proveniência obrigatória.** Toda linha tem fonte, licença, `fetched_at` e URL de origem;
toda série guarda o código/endpoint para ser reproduzível.

**R10. Export para gráfico.** Periódico (`manage.py export_series`) gera CSV em
`dados/export/`, para o frontend desenhar sem rede.

**R11. Bloqueio declarado.** Endpoint que falha, símbolo que não existe ou cota estourada vira
`fetch_log` com erro e lacuna relatada — nunca estimativa silenciosa.

**R12. Escrita só por `fontes-de-dados`.** Os demais agentes **leem**. Escrita concorrente é o
que gera duplicata e retrabalho.

## Critérios de aceite

- [ ] Reexecutar a mesma ingestão não duplica linha nem muda fato passado.
- [ ] Consulta respondida do banco não faz nenhuma chamada de rede.
- [ ] Gap calculado antes do fetch; nenhum período já coberto é baixado de novo.
- [ ] Chave ausente é relatada pela **variável**, sem tentar imprimir valor.
- [ ] `fetch_log` mostra cota consumida por fonte no dia.
- [ ] Toda linha exportada carrega fonte e data-base.
- [ ] Licença da fonte registrada em `sources` antes do primeiro uso automatizado.

## Lacunas (confirmar antes de automatizar)

- **Stooq:** símbolos não confirmados (`^spx`, `^dji`, `ndq`); commodities com indício de
  `XAUUSD`, `GC.F`, `CL.F`, `CB.F`; cota numérica não publicada; uso pessoal apenas.
- **B3:** não há API aberta de preços; a página de histórico proíbe coleta automatizada.
- **BCB SGS:** filtros de data obrigatórios desde 26/03/2025 e **máximo de 10 anos por
  requisição**; PTAX por período sem limite de janela confirmado.
- **Alpha Vantage:** índices históricos (S&P 500, Nasdaq) exigem *entitlement* — não é acesso
  grátis garantido; USD/BRL e ouro não confirmados.
- **CoinGecko:** acesso sem chave é limitado por IP; plano Demo (100/min) exige conta e chave;
  histórico completo só em plano pago.
- **Cotas** de Twelve Data, Marketstack, Finnhub, Tiingo, EIA e Nasdaq Data Link: as páginas
  consultadas não trazem um número único confirmado para todas as fontes — ver skill.

## Fontes

- BCB PTAX/SGS: https://dadosabertos.bcb.gov.br · https://www3.bcb.gov.br/sgspub
- Frankfurter: https://frankfurter.dev
- Stooq: https://stooq.com/db/
- B3 histórico: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/
- brapi: https://brapi.dev/docs/authentication.md
- EIA: https://www.eia.gov/opendata/register.php
- Alpha Vantage: https://www.alphavantage.co/support/

## Fontes adicionadas (27/10/2026)

### Dividendos — Yahoo Finance (gratuito, com cadastro)
- **id**: `yahoo_dividendos`
- **nome**: `Yahoo Finance Dividendos`
- **tipo**: `api`
- **url_base**: `https://finance.yahoo.com/quote/<ticker>/history`
- **exige_chave**: `false` (gratuito, limita por IP)
- **licenca**: `uso pessoal e educacional, comercial proibido` — semelhante a Stooq
- **cota_por_dia**: `100 requisições` (limite não oficial, confirmar)
- **ativo**: `qualquer ação ticker` (ex.: `petr4`, `vale3`)

### Balanços — Investing.com (gratuito, com cadastro)
- **id**: `investop_balanco`
- **nome**: `Investing.com Balanços`
- **tipo**: `api`
- **url_base**: `https://www.investing.com/quotes/<ticker>/financials`
- **exige_chave**: `true` (cadastro grátis)
- **licenca**: `uso pessoal, redistribution proibido` — confirmar nos termos
- **cota_por_dia**: `80 requisições` na free tier
- **ativo**: `ações ticker` (ex.: `petr4`, `vale3`)

## Lacunas confirmadas (27/10/2026)

As seguintes fontes já foram pesquisadas e seus limites/documentação registrados:

1. **Yahoo Finance Dividendos** — endpoint confirmado para histórico de dividendos; símbolo `.<ticker>` funciona; limitação por IP; licença pessoal/educacional.
2. **Investing.com Balanços** — endpoint de financials confirmado; cadastro grátis requer e-mail; 80 req/dia na free tier; licença pessoal.

## Pendências de pesquisa (27/10/2026)

1. **Twelve Data dividendos** — verificar se série de dividendos existe na free tier (800 créditos/dia, sem cartão). Se houver, registrar endpoint, limite e licença.
2. **MarketStack dividendos** — confirmar se a API gratuita (100/mês) traz histórico de dividendos ou apenas preço. Se não, marcar como "não cobre".
3. **Alpha Vantage dividendos** — confirmar se a free tier traz dividendos ou só preço/volume. Marcar como "não confirmado" se não houver.
4. **B3/SGA dividendo** — a página da B3 proíbe coleta automatizada (R8). Se houver fonte alternativa (ex.: brapi), registrar.
5. **Proventos EV da CVM** — verificar se a CVM tem dado de proventos em dados abertos (já citado em dominio-e-fontes.md). Se houver, registrar source e licença.
