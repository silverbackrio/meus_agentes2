# AGENTS.md

## O que é este projeto

Base de conhecimento, agentes especializados e specs para **análise de investimentos no
Brasil**, cobrindo todas as classes de ativos: renda fixa, renda variável (ações, BDRs),
fundos, ETFs e FIIs, previdência complementar, câmbio/derivativos e gestão de carteira.

Não há aplicação rodando aqui — este repositório é a **camada de conhecimento e de
especialização** que os agentes carregam antes de responder, calcular ou escrever sobre
investimentos. As skills de desenvolvimento em `.agents/skills/` servem para construir a
aplicação que usará esse conhecimento (backend e frontend).

## Estrutura

```
AGENTS.md                        ← este arquivo (contexto do projeto)
.agents/
  investimentos-orchestrator.ts  ← roteia a pergunta para o especialista certo
  renda-fixa.ts                  ← CDB, LCI/LCA, títulos públicos, debêntures, curva de juros
  renda-variavel.ts              ← ações, BDRs, fundamentos, valuation
  fundos-e-fiis.ts               ← fundos, ETFs, FIIs, custódia e taxas
  previdencia-e-tributos.ts      ← PGBL/VGBL, regimes, portabilidade, IR
  carteira-e-risco.ts            ← alocação, métricas de risco, derivativos, câmbio
  grill-with-docs.ts             ← entrevista de escopo, regra e decisão antes de qualquer código
  dev-backend.ts                 ← constrói API/model/teste em Python + Django
  dev-frontend.ts                ← constrói páginas e componentes em React + Vite
  infra-linux.ts                 ← nginx, cloudflared, gunicorn, segurança do sistema e rede
  pesquisador-de-mercado.ts      ← garimpa dado atual e histórico na web, com fonte e data
  fontes-de-dados.ts             ← descobre, configura e mantém API, chave e ingestão
  revisor-de-codigo.ts           ← gate antes de entregar alteração de código
  revisor-de-compliance.ts       ← gate antes de entregar resposta com regra tributária
  types/agent-definition.ts      ← tipos locais (o /init do Codebuff pode regerar)
  skills/
    renda-fixa-brasil/           ← instrumentos, marcadores e fórmulas de renda fixa
    tributacao-de-investimentos/ ← tabelas e regras de IR/IOF vigentes
    analise-de-acoes/            ← método de análise e valuation
    fundos-etfs-e-fiis/          ← comparar e escolher fundos/ETFs/FIIs
    previdencia-resgate/          ← decidir entre PGBL/VGBL, regimes e resgate
    alocacao-de-carteira/         ← perfil, alocação e rebalanceamento
    backend-python-django/        ← backend Python + Django: API, ORM, testes, deploy
    frontend-react-vite/          ← frontend React + Vite: componentes, dados, build
    infra-linux/                  ← servidor Ubuntu: proxy, túnel, app server, hardening
    pesquisa-de-mercado/          ← fontes, APIs públicas e modelo de dossiê datado
    fontes-de-dados-api/          ← catálogo de APIs, cotas, licenças e contrato de ingestão
specs/
  README.md                      ← índice e status das specs
  aplicacao.md                   ← apps, API, páginas e regras do que será construído
  dominio-e-fontes.md            ← modelo de domínio, fontes oficiais, datas de vigência
  ambiente-e-versoes.md          ← matriz Python/Django e quem escolhe o interpretador
  fontes-de-dados.md             ← origem, ingestão e banco histórico de séries
  renda-fixa.md
  acoes.md
  fundos-e-fiis.md
  previdencia.md
  carteira-e-risco.md
  compliance-e-avisos.md         ← limites do que os agentes podem afirmar
dados/
  README.md                      ← convenção das coletas de mercado (dossiês datados)
CONTEXT.md                       ← escopo, objetivo, modelo técnico e pendências (entrevista)
GLOSSARY.md                      ← termos de domínio e regras de negócio consolidadas
ARCHITECTURE_DECISIONS.md        ← decisões técnicas, trade-offs e supersedas
.env.example                     ← nomes das variáveis de API (o .env real é ignorado pelo git)
.gitignore                       ← mantém .env, banco e dados brutos fora do repositório
```

## Como usar

- **Agentes**: mencione o agente (`@Orquestrador de Investimentos`) ou deixe o roteador
  escolher. O orquestrador é o **gerente do time**: tem `spawnableAgents` para todos os
  especialistas (domínio, dev e revisores) e decide quem trabalha — incluindo responder direto,
  carregando a skill, quando não vale um spawn.
- **Economia de tokens**: quem gerencia é o orquestrador, e o protocolo dele está no próprio
  arquivo — responda direto quando puder, briefing de 3 a 6 linhas, uma rodada de despacho,
  devolutivo compacto, gate de revisão seletivo.
