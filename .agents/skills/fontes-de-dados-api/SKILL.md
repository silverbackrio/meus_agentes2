---
name: fontes-de-dados-api
description: "Descubra, configure e mantenha fontes de API de dados de mercado: BCB PTAX e SGS, Frankfurter, Stooq, brapi (B3), EIA, Alpha Vantage, Twelve Data, Marketstack, Tiingo, Finnhub — com endpoint, limite de cota, variável de .env e licença. Use quando precisar de uma API nova, cadastrar chave, testar endpoint, verificar cota, criar o script de ingestão ou decidir de onde vem dólar, ouro, petróleo, S&P 500, Nasdaq, Ibovespa ou ações da B3."
metadata:
  category: infraestrutura
  dados: mercado
  atualizado_em: 2026-10
---
# Fontes de Dados e APIs

Catálogo de APIs para o banco histórico local (`specs/fontes-de-dados.md`): **encontrar a fonte,
configurar, testar e manter** — sem gastar cota à toa e sem quebrar termo de uso.

## Quando usar

- Precisar de dado e não existir no banco local (dólar, ouro, petróleo, índices EUA, B3, cripto).
- Cadastrar chave nova de API (variável no `.env`).
- Testar endpoint, diagnósticar falha ou cota estourada.
- Criar/atualizar o script de ingestão.

## Regra de entrada

**Antes de qualquer API nova:** existe série local para isso? `SELECT` no banco primeiro. Achou,
responde sem rede. Não achou, calcula o gap e busca **só** o que falta (spec, R3–R5).

## Catálogo — sem chave

| Para | Fonte | Endpoint | Limite | Licença/atenção |
|---|---|---|---|---|
| USD/BRL histórico | **BCB PTAX** (oficial) | `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?@dataInicial='DD-MM-YYYY'&@dataFinalCotacao='DD-MM-YYYY'&$format=json` | janela por período não confirmada | ODbL; datas no formato **DD-MM-YYYY** |
| Dólar, CDI, Selic, IPCA, séries macro | **BCB SGS** (oficial) | `https://api.bcb.gov.br/dados/serie/bcdata.sgs.<codigo>/dados?formato=json&dataInicial=DD/MM/YYYY&dataFinal=DD/MM/YYYY` | **filtro de data obrigatório desde 26/03/2025** e **máx. 10 anos por requisição** | ODbL; **registre o código da série** |
| Câmbio de referência (ECB) | **Frankfurter** | `https://api.frankfurter.dev/v2/rates?base=USD&quotes=BRL&from=YYYY-MM-DD&to=YYYY-MM-DD` | sem cota diária/mês; throttling | software MIT; dados conforme provedor; **não é a PTAX oficial** |
| Índices e commodities EUA | **Stooq** (terceiro) | `https://stooq.com/q/d/l/?s=<simbolo>&i=d&d1=YYYYMMDD&d2=YYYYMMDD` → CSV | cota não publicada | **uso pessoal, comercial proibido**; valide cada símbolo antes |
| Cotações B3 (indício) | **brapi** sem chave | tickers de teste documentados | — | o uso normal é com chave |

**Símbolos Stooq — valide antes de automatizar:** `^spx`, `^dji` e `ndq` **não confirmados**;
`COMP` aparece como índice (indício de Nasdaq); commodities com indício de `XAUUSD` (ouro spot),
`GC.F` (ouro futuro), `CL.F` (WTI), `CB.F` (Brent); `^BVP` como indício de Bovespa. **Não trate
ETF como índice** (`dia` ≠ Dow). Confirme no buscador do Stooq e na página histórica do símbolo.

**B3 oficial:** arquivos históricos desde 1986 em ZIP/TXT (COTAHIST), mas a página **proíbe
coleta automatizada** e não há API aberta de preços — não automatize sem confirmar os termos.
**CVM dados abertos** tem documentos/registros, não cotação diária.

## Catálogo — com cadastro (chave no `.env`)

