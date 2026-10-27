---
status: ativa
atualizada_em: 2026-10-27
responsavel: projeto
---
# Specs

Índice das especificações deste projeto. A spec é a **autoridade final** sobre o que os agentes
podem afirmar sobre cada classe de ativo: skill e agente implementam a spec; nunca a contradizem.

## Status

| Spec | Status | Atualizada em | Associa |
|---|---|---|---|
| [aplicacao](aplicacao.md) | ativa | 2026-10-27 | agente `dev-backend`, agente `dev-frontend` |
| [dominio-e-fontes](dominio-e-fontes.md) | ativa | 2026-10-27 | todas as skills |
| [fontes-de-dados](fontes-de-dados.md) | ativa | 2026-10-27 | `fontes-de-dados-api`, agente `fontes-de-dados` |
| [ambiente-e-versoes](ambiente-e-versoes.md) | ativa | 2026-10-27 | agente `dev-backend`, skill `backend-python-django` |
| [renda-fixa](renda-fixa.md) | ativa | 2026-10-27 | `renda-fixa-brasil`, agente `renda-fixa` |
| [acoes](acoes.md) | ativa | 2026-10-27 | `analise-de-acoes`, agente `renda-variavel` |
| [fundos-e-fiis](fundos-e-fiis.md) | ativa | 2026-10-27 | `fundos-etfs-e-fiis`, agente `fundos-e-fiis` |
| [previdencia](previdencia.md) | ativa | 2026-10-27 | `previdencia-resgate`, agente `previdencia-e-tributos` |
| [carteira-e-risco](carteira-e-risco.md) | ativa | 2026-10-27 | `alocacao-de-carteira`, agente `carteira-e-risco` |
| [compliance-e-avisos](compliance-e-avisos.md) | ativa | 2026-10-27 | todas as skills e agentes |

## Como ler

1. Antes de alterar uma skill, leia a spec da classe de ativo correspondente.
2. Antes de escrever código da aplicação, leia `aplicacao.md` — ela manda na estrutura; a spec
   da classe manda no cálculo.
3. Uma spec `obsoleta` não pode ser usada como fonte por nenhum agente — substitua e marque o
   status antes de seguir em frente.
4. Uma spec `proposta` é válida apenas como rascunho; não a cite como regra em resposta ao
   usuário.

## O que uma spec contém

```
frontmatter      status + atualizada_em
escopo           o que está dentro e o que ficou de fora
modelo           entidades, campos e unidades usadas nos cálculos
regras           o que pode ser afirmado, com norma e data de vigência
cálculos         fórmulas obrigatórias e critérios de comparação
aceite           o que precisa ser verdade para a resposta estar pronta
lacunas          o que é incerto e não pode ser afirmado sem pesquisa
```

## Ciclo de atualização

1. Mudou a norma → pesquise a fonte oficial e anote a URL e a data.
2. Atualize a **spec** primeiro, com o `atualizada_em` novo.
3. Atualize a **skill** correspondente e a data no frontmatter dela.
4. Revise o **agente** se a mudança alterar o fluxo de trabalho.
5. Se a norma foi revogada sem substituta, marque a spec como `obsoleta` e registre o motivo na
   seção "lacunas".