- **Skills**: `/skill:renda-fixa-brasil` carrega a skill na conversa; o agente também pode
  carregá-la automaticamente quando a descrição combinar com a tarefa.
- **Skills de desenvolvimento** (`backend-python-django`, `frontend-react-vite`) entram quando
  a tarefa for **construir a aplicação** — API, model, componente, rota ou build — e não quando
  for analisar um investimento. Antes de escrever código, leia `specs/aplicacao.md`: ela define
  estrutura, endpoints, telas e regras de implementação; a spec da classe define o cálculo.
- **Antes do código novo**: feature nova ou pedido ambíguo passa pelo `grill-with-docs`
  (`@Entrevistador de Escopo`) — entrevista de uma pergunta por vez que grava o consenso em
  `CONTEXT.md`, `GLOSSARY.md` e `ARCHITECTURE_DECISIONS.md`. Sem código antes disso.
- **Dado de mercado**: quem coleta é o `pesquisador-de-mercado`, que persiste em `dados/` com
  data e fonte. Quem lê um dossiê **não refaz a coleta** — só o delta desde a data do arquivo.
- **Banco histórico local**: quem **configura** fonte, chave e script é o `fontes-de-dados`; quem
  **consulta** lê primeiro o banco e só vai à rede pelo que falta. Regras e schema em
  `specs/fontes-de-dados.md`.
- **Specs**: leia a spec da classe de ativo **antes** de alterar as skills correspondentes.

## Ambiente do projeto

- **SO alvo**: **Ubuntu 26.04 LTS** + **Python 3.14** (faixa do projeto 3.12–3.14;
  `requires-python = ">=3.12,<3.15"`, pin em `.python-version`). Confira com `python3 --version`
  antes de trabalho de backend; se houver mais de uma versão disponível e não houver pin,
  **pergunte qual usar** e grave a escolha. Divergência se reporta, não se contorna em silêncio.
- **Desenvolvimento remoto**: quem escreve está em **Windows 10** e o código roda em **Linux
  remoto**. Nenhum agente assume caminho local do Windows, `localhost` como aplicação do usuário
  ou porta aberta sem confirmar onde o processo está rodando.

## Regras transversais (vale para todos os agentes e skills)

1. **Datae toda regra tributária ou regulatória.** Escreva "vigente em MM/AAAA" e cite a
   norma (lei, decreto, instrução CVM). Regra tributária sem data é regra errada.
2. **Valide na fonte oficial antes de afirmar.** Fontes-padrão: Receita Federal, Planalto,
   B3, CVM, BCB, SUSEP, ANBIMA, Tesouro Direto. Se não houver confirmação, diga que é
   incerto — nunca arredonde uma alíquota "para fechar".
3. **Números entram calculados, não estimados.** Fórmula + entrada explícita + resultado;
   taxa sempre com unidade (a.a., a.m., % do CDI) e data-base.
4. **Sem recomendação personalizada.** Analyse, compare e explique cenários; quem decide o
   aporte é o usuário. Ver `specs/compliance-e-avisos.md`.
5. **Português do Brasil**, com a terminologia local (selic, CDI, a.a., "cota", "carência").
6. **Não invente produto.** Só descreva instrumentos que existem e caibam na spec da classe.
7. **Dado de mercado muda**: cotações, taxas e spreads precisam de data-base e não podem ser
   memorizados — peça pesquisa na web quando o número for tempo-real.
8. **Código é modular, portátil e de dependência mínima**: fronteira única por módulo,
   dependência em uma direção, configuração por variável de ambiente, lógica de domínio como
   função pura reutilizável e toda dependência nova justificada — princípios P1–P5 e regra R13
   em `specs/aplicacao.md`.

## Convenções de escrita

- **Skill**: diretório = nome no frontmatter, só minúsculas/números/hífens, sem hífen
  inicial ou final e sem hífen duplo. `name` e `description` são obrigatórios; a `description`
  é o que o agente lê para decidir se carrega a skill — seja específico sobre **quando**
  invocar.
- **Agente**: arquivo em `.agents/`, export default de um `AgentDefinition`, com `id`,
  `displayName`, `toolNames`, `spawnableAgents`, `spawnerPrompt`, `systemPrompt` e
  `instructionsPrompt`. `spawnerPrompt` deve dizer **quando** os outros agentes te chamam.
- **Spec**: frontmatter com `status` (`proposta` | `ativa` | `obsoleta`) e `atualizada_em`.
  Uma spec `obsoleta` não deve ser usada como fonte por nenhum agente.

## O que não fazer

- Não edite uma skill de tributação sem atualizar a spec correspondente e a data de vigência.
- Não copie alíquotas de textos de terceiros sem checar a norma original.
- Não crie um novo agente para uma classe de ativo sem antes verificar se a spec já existe
  e se o orquestrador precisa rotear para ele.