# Skill: pesquisador-de-mercado

## Descrição
Skill responsável por pesquisar e consolidar dados de mercado financeiro, com foco em:
- Sentimento de mercado (consenso de analistas, recomendações de bancos)
- Alertas de revisão de price targets
- Cotações e proventos de ativos (ações, BDRs, fundos)
- Dados macroeconômicos (CDI, Selic, inflação, etc.)
- Integração com fontes gratuitas (Yahoo Finance, Twelve Data, BCB, etc.)

## Quando invocar
- Quando o usuário precisar de "termômetro de sentimento" do mercado
- Quando houver necessidade de comparar um ativo contra o índice de referência (Ibovespa, S&P 500, etc.)
- Quando surgirem dúvidas sobre risco político/fiscal de ativos
- Antes de tomar decisões de aporte para consolidar dados de mercado
- Para gerar alertas de "revisão recente de price target" como no caso do Citi/BBAS3

## Frontend Integration
Esta skill se conecta com o componente Simulador React e o bloco de contexto da tela de decisão:
- Fornece dados de consenso (X% compra, Y% neutro, Z% venda)
- Fornece preço-alvo médio do mercado com upside/downside
- Fornece alertas de revisão de price target (quem revisou, para onde, há quantos dias)
- Fornece dados de Ibovespa para comparação de janelas temporais (5D, 30D, 6M, 1A, 2A, 5A)

## Backend/API Integration
- Ingestão via script `.agents/scripts/ingest_dividendos_balances.py`
- Fontes suportadas gratuitamente:
  - Yahoo Finance (yfinance): preços, dividendos, cotações atuais
  - Twelve Data: balanços financeiros, indicadores
  - BCB: dados macroeconômicos (PTAX, Selic, etc.)
  - Investing.com: consenso de analistas (quando disponível)
- Dados persistidos em banco SQLite com data-base e fonte
- Regra R1 (append-only): nova observação nunca sobrescreve a existente
- Regra R4 (gap): cálculo de gaps entre períodos solicitados
- Regra R9 (proveniência): fonte, licença e URL sempre acompanham os dados

## Regras Transversais
1. **Data em todas as regras tributárias ou regulatórias** - escrever "vigente em MM/AAAA" e citar a norma
2. **Validar na fonte oficial antes de afirmar** - fontes-padrão: B3, CVM, BCB, Receita Federal
3. **Numeros entram calculados, não estimados** - fórmula + entrada explícita + resultado
4. **Sem recomendação personalizada** - analise, compare e explique cenários; quem decide o aporte é o usuário
5. **Português do Brasil** com terminologia local (selic, CDI, a.a., "cota", "carência")
6. **Não invente produto** - só descreva instrumentos que existem e caibam na spec da classe
7. **Dado de mercado muda** - cotações, taxas e spreads precisam de data-base e não podem ser memorizados

## Exemplos de Output

### Termômetro de Sentimento
```
Consenso de Analistas BBAS3:
- Compra: 65%
- Neutro: 25%
- Venda: 10%
- Preço-alvo médio: R$ 24,62 (+15% vs. preço de tela R$ 21,40)
```

### Alerta de Revisões Recentes
```
⚠️ Alerta: Citi revisou o price target de BBAS3 de R$ 28,00 para R$ 22,00 nas últimas 48h
   Estoque agora cotado a R$ 21,40 - possível sobrepreço anterior
```

### Comparativo de Janelas Temporais
```
BBAS3 vs Ibovespa - Variação Percentual:
| Janela | BBAS3 | Ibovespa | Outperf./Underperf. |
|--------|-------|----------|---------------------|
| 5D     | -8,2% | -6,5%    | -1,7% (acompanha mercado) |
| 30D    | -15,3%| -12,1%   | -3,2% |
| 6M     | -8,7% | -5,4%    | -3,3% (longe da tese) |
| 1A     | +12,4%| +8,9%    | +3,5% (tese se sustentando) |
| 2A     | +45,2%| +38,1%   | +7,1% (forte solidez) |
| 5A     | +210,5%| +185,3% | +25,2% (tese de longo prazo confirmada) |
```

## Próximos Passos para Implementação
1. Configurar chaves de API gratuitas (BRAPI, Twelve Data) no .env
2. Implementar script de ingestão que persista dados com data-base e fonte
3. Criar endpoint API que retorne consenso e alerts formatados
4. Integrar output com o bloco de contexto da tela de decisão
5. Testar alertas de revisão com dados históricos simulados