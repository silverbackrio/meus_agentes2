---
status: ativa
atualizada_em: 2026-10-30
---
# Spec: Aplicação

O que **construir**: estrutura do projeto, apps Django, contrato da API, páginas do frontend e
regras de implementação. É a referência do `dev-backend` e do `dev-frontend` — ela diz o que
existe e como se conecta; o **cálculo** continua sendo autoridade da spec da classe de ativo e o
**dado** da `fontes-de-dados.md`.

## 0. Visão geral (entrevista de 27–28/10/2026)

**Projeto:** base de conhecimento e especialização em investimentos no Brasil, cobrindo renda
fixa, renda variável (ações, BDRs), fundos, ETFs e FIIs, previdência, câmbio/derivativos e
gestão de carteira — mais a aplicação que os agentes constroem para o investidor usar.

**Modelo do sistema:** (1) regras ficam nas specs e skills; (2) os agentes explicam e calculam
com base nelas; (3) a aplicação Django guarda e expõe dado histórico, carteira, análise e
configuração; (4) o frontend React consome a API; (5) a infraestrutura executa e protege o
sistema; (6) as fontes externas alimentam o banco por ingestão controlada.

**Princípios travadores:** dado real passado não muda e não se paga duas vezes; toda regra
tributária com data e fonte; nada é estimado quando dá para calcular ou consultar; quem decide
o aporte é o investidor, nunca o sistema; modularidade por padrão; segredo fora do código.

**Bloco 1 da v1 (decidido na entrevista de 27/10/2026, caso BBAS3):** para quem já é
acionista, a primeira tela entregue é **gestão de posição** — preço médio atual, P&L,
simulador de novo preço médio, yield on cost projetado e consenso de mercado datado — e não
uma tela genérica de descoberta de ativos.

**Fora desta spec:** fórmula de cada classe (`specs/<classe>.md`), origem de dado
(`specs/fontes-de-dados.md`), interpretador (`specs/ambiente-e-versoes.md`), o que pode ser
afirmado (`specs/compliance-e-avisos.md`) e operação de servidor (`.agents/skills/infra-linux`).

## Escopo

**Dentro:** stack e versões, estrutura de diretórios, apps e seus modelos, endpoints REST, páginas
React, camadas de código, ordem de implementação e critérios de aceite do código.
**Fora:** regra de domínio e fórmula (`specs/<classe>.md`), origem e ingestão de dado
(`specs/fontes-de-dados.md`), versão de interpretador (`specs/ambiente-e-versoes.md`), o que pode
ser afirmado ao usuário (`specs/compliance-e-avisos.md`) e operação de servidor
(`.agents/skills/infra-linux`).

## Princípios de arquitetura

Valem para o backend e para o frontend, e sobrepõem qualquer escolha de convenção que surja
no caminho. Mudá-los é mudar esta spec primeiro.

**P1. Modular.** Cada app (`market_data`, `carteira`, `analise`) e cada módulo do frontend tem
fronteira única: só se fala com o vizinho pela camada pública (service/API client), nunca pelo
interior. Dependência sempre em **uma direção** — o inverso é bug de arquitetura.

**P2. Portátil.** Nada de atrelar código a lugar, provedor ou sistema: caminho relativo,
configuração por variável de ambiente, sem caminho absoluto de Windows ou Linux embutido, sem
serviço externo obrigatório para subir (rede é opcional). O mesmo código roda em desenvolvimento
e em produção sem alteração — SQLite/Postgres é mudança de configuração, não de código.

**P3. Reutilizável.** A lógica de domínio é função pura sem Django no meio
(`analise/calculos.py`, `analise/renda_fixa.py`): serve para a view, para um `manage.py command`,
para um teste e para qualquer app futura sem retrabalho. No frontend, componentes e hooks sem
amarro com rota ou tela concreta.

