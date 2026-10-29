# Skill: fontes-de-dados-api

## Descrição
Skill responsável por gerenciar e configurar as fontes de dados de mercado, com foco em:
- Catálogo de APIs disponíveis (gratuitas e pagas)
- Chaves de API e variáveis de ambiente (.env)
- Contratos de ingestão e schemas de dados
- Cotas de consumo e rate limiting
- Licenças e proveniência dos dados
- Inicialização e migração de banco de dados

## Quando invocar
- Quando necessário configurar novas fontes de dados
- Quando chaves de API precisarem ser rotacionadas ou atualizadas
- Quando o sistema mostrar "cota esgotada" messages
- Quando precisar adicionar ou remover uma fonte de dados do sistema
- Durante o setup inicial do projeto ou após deploy

## Frontend Integration
- Tela de configuração de fontes (acessível via menu/config)
- Lista de fontes ativas/inativas com status de cota
- Campos para inserção de novas chaves de API (devem ser direcionadas ao .env)
- Status visual de cada fonte (online/offline, cota disponível/esgotada)
- Botão de "Testar Conexão" para cada fonte configurada

## Backend/API Integration
- Gerenciamento de variáveis de ambiente (.env example already project)
- Validação de chaves API antes de persistir no sistema
- Contagem de usos diários por fonte (regra R7 do specs/fontes-de-dados.md)
- Cota diária por fonte (campo `cota` na model Source)
- Regra R12: escrita só por fontes-de-dados (never via view or API)
- Scripts de ingestão CLI em `.agents/scripts/`

## Fontes Suportadas (Catalogadas)

### Fontes Gratuitas (Sem Chave ou Cadastro Simples)
| Fonte | Tipo | Limite | Cadastro | URL |
|-------|------|--------|----------|-----|
| Yahoo Finance | Preços/dividendos | Gratuito | yfinance Python lib | https://finance.yahoo.com |
| Twelve Data | Dados completos | 8 cr/min, 800/dia | Gratuito (registrar e-mail) | https://twelvedata.com |
| BCB (Banco Central) | Dados macro | Gratuito | Não requer cadastro | https://dadosabertos.bcb.gov.br |
| Investing.com | Consenso/calendário | Variável | Gratuito (registro) | https://www.investing.com |
| Alpha Vantage | Diversos | 25 req/dia | Gratuito (API Key) | https://www.alphavantage.co |
| Naval Action | (Outros) | Variável | - | - |

### Fontes com Cadastro (Gratis)
| Fonte | Tipo | Limite | Cadastro | URL |
|-------|------|--------|----------|-----|
| EIA (WTI e Brent) | Commodities | Variável | Registro por e-mail | https://www.eia.gov/opendata/register.php |
| Brapi (B3/Ibovespa) | Ações/BDRs | 15.000 req/mês | Cadastro no dashboard | https://brapi.dev/dashboard |
| Marketstack | Ações globais | Plano grátis | Registro | https://marketstack.com |
| Finnhub | Diversos | 60 req/min grátis | Registo | https://finnhub.io |
| Tiingo | Dados financeiros | Plano grátis | Registro | https://tiingo.com |

### Fontes Pagas / Enterprise
| Fonte | Tipo | Limite | Observações |
|-------|------|--------|-------------|
| Bloomberg | Dados completos | Contratual | Institucional |
| Refinitiv | Dados completos | Contratual | Institucional |
| S&P Global | Dados completos | Contratual | Institucional |

## Estrutura de Dados (Modelos Django)

### Source Model (já existente em market_data)
```python
class Source(models.Model):
    nome = models.CharField(max_length=100)  # Ex: "Yahoo Finance", "Twelve Data"
    tipo = models.CharField(max_length=50)   # Ex: "api", "csv", "bcb"
    url_base = models.URLField(blank=True)   # URL da API ou fonte
    licenca = models.CharField(max_length=100)  # Ex: "Gratuita com atribuição"
    exige_chave = models.BooleanField(default=False)  # Precisa de chave API
    cota = models.IntegerField(default=None, null=True)  # Cota diária
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
```

### .env Example (já existente)
```
# Fontes COM cadastro (cole o valor no .env)
# brapi (B3/Ibovespa) — 15.000 req/mês ....... https://brapi.dev/dashboard
BRAPI_API_KEY=

# EIA (WTI e Brent, oficial) — cadastro por e-mail ... https://www.eia.gov/opendata/register.php
EIA_API_KEY=

# Alpha Vantage — 25 req/dia ....... https://www.alphavantage.co/support/
ALPHA_VANTAGE_API_KEY=

# Twelve Data — 8 créditos/min, 8... (ver catálogo completo)
TWELVE_DATA_API_KEY=

# Fontes SEM cadastro (não modificar estas linhas)
# yfinance (gratuitos, sem chave)
# brapi (já tem key embutida no código, usar como fallback)
```

## Regras de Cota e Consumo
- Cada fonte tem um limite diário (`cota` no modelo Source)
- O script de ingestão decrementa a cota a cada uso (regra R7)
- Quando cota chega a 0, fonte é marcada como "esgotada" temporariamente
- O sistema deve avisar o usuário quando a cota estiver baixa (< 20% restante)
- Reset da cota ocorre em horário definido (configurável, geralmente 00:00 do fuso do projeto)
- Regra R12: escrita de novos dados só via script de ingestão CLI, nunca via views ou API direta

## Convenções de escrita
- **Skill**: diretório = nome no frontmatter, só minúsculas/números/hífens, sem hífen inicial ou final e sem hífen duplo
- `name` e `description` são obrigatórios na frontmatter; a `description` é o que o agente lê para decidir se carrega a skill — seja específico sobre **quando** invocar
- Todos os nomes de variáveis de ambiente devem ir no `.env.example` (não no .env real)
- Licenças devem ser sempre citadas com versão/data de vigência quando possível

## Próximos Passos para Implementação
1. Preencher as chaves de API no .env (apenas as necessárias para o início)
2. Testar conectividade com cada fonte catalogada
3. Implementar validação de chave antes de adicionar ao catálogo
4. Criar interface de administração para gerenciar fontes ativas/inativas
5. Documentar limites de cota observados em produção
6. Implementar rotacionamento automático de chaves quando perto do limite