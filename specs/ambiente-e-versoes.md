---
status: ativa
atualizada_em: 2026-10-27
---
# Spec: Ambiente e Versões

## Escopo

**Dentro:** qual Python, qual Django e qual ferramenta este projeto usa, onde isso fica declarado,
e quem decide quando existe mais de uma opção instalada.
**Fora:** instalação de sistema operacional, containers e compatibilidade de bibliotecas de
dados não listadas na matriz — estas são verificadas caso a caso na fonte.

## Modelo

| Campo | Onde vive | O que significa |
|---|---|---|
| `requires-python` | `pyproject.toml` | **contrato**: quais pythons o projeto suporta |
| `.python-version` | raiz do projeto | **pin**: qual interpretador o uv usa no dev local |
| `Django` | `pyproject.toml` + lockfile | versão efetiva do framework, já resolvida |
| ambiente real | `python3 --version`, `.venv` | o que de fato vai executar |
| disponíveis | `uv python list --only-installed` | opções existentes na máquina |

`requires-python` é faixa, não pin; `.python-version` é pin, não faixa. Uma não substitui a outra.

## Matriz — Django × Python (outubro de 2026)

| Django | Python declarado | Situação em 10/2026 | Fim de suporte |
|---|---|---|---|
| 4.2 LTS | 3.8–3.12 (3.12 a partir da 4.2.8) | **sem suporte** | 04/2026 |
| 5.1 | 3.10–3.13 (3.13 a partir da 5.1.3) | **sem suporte** | 12/2025 |
| 5.2 LTS | 3.10–3.14 (3.14 a partir da 5.2.8) | extended | 04/2028 |
| 6.0 | 3.12–3.14 | extended | 04/2027 |
| 6.1 | 3.12–3.15 (3.15 a partir da 6.1.3) | **mainstream** | 12/2027 |

## Matriz — Python (outubro de 2026)

| Python | Fase | Fim de suporte |
|---|---|---|
| 3.12 | security | 10/2028 |
| 3.13 | security | 10/2029 |
| 3.14 | bugfix | 10/2030 |
| 3.15 | bugfix | 10/2031 |

**Combinções válidas a partir da 3.12** (faixa do projeto):
`3.12 + Django 6.0/6.1 ou 5.2 LTS` · `3.13 + 5.2/6.0/6.1` · `3.14 + 5.2.8+/6.0/6.1` ·
`3.15 apenas com Django 6.1.3+` (fora da faixa atual do projeto).

**Padrão do projeto:** Python 3.14 + Django 5.2 LTS (compatíveis de 5.2.8 em diante, suporte
estendido até 04/2028). Django 6.1 é opção válida para quem quer a série mainstream (até
12/2027), com a mesma faixa de Python.

## Matriz — ecossistema (outubro de 2026)

| Ferramenta | Declaração oficial |
|---|---|
| DRF 3.18.x | Python 3.10–3.15; Django 5.2, 6.0, 6.1 (removeu 4.2, 5.0 e 5.1) |
| Django Ninja 1.x | `requires-python >=3.7`, `Django >=3.1` **sem teto declarado**; classifiers até 6.1 |
| pytest-django 4.14.x | Python ≥3.10 (3.14 oficial); Django 5.2 e 6.0 oficiais |
| mypy | precisa de **Python 3.10+ para rodar** |
| gunicorn | Python 3.10+ |
| ruff | analisa código-alvo **3.7+** — não exige rodar nessa versão |

## Regras

**R1.** O projeto declara `requires-python = ">=3.12,<3.15"` (aceita 3.12, 3.13 e 3.14) e pin
`.python-version` na linha de desenvolvimento (**3.14**).

**R2.** Nunca presumir a versão. Ordem de detecção: `.python-version` → `requires-python` →
`python3 --version` do ambiente → `uv python list --only-installed`.

**R3.** Sempre **informar** a versão detectada na resposta. **Perguntar qual usar** quando houver
mais de uma opção instalada e pin + ambiente não convergirem. Proibido escolher em silêncio e
proibido trocar a versão sozinho.

**R4.** Depois da escolha, gravar `.python-version` (e `requires-python` se estiver em aberto) —
a pergunta acontece **uma vez por projeto**, não a cada tarefa.

**R5.** Django fora de suporte não entra em projeto novo: 4.2 e 5.1 estão EOL desde 04/2026 e
12/2025. Django LTS só com a data de fim na resposta.

**R6.** Compatibilidade é conferida nas release notes **antes de afirmar**; a matriz acima é
datada em 10/2026 e precisa de reconferência a cada release nova do Django ou do Python.

**R7.** Divergência entre pin e ambiente real (ex.: pin 3.14, máquina com 3.12) é **reportada e
corrigida com `uv python install 3.14` + `uv python pin 3.14`** — nunca silenciada, nunca
contornada com downgrade.

**R8.** O servidor alvo (Ubuntu 26.04) é verificado à parte: pode ter outra versão que a local;
a resposta declara a das duas, quando forem diferentes.

**R9.** Se o projeto declara faixa, o CI testa a **faixa** (3.12, 3.13, 3.14), não só o pin local
— pin local não prova compatibilidade.

## Critérios de aceite

- [ ] Toda tarefa de backend declara qual Python foi detectado e qual será usado.
- [ ] A escolha foi perguntada apenas quando havia ambiguidade, e ficou gravada depois.
- [ ] Nenhuma troca silenciosa de versão de interpretador ou do Django.
- [ ] Matriz datada e com a release note oficial como fonte.
- [ ] Django sempre em série com suporte, com a data de fim citada.
- [ ] Ambiente local e remoto reportados quando divergentes.

## Lacunas

- **pytest-django × Django 6.1**: suporte oficial confirmado para 5.2 e 6.0; para 6.1, verificar
  o changelog antes de afirmar.
- **Django Ninja**: não declara teto de Django — a compatibilidade por combinação não é garantia,
  e a página inicial traz texto mais antigo que o `pyproject.toml`.
- **EOL do Python**: publicado como mês/ano; os PEPs dizem "aproximadamente" a data.
- Novas séries do Django mudam a matriz; quem altera a matriz altera primeiro esta spec.

## Fontes

- https://www.djangoproject.com/download/
- https://docs.djangoproject.com/en/6.1/releases/6.1/ · /6.0/releases/6.0/ · /5.2/releases/5.2/
- https://www.python.org/downloads/
- https://www.django-rest-framework.org/community/release-notes/
- https://pytest-django.readthedocs.io/en/latest/changelog.html
- https://docs.astral.sh/uv/concepts/python-versions/