**P4. Crescimento incremental.** Recurso novo entra por **composição** (módulo, componente,
rota nova) e não por edição em um centro que todos importam. Sem classe que acumula responsabilidades
e sem import circular entre apps.

**P5. Dependências mínimas e opcionais.** Toda dependência nova precisa de justificação no
diff: **o que ela substitui de código próprio, quem mantém, por que não dá para fazer com o
stdlib**. O cálculo de domínio **nunca** depende de pacote de terceiro. Dependência que serve a
uma única feature vira `optional-dependencies` (Python) ou lazy-load (frontend) — crescer não
pode virar obrigação de instalar tudo.

## Stack (decisões de 27/10/2026)

| Camada | Escolha | Por quê |
|---|---|---|
| Python | 3.14 (faixa `>=3.12,<3.15`) | `ambiente-e-versoes.md` |
| Framework | **Django 5.2 LTS** + Django REST Framework | suporte até 04/2028, DRF 3.18 oficial |
| Gerenciador | `uv` (`.python-version` + `requires-python`) | regra de detecção em `ambiente-e-versoes.md` |
| Banco | **SQLite agora → Postgres depois** | schema append-only já portável; migração = trocar driver |
| Testes | `pytest` + `pytest-django` | dourados por cálculo obrigatório |
| Lint/format | `ruff` (+ `mypy` no domínio) | já no `backend-python-django` |
| Frontend | **React + Vite** | `frontend-react-vite` |

## Estrutura

```
raiz/
  pyproject.toml            ← requires-python = ">=3.12,<3.15" + ruff/mypy
  .python-version           ← 3.14
  pytest.ini                ← DJANGO_SETTINGS_MODULE + pythonpath
  manage.py
  investimentos_project/    ← project: settings/{base,dev,prod}.py, urls.py, wsgi, asgi
  investimentos/            ← pacote dos apps (precisa de __init__.py)
    market_data/            ← app 1 — séries, observações, payload e fetch_log
    carteira/               ← app 2 — objetivo, perfil, política, posições, operações
    analise/                ← app 3 — cálculos, métricas, cenários, dossiês
    documentos/             ← app 4 — documento → lançamentos → carteira
  .agents/scripts/          ← ingestão (script CLI, R3)
  frontend/                 ← Vite + React (a criar)
  dados/                    ← coletas datadas e export/ (R10 da fontes-de-dados)
  specs/  GLOSSARY.md  CONTEXT.md  ARCHITECTURE_DECISIONS.md
```

Regra de dependência: `analise` **lê** `market_data` e `carteira`; `carteira` **lê**
`market_data`; `documentos` **lê** `carteira` (promoção grava operação); `market_data` não
depende de nenhum outro. Nenhum app importa o frontend, e o frontend não importa modelo Django
— só JSON da API.

## Apps

### `market_data`
Tabelas da `specs/fontes-de-dados.md`: `sources`, `series`, `observations`, `raw_payloads`,
`fetch_log`, `credentials`. Fim da linha da escrita: **só o script de ingestão escreve**.
Nenhuma outra view pode gravar observação.

### `carteira`
Espelha `specs/dominio-e-fontes.md` e `specs/carteira-e-risco.md`:

| Entidade | Campos essenciais |
|---|---|
| `Objetivo` | valor-alvo, unidade (real/nominal), horizonte, liquidez necessária |
| `Perfil` | tolerância, capacidade, restrições |
| `Classe` | nome, fator de risco, liquidez, tratamento tributário |
| `Politica` | classe, peso_alvo, faixa_min, faixa_max, regra_de_rebalanceamento |
| `Posicao` | ativo, classe, quantidade, custo_medio, moeda, instituição |
| `Operacao` | evento (aplicacao/resgate/venda/distribuicao/...), data, valor, base_de_calculo, aliquota, imposto_ja_retdo, iof |

V1 é **sem login e sem multiusuário**: existe um único dono (`owner` já nasce no schema para a v2
não exigir migração de dados).

