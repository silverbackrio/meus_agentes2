--- 
name: web-scraping 
description: "Agente responsável por coletar dados de mercado da web (cotações, dividendos, balanços, indicadores) através de web scraping ou APIs gratuitas, armazenando no banco Django according to specs/fontes-de-dados.md. Use quando a tarefa envolver coleta de dados, ingestão de séries históricas ou atualização de mercado." 
metadata: 
  category: dados 
  atualizado_em: 2026-10 
--- 
# Web Scraping Agent

## Quando usar
- Coletar cotações de ações, índices (B3, NYSE, NASDAQ)
- Coletar dados de dividendos e proventos
- Coletar balanços e demonstrações financeiras
- Atualizar séries históricas de taxa (Dólar, Selic, CDI)
- Coletar dados de fundos, ETFs, FIIs

## Stack de referência (outubro de 2026)
| Peça | Escolha | Nota |
|---|---|---|
| Python | 3.14.x (faixa do projeto) | Via `.python-version` e `uv` |
| Bibliotecas | `requests`, `beautifulsoup4`, `lxml` | Para scraping simples |
| | `scrapy` | Para scraping avançado/ crawl |
| ORM Django | Usar models de `investimentos.market_data` | Append-only (R1), log (R7) |
| Agendamento | `cron` no Linux ou `django-cron` | Rua executar via CLI/manage.py |
| Testes | `pytest` + `responses` (mock de HTTP) | Nunca chame API real em test |

## Estrutura de trabalho
```bash
# 1. Descobrir fonte (manual ou research)
# 2. Criar Source no banco via manage.py ou script
# 3. Rodar script de ingestão: python manage.py ingest_dados --source=X
# 4. Verificar no banco (Observation, Serie, RawPayload)
```

## Regras essenciais (do specs/fontes-de-dados.md)
- **R1 (append-only):** Nunca sobrescrever observação existente para mesma data/serie
- **R6 (chave em .env):** Toda fonte que requisite chave deve ter valor no `.env`, nunca no código
- **R7 (log de fetch):** Todo fetch deve registrar `FetchLog` com status, itens, latência
- **R8 (licença):** Verificar licença antes de usar fonte; se não tiver livre, declarar "não disponível"
- **R9 (auditoria):** Payload bruto salvo via `RawPayload` com hash SHA256
- **R11 (bloqueio):** Se fonte não permitir coleta automática, registrar log e declarar bloqueado
- **R12 (escrita via CLI):** Nunca escrever via view/API pública; só por `manage.py` ou script CLI

## Exemplo de fluxo de uso
1. Agent pesquisa fonte viável (free com cadastro ou sem chave)
2. Cria `Source` no banco: `Source(nome='Investing.com', tipo='api', url_base='...', licenca='...', exige_chave=True)`
3. Usuário coloca chave no `.env`: `INVESTING_API_KEY=sua_chave`
4. Roda ingestão: `python manage.py ingest_dados --source=Investing.com`
5. Script coleta, salva `Observation` (se não existir), registra `FetchLog`, salva `RawPayload`

## Fontes gratuitas com cadastro (precisam de chave no .env)
- brapi (B3/Ibovespa): 15.000 req/mês — `BRAPI_API_KEY`
- EIA (WTI/Brent): cadastro por e-mail — `EIA_API_KEY`
- Alpha Vantage: 25 req/dia — `ALPHA_VANTAGE_API_KEY`
- Twelve Data: 8 créditos/min — `TWELVE_DATA_API_KEY`
- Finnhub: 60 req/min — `FINNHUB_API_KEY`
- Nasdaq Data Link: por dataset — `NASDAQ_DATA_LINK_API_KEY`

## Fontes sem chave (funcionam sem .env)
- BCB PTAX: https://olinda.bcb.gov.br/olinda/servico/PTAX/...
- BCB SGS: https://api.bcb.gov.br/dados/serie/bcdata.sgs...
- Frankfurter: https://api.frankfurter.dev/v2/rates

## Instruções para o agente
1. Sempre verifique a spec `fontes-de-dados.md` antes de propor nova fonte
2. Nunca grave chave de API no código ou commits; só no `.env` local
3. Todo fetch deve registrar no `FetchLog` (status, itens, latência)
4. Se fonte bloquear coleta automática, registrar log status="bloqueado" e mostrar "não disponível" na tela
5. Use `transaction.atomic` para writes multi-tabela; `select_for_update` se houver concorrência
6. Never use `FloatField` para dinheiro; usar `DecimalField` nos models