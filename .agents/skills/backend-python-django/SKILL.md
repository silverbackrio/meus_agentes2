---
name: backend-python-django
description: "Desenvolva backend em Python e Django: estrutura de projeto, models e ORM, migrations, admin, API com DRF ou Django Ninja, autenticação e permissões, testes com pytest, performance (N+1, cache, índices), segurança e deploy. Use quando a tarefa envolver criar ou alterar endpoint, model, migration, serializer, view, comando de management ou qualquer código de backend Django."
metadata:
  category: desenvolvimento
  linguagem: python
  framework: django
  atualizado_em: 2026-10
---
# Backend: Python + Django

Guia para construir e manter backend Django em produção, do model ao deploy, com verificação
obrigatória antes de entregar.

## Quando usar

- Criar ou alterar model, migration, endpoint, serializer, permissão ou comando.
- Projetar contrato de API, autenticação ou camada de serviço.
- Diagnosticar query lenta, bug de concorrência, falha de segurança ou erro de deploy.
- Escrever ou revisar testes de backend Django.

## Stack de referência (outubro de 2026)

| Peça | Escolha | Nota |
|---|---|---|
| Python | **3.14.x** — linha do projeto (Ubuntu) | 3.15.2 é a mais nova (25/10/2026), ainda cedo para certificar; Python não tem LTS oficial |
| Django | **5.2.x LTS** em produção (suporte até abr/2028) | 6.1.2 é a estável mais nova; 6.2 LTS sai em abr/2027 |
| API | **DRF 3.18.x** ou **Django Ninja 1.7.x** | DRF = convenções e ecossistema; Ninja = schemas Pydantic + OpenAPI enxuto |
| Dependências | `pyproject.toml` + lockfile + **uv** | Poetry e pip-tools continuam válidos se já usados |
| Lint/formato | **ruff** (config em `pyproject.toml`) | |
| Tipos | **mypy** ou **pyright** | verificador estático, não substitui o ruff |
| Testes | **pytest** + **pytest-django** + **factory-boy** | |
| Servidor | **gunicorn**/uvicorn atrás de proxy | ASGI quando usar async de verdade |

Notas de versão que mudam código:
- Django 6.0+: `BigAutoField` é o `DEFAULT_AUTO_FIELD` padrão, CSP nativo, *template partials*.
- Django 6.1: *fetch modes* de campos do ORM, `ON DELETE` em nível de banco, múltiplos mailers.
- ORM **async é parcial**: uma `view async def` não torna as consultas assíncronas — conheça a
  fronteira antes de prometer concorrência.

## Versões: matriz e decisão (spec `ambiente-e-versoes`)

A faixa do projeto é **Python 3.12 a 3.14** (`requires-python = ">=3.12,<3.15"`), com pin de
desenvolvimento na **3.14**. Django sempre em série com suporte.

| Django | Python declarado | Situação 10/2026 | Fim de suporte |
|---|---|---|---|
| 4.2 LTS | 3.8–3.12 (3.12 da 4.2.8) | **sem suporte** | 04/2026 |
| 5.1 | 3.10–3.13 (3.13 da 5.1.3) | **sem suporte** | 12/2025 |
| 5.2 LTS | 3.10–3.14 (3.14 da 5.2.8) | extended | 04/2028 |
| 6.0 | 3.12–3.14 | extended | 04/2027 |
| 6.1 | 3.12–3.15 (3.15 da 6.1.3) | **mainstream** | 12/2027 |

Ecossistema: DRF 3.18.x (Python 3.10–3.15, Django 5.2/6.0/6.1) · Django Ninja 1.x (`>=3.7`,
`Django >=3.1` sem teto) · pytest-django 4.14.x (Python ≥3.10, Django 5.2 e 6.0 oficiais) ·
mypy exige Python 3.10+ para rodar · gunicorn Python 3.10+ · ruff só define alvo 3.7+.

**Detecção e pergunta — faça nesta ordem:**

1. `.python-version` (pin) → 2. `requires-python` (contrato) → 3. `python3 --version` →
   4. `uv python list --only-installed` (opções disponíveis).
2. **Informe sempre** a versão detectada na resposta.
3. **Pergunte qual usar** (ask_questions) só quando houver mais de uma opção e pin + ambiente
   não convergirem. **Proibido escolher em silêncio ou trocar a versão sozinho.**
4. Escolhida, grave: `uv python pin <versão>` — a pergunta acontece uma vez por projeto.
5. Divergência (pin 3.14, máquina 3.12) é **reportada e corrigida** com
   `uv python install 3.14 && uv python pin 3.14`, nunca silenciada.
6. Servidor remoto é verificado à parte: se a versão do Ubuntu 26.04 divergir da local, declare
   as duas.

Compatibilidade é sempre confirmada nas release notes antes de afirmar — a matriz acima é datada
e precisa de reconferência a cada release nova. Detalhes e lacunas: `specs/ambiente-e-versoes.md`.

## Ambiente do projeto

- **SO alvo:** Ubuntu 26.04 LTS. **Python:** faixa 3.12–3.14 (requires-python ">=3.12,<3.15"),
  pin de desenvolvimento na 3.14. Fixe com `uv python pin 3.14`.
- O desenvolvimento é remoto: Windows 10 do lado de quem digita, código no Ubuntu. Não assuma
  caminho do Windows nem `localhost` sem confirmar onde o processo roda.