### `analise`
Estado derivado, não fonte de verdade: `Metrica` (valor, fórmula, período, frequência, base,
data-base), `Cenario` (choque por fator, premissa datada, impacto em R$ e %), `Dossie` (data,
ativos, texto com fontes). Onde a spec manda cálculo (`renda-fixa.md`, `carteira-e-risco.md`),
ele vive em módulo Python puro e testável — `analise/calculos.py`, `analise/renda_fixa.py` —
jamais em view, template ou JavaScript.

### `documentos`
App reutilizável de leitura de documento: recebe arquivo ou texto, identifica o layout,
extrai lançamentos e, sob comando explícito, promove para `Posicao`/`Operacao` da carteira.

| Entidade | Campos essenciais |
|---|---|
| `Documento` | nome, `sha256` (idempotência), tipo, layout, confiança, status, `as_of`, texto, avisos |
| `Lancamento` | documento + linha (único), data, ativo, código, lado (C/V), quantidade, preço, valor, operação gerada |

Layouts registrados em `documentos/layouts/` — hoje `nota_corretagem_b3`. Layout novo entra
como **módulo novo + uma linha no registro**, sem editar o parser existente (P4). O detector
devolve confiança 0–1; abaixo de 0,5 a leitura é **recusada** com `422`, nunca chutada.

Regra da venda: `C` vira `aplicacao` (inclusão); `V` vira `venda` e só **reduz** posição
existente — sem posição cadastrada o lançamento é ignorado com motivo, nunca cria posição.

Limites declarados: PDF exige a dependência **opcional** `pypdf` (sem ela, o endpoint aceita o
campo `texto`); OCR de imagem digitalizada não entra na v1.

## Contrato da API — `/api/v1/`

Formato único de resposta com número, sem exceção:

```json
{ "valor": 5.2371, "unidade": "BRL/USD", "data_base": "2026-10-24",
  "fonte": {"nome": "BCB PTAX", "url": "..."}, "as_of": "2026-10-24" }
```

Série devolve `unidade`, `frequencia`, `moeda`, `licenca`, `pontos: [[data, valor], ...]` e
`gaps: [[de, ate], ...]`.

| Método | Rota | Devolve |
|---|---|---|
| GET | `/series/?ativo=&moeda=&frequencia=` | séries com cobertura e `as_of` |
| GET | `/series/{id}/observacoes/?de=&ate=` | pontos + gaps + proveniência |
| GET | `/dados/status` | cobertura por série, `fetch_log` do dia, cota consumida |
| GET | `/carteira/resumo` | posições, custo médio, pesos atuais vs política, P&L com `as_of` |
| POST | `/carteira/operacoes` | registrar operação (valida evento, data, base de cálculo) |
| GET | `/analise/metricas/?periodo=&frequencia=` | valor + fórmula usada + entradas + data-base |
| POST | `/analise/simular/` | novo preço médio, YoC e projeção de renda passiva (entrada do usuário, sem gravação) |
| POST | `/analise/cenarios` | choque por premissa datada, impacto em R$ e % |
| GET | `/analise/dossies/` · `/analise/dossies/{data}` | dossiês datados |
| GET | `/comparar?ativos=&base=liquida` | comparação com prazos e base equivalenciados (ver nota abaixo) |
| GET | `/documentos/` | documentos recebidos com status, layout e lançamentos |
| POST | `/documentos/` | recebe `arquivo` (PDF/txt) ou `texto` e extrai os lançamentos |
| GET | `/documentos/{id}/` | documento com os lançamentos extraídos |
| POST | `/documentos/{id}/promover/` | grava posições e operações na carteira (idempotente) |

Erros: envelope `{erro, campo, sugestao}` — `404` série inexistente, `409` divergência de dado
observado, `422` entrada inválida (falta data-base, unidade ou faixa), `429` cota de fonte
estourada. **Não existe ingestão por HTTP**: baixar dado é `manage.py ingest`, nunca endpoint
público.