| Serviço | Variável | Limite free (confirmado) | Cobertura | Cartão |
|---|---|---|---|---|
| **brapi** (B3) | `BRAPI_API_KEY` | **15.000 req/mês**, 1 simultânea | ações BR, `^BVSP`, histórico, dividendos, fundamentos | não confirmado |
| **Alpha Vantage** | `ALPHA_VANTAGE_API_KEY` | **25 req/dia** | ações globais, forex, commodities (WTI/Brent); índices históricos exigem *entitlement* | não confirmado |
| **Twelve Data** | `TWELVE_DATA_API_KEY` | **8 créditos/min, 800/dia** (custo varia por endpoint/símbolo) | forex e ações EUA; índices "coming soon" | **não exige** |
| **Tiingo** | `TIINGO_API_KEY` | **50/h, 1.000/dia, 500 símbolos/mês** | ações EUA EOD, 30+ anos | não confirmado |
| **Marketstack** | `MARKETSTACK_ACCESS_KEY` | **100 req/mês**, até 1 ano de histórico | EOD NYSE/Nasdaq (1 req por ticker pode) | não confirmado |
| **Finnhub** | `FINNHUB_API_KEY` | **60 req/min** (página não legível na consulta) | ações EUA, forex, cripto | não confirmado |
| **EIA** (petróleo) | `EIA_API_KEY` | limite não publicado nas páginas consultadas | **WTI Cushing e Brent, oficial** | registro por e-mail |
| **Nasdaq Data Link** | `NASDAQ_DATA_LINK_API_KEY` | por dataset, sem total geral confirmado | datasets variados (WIKI parou em 2018) | não confirmado |
| **CoinGecko** | `COINGECKO_API_KEY` | sem chave: limite por IP; Demo 100/min | cripto; histórico completo é pago | — |

Cobertura ≠ plano free: um ativo aparecer no produto não significa que está na franquia gratuita.
Confirme **testando com a chave** antes de prometer dado.

## Configuração de chave

1. Crie a conta na fonte, pegue a chave, **não cole a chave no chat nem no código**.
2. Adicione a variável em `.env.example` (só o nome, valor vazio) e no `.env` local o valor.
3. Registre em `credentials` do banco: fonte, variável, tem_chave, testada_em.
4. Teste com uma chamada real e registre o resultado em `fetch_log`.
5. Nunca imprima, logue ou passe a chave em argumento de comando visível; use `os.environ` /
   `env.<VAR>` no servidor.

## Contrato do script de ingestão

```bash
python manage.py ingest --serie <nome> --de YYYY-MM-DD --ate YYYY-MM-DD
# 1. lê o banco: quais datas já existem?
# 2. calcula o gap
# 3. busca SÓ o gap (API > HTML > manual), respeitando cota
# 4. normaliza: valor, unidade, data, fonte, fetched_at
# 5. insert idempotente (conflict do nothing) + payload bruto em raw_payloads
# 6. registra fetch_log (status, itens, latencia) e imprime resumo curto
```

Saída esperada: `novos=NN, ignorados=NN, erros=NN, cota_fonte=AA/BB` — nada mais. O agente lê
esse resumo, não a resposta crua.

## Erros clássicos

- Baixar histórico inteiro de novo porque não consultou o banco antes.
- Sobrescrever valor de 2016 com a cotação de hoje "para atualizar".
- Chave colada no código, no comando ou no repositório.
- Estourar cota diária rodando backfill em loop (25 req/dia é o Alpha Vantage inteiro).
- Tratar símbolo de ETF como índice, ou taxa de referência como PTAX.
- Automatizar fonte cuja licença proíbe coleta.

## Fontes

- BCB dados abertos: https://dadosabertos.bcb.gov.br
- Frankfurter: https://frankfurter.dev
- Stooq: https://stooq.com/db/
- brapi: https://brapi.dev/docs
- Alpha Vantage: https://www.alphavantage.co/support/
- Twelve Data: https://twelvedata.com/pricing
- EIA: https://www.eia.gov/opendata