# Investimentos — agentes, specs e aplicação local

Repositório que reúne **base de conhecimento, agentes especializados, especificações e a
aplicação local** para análise e apoio à decisão de investimentos no Brasil.

Não é um serviço hospedado. O projeto é voltado para uso pessoal no seu próprio
ambiente/local.

## O que tem aqui

- **Conhecimento e agentes:** regras, fórmulas e contexto que os agentes usam antes de
  responder ou calcular.
- **Specs:** o que pode ser afirmado sobre cada classe de ativo, como os dados entram no
  sistema e como o app deve se comportar.
- **Aplicação local:** backend Django + frontend React + Vite, para rodar na sua máquina
  sem depender de nuvem para funcionar.

## Primeiro contato

Se você é novo no projeto, comece por estes arquivos:

- [CONTEXT.md](CONTEXT.md) — escopo, objetivo, modelo técnico e o que está decidido
  (atualizado na entrevista de escopo).
- [AGENTS.md](AGENTS.md) — como os agentes, skills e specs se relacionam nesse repo.
- [specs/README.md](specs/README.md) — índice das especificações e como ler cada uma.

## Setup local

### Ambiente Python

O projeto usa **Python 3.14** (faixa permitida: `>=3.12,<3.15`).

1. Crie e ative um ambiente virtual.
2. Instale as dependências listadas em `pyproject.toml`.
3. Configure `DJANGO_SETTINGS_MODULE` para o ambiente desejado
   (ex.: `investimentos_project.settings.dev` no dia a dia).

### Banco

Por padrão, o projeto usa SQLite local. A troca por Postgres é questão de configuração,
não de alteração do schema.

### Backend

Para subir o backend em desenvolvimento:

```bash
python manage.py runserver
```

O backend expõe a API em `/api/v1/`.

Para rodar comandos administrativos, use `manage.py`, como:

```bash
python manage.py migrate
python manage.py ingest
python manage.py export_series
```

### Frontend

O frontend fica em `frontend/`. Rode o Vite com `npm`, `yarn` ou `pnpm`, conforme a
ferramenta de pacotes que você costuma usar no projeto. O front consome a API do backend
via HTTP.

### Sem rede

A aplicação foi pensada para continuar respondendo com o banco local quando não houver
conexão. A coleta externa de dados é separada e controlada.

## Fontes de dado e chaves

As chaves de API ficam fora do repositório.

- Veja os nomes das variáveis em [.env.example](.env.example).
- Crie seu `.env` local a partir desse exemplo.
- **Nunca commite o `.env` nem cole chaves no chat ou no código.**

## Estrutura de conhecimento

- Agentes e skills estão em `.agents/`.
- Especificações estão em `specs/`.
- Coletas de mercado datadas estão em `dados/`.

Os detalhes de como tudo se conecta estão em [AGENTS.md](AGENTS.md) e
[CONTEXT.md](CONTEXT.md).

## O que não fazer

- Não coloque chaves, tokens, CPF, dados de conta ou qualquer segredo no repositório.
- Não adicione fontes externas sem registrar licença e limite antes de automatizar.
- Sem recomendação personalizada de investimento — o sistema analisa e explica cenários;
  a decisão é do usuário.

## Próximo passo

Agora que o repositório está versionado, abre-se o desenvolvimento do **simulador**:
preço médio, custo total do aporte e yield on cost projetado, com a fórmula no backend e o
fluxo no frontend.

Veja os detalhes que já foram decididos em [CONTEXT.md](CONTEXT.md).