- O Ubuntu LTS traz um Python mais antigo que o da linha do projeto. Em vez de mexer no
  interpretador do sistema, deixe o **uv** gerenciar a versão:
  `uv python install 3.14` → `uv python pin 3.14` → `uv sync`.
- Antes de qualquer tarefa de backend, rode `python3 --version` e declare na resposta se o
  ambiente está na 3.14. Se estiver em outra versão (a VM do Codebuff veio com 3.12), **reporte
  a divergência** e use o uv para obter a linha certa — nunca trabalhe em silêncio sobre a versão
  errada.
- A versão do Ubuntu também limita o que dá para instalar via `apt` (libpq, nodejs, libs de
  imagem); registre a versão do Ubuntu quando ela condicionar o build.

## Estrutura

```
projeto/
  pyproject.toml  uv.lock
  manage.py
  config/
    settings/{base,dev,prod}.py    # por variável de ambiente, nunca por commit
    urls.py  asgi.py  wsgi.py
  apps/<dominio>/
    models.py  services.py  views.py  serializers.py  admin.py  urls.py
    migrations/
    tests/                          # espelha a estrutura do app
```

Regras: um app por domínio; negócio em `services.py` (ou camada de domínio), **não** na view;
segredo só em variável de ambiente; `DEBUG=False` fora de dev.

## Models, ORM e migrations

- **Dinheiro é `DecimalField`**, nunca `FloatField`. Datas com `DateTimeField` e fuso; usar
  `UUIDField` como PK pública quando o recurso for exposto por API.
- `ForeignKey` sempre com `on_delete` explícito e `related_name`; `db_index`, `unique=True` e
  `constraints` (`UniqueConstraint`, `CheckConstraint`) onde o dado exigir.
- **Consultas:** `select_related`/`prefetch_related` para relações, `values()`/`values_list()`
  para projeção, `aggregate`/`annotate` para calcular **no banco**, `iterator()` para volume
  grande. Filtrar em Python é bug de performance.
- **Transações:** `transaction.atomic` em escrita multi-tabela; `select_for_update` quando
  houver concorrência; preferir restrição única no banco a checagem em código.
- **Migrations:** sempre gerar e revisar; nunca editar migration já aplicada em ambiente
  compartilhado; manter reversível; separar *schema* de *data*; no CI, `python manage.py
  makemigrations --check` para travar drift.

## Camada de API

1. Validar na fronteira (serializer/schema) e devolver erro padronizado com status correto.
2. Lógica em serviço; a view só orquestra: validar → chamar serviço → serializar.
3. Paginação obrigatória em listagem, filtro declarado e versionamento desde o início.
4. Documentar o contrato (OpenAPI/DRF-yasg ou Ninja) e tratar exceção em um handler global.
5. Logging estruturado com `request_id`; nunca logar token, senha ou payload completo.

## Autenticação e permissões

- App próprio com SPA: sessão com cookie `SameSite` **ou** token em header, escolhido e
  documentado — não misturar os dois sem motivo.
- Padrão é **negar por padrão**: permission explícita em toda view, checagem de objeto quando
  o recurso for de usuário.
- Escopo de dados sempre pelo usuário autenticado, nunca por id vindo do cliente.

## Segurança (checklist obrigatório)

- CSRF ativo em toda mutação; `X_FRAME_OPTIONS`, `ALLOWED_HOSTS` e cookies `Secure`.
- SQL injection: só ORM e parâmetros parametrizados.
- XSS: escapar de template, `Content-Type` correto, CSP (nativa desde Django 6.0).
- Upload com validação de tipo/tamanho; rate limit em login e endpoints caros.
- Segredos em variáveis de ambiente, fora do repositório, com `.env` ignorado pelo git.

## Performance

1. Medir antes de otimizar: `django-debug-toolbar`, `connection.queries` ou `EXPLAIN`.
2. Causa clássica de lentidão: N+1 — corrigir com `prefetch_related`, não com cache.
3. Cache com a API do Django (Redis/Memcached) em leitura cara; invalidar por chave de domínio.
4. Endpoint de listagem: paginação + índice que cubra o `WHERE`/`ORDER BY`.

## Testes

```
tests/
  unit/test_services.py     # regra de negócio pura
  api/test_<recurso>.py     # contrato, status, permissão, serialização
  factories.py              # factory-boy
```
- Casos mínimos por endpoint: sucesso, falha de validação, 401, 403, 404 de recurso alheio.
- Pirâmide: muitos units de serviço, boa camada de API, poucos E2E.
- Compatibilidade: conferir no `pyproject.toml` que Django/Python/DRF estão na faixa suportada.

## Instruções

1. Leia o requisito e o contrato existente antes de escrever; confirme o modelo de dados.
2. Modele o dado e gere a migration revisando o SQL que ela produz.
3. Implemente na camada certa (service → view → serializer) sem duplicar regra.
4. Escreva o teste junto: unit de serviço e teste de API do caminho feliz e do erro.
5. Rode a verificação e só então entregue:
   `ruff check . && ruff format --check . && mypy . && pytest -q && python manage.py makemigrations --check`
6. Deixe explícito o que mudou de contrato, de schema e o que precisa de migration em produção.

## Fontes

- Django: https://docs.djangoproject.com
- DRF: https://www.django-rest-framework.org
- Django Ninja: https://django-ninja.dev
- Ruff: https://docs.astral.sh/ruff
- pytest-django: https://pytest-django.readthedocs.io