**Nota do `/comparar` (registrada em 30/10/2026):** os produtos vêm com entrada explícita —
cada item de `ativos` é `nome|taxa_a_a|prazo_dias|tipo` separado por vírgula (`tipo` =
`isento` para LCI/LCA/CRI/CRA ou `tributado`), `base` só aceita `liquida` (renda-fixa.md R5) e
`valor` (VI em BRL) é opcional: sem ele entra a premissa declarada de R$ 10.000,00, que o
envelope sempre mostra. Prazo menor que 30 dias responde `422` com o motivo do IOF regressivo
(Decreto 6.306/2007), que o módulo não calcula. O cálculo é função pura em
`analise/renda_fixa.py` com testes dourados em `analise/tests.py`; a rota fica em
`/api/v1/comparar/` (nível raiz, fora do prefixo `/analise/`), com variante sem barra final.

## Páginas (React + Vite)

| Rota | Tela | Origem dos dados |
|---|---|---|
| `/` | painel: resumo da carteira, cobertura de dados, avisos | `/carteira/resumo`, `/dados/status` |
| `/dados` | séries, cobertura, gaps, export CSV | `/series`, `/dados/status` |
| `/carteira` | posições, operações, custo médio, alocação vs política | `/carteira/*` |
| `/analise` | métricas, cenários, gráficos | `/analise/*` + `dados/export/` |
| `/dossies/{data}` | dossiê datado | `/analise/dossies/{data}` |
| `/comparar` | comparativo em base líquida | `/comparar` |
| `/config` | fontes, status de chave e cota — **nunca o valor da chave** | `/dados/status` |

## Regras

**R1. A spec de domínio manda.** A aplicação implementa a regra escrita na spec da classe, com a
data de vigência lá registrada. Divergência entre código e spec é bug do código.

**R2. Todo número trafega datado.** `data_base` + `unidade` + `fonte`/`as_of` em toda resposta
que traz valor. Faltando um dos três, a resposta é inválida e o front mostra o aviso de dado
ausente em vez de exibir zero.

**R3. Escrita de dado de mercado é só via ingestão CLI** (`fontes-de-dados.md` R12). View, comando
de teste e nunca o front gravam `observations`.

**R4. O front não calcula.** Nenhum IR, taxa equivalente, volatilidade, Sharpe ou custo médio é
calculado em JavaScript: o backend devolve o valor **com a fórmula que usou**, o React só
renderiza. O que o front pode fazer é ordenar, formatar e desenhar.

**R5. Dinheiro é `Decimal`, nunca `float`.** Datas em ISO-8601; sem campo de moeda fora de
`BRL|USD|outra`; sem recurso exclusivo do SQLite (nada de `AUTOINCREMENT` específico, de datas
como texto fora do ISO ou de funções só-do-driver) para a troca por Postgres ser de configuração.

**R6. Cada cálculo obrigatório tem teste dourado.** Entrada explícita, fórmula da spec, resultado
esperado — um teste por linha de "Cálculos obrigatórios" das specs. Falha de teste dourado
para a entrega.

**R7. Tela funciona sem rede.** Toda rota responde do banco local com o `as_of` da maior data
guardada; a rede só entra quando a observação não existe (`fontes-de-dados.md` R3).

**R8. Nenhuma chave no frontend.** Segredo vive em `.env` no servidor; o bundle React não contém
API key, token nem endpoint interno, e nada de sessão em `localStorage`.

**R9. Nenhuma tela recomenda.** Nenhum "compre", "venda", "aloque X%" ou ordem de aporte na
interface; os avisos obrigatórios de `compliance-e-avisos.md` são renderizados junto da resposta
que os exige (comparativo, simulação, cenário, dossiê).

**R10. Migrações versionadas e código revisado.** `makemigrations` committado, `ruff` e `pytest`
verdes antes de entregar, e toda alteração passa pelo `revisor-de-codigo` (e pelo
`revisor-de-compliance` quando houver regra tributária no diff).

**R11. Produção não roda `runserver`.** Servidor, túnel, TLS e hardening são escopo do
`infra-linux`; o `dev-backend` só entrega código que sobe em gunicorn.

**R12. Mudou a estrutura, mudou esta spec primeiro.** App novo, rota nova ou tela nova entra aqui
antes de existir no código.

**R13. Dependência nova é justificada e revisada.** O diff entrega a linha: nome, versão, o que
substitui, quem mantém e por que o stdlib não resolve. Sem isso, o `revisor-de-codigo` devolve.
Princípios P1–P5 valem aqui.

**R14. Leitura de documento é determinística e conferível.** O que não está escrito no
documento não é inferido: parser sem confiança mínima recusa (`422`), linha de total não vira
lançamento, divergência entre quantidade×preço e valor vira **aviso**, não correção silenciosa.
Promover é idempotente por lançamento e nunca duplica operação; venda sem posição reduz, não
inclui. Todo documento guarda o texto lido para auditoria e reprocessamento.

## Ordem de implementação

0. **Bloco 1 da v1 (prioridade da entrevista 27/10):** `analise/calculos.py` puro com preço
   médio, YoC e projeção de renda passiva + `POST /analise/simular/` + testes dourados.
1. Scaffold do backend: `uv`, Django 5.2, DRF, settings, três apps vazios, `pytest` verde.
2. `market_data`: modelos + `manage.py ingest` com **uma** série (PTAX USD/BRL) + `export_series`.
3. Scaffold do frontend: Vite + React, cliente de API, tela `/dados` com cobertura e gaps.
4. `carteira`: modelos, `/carteira/resumo` e as telas de posição e operação.
5. `analise`: cálculos com testes dourados, `/analise/metricas` e `/analise/cenarios`.
6. Dossiês e `/comparar`, com os avisos de compliance renderizados.
7. `infra-linux`: gunicorn + nginx + túnel, só depois de haver tela para servir.

## Critérios de aceite

- [ ] `uv sync && pytest` verdes na faixa `>=3.12,<3.15`, com Python informado no início da tarefa.
- [ ] Toda resposta da API com número traz `data_base`, `unidade` e `fonte`/`as_of`.
- [ ] Reexecutar a ingestão não duplica linha nem altera fato passado.
- [ ] Tela renderiza com a rede desligada, usando o banco local.
- [ ] Cada "Cálculo obrigatório" das specs tem teste dourado correspondente.
- [ ] Nenhum cálculo de domínio existe em JavaScript; nenhum `float` guarda dinheiro.
- [ ] Trocar SQLite por Postgres não exige alterar schema (só driver e `DATABASES`).
- [ ] Nenhuma chave no bundle do frontend e nenhuma recomendação nas telas.
- [ ] Nenhum módulo importa o interior de outro módulo; a dependência entre apps é em uma direção.
- [ ] Toda dependência nova justificada (o que substitui / quem mantém); o cálculo usa só stdlib.
- [ ] Roda igual em dev e em produção sem editar código (só configuração).
- [ ] `manage.py check` e `ruff check .` limpos, e `pytest` com 100% verde antes do commit.

## Lacunas

- **Vue:** mantido React+Vite porque a skill `frontend-react-vite` já existe; trocar exigiria
  reescrever a skill — decidir só se houver motivo concreto, e então mudar esta spec antes.
- **Postgres:** versão e forma de instalar no Ubuntu 26.04 não definidas; preencher no momento
  da migração, junto com o `infra-linux`.
- **Autenticação e multiusuário (v2):** fora desta versão; o `owner` existe no schema para não
  exigir migração de dados depois.
- **Porta, hostname e domínio de produção:** definidos pelo ambiente, não por esta spec.
- **Números de versão do ecossistema** (DRF, pytest-django, Vite): confirmar no `pyproject.toml`
  gerado, não nesta spec.