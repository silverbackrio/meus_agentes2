/**
 * Tipos locais para escrever os agentes de `.agents/*.ts`.
 *
 * O `/init` do Codebuff gera esta mesma pasta de tipos. Se você rodar o comando, este
 * arquivo pode ser substituído pelo oficial — os agentes continuam válidos, porque o
 * import é `import type` e não muda o que roda em runtime.
 */

export type AgentDefinition = {
  /** Identificador único e estável, em kebab-case. É o que aparece em `spawnableAgents`. */
  id: string
  /** Nome exibido na interface e usado nas menções `@Nome do Agente`. */
  displayName: string
  /** Publisher, apenas quando o agente for publicado na store do Codebuff. */
  publisher?: string
  /** Modelo, ex.: 'anthropic/claude-sonnet-4.5'. Omita para herdar o padrão do projeto. */
  model?: string
  /** Ferramentas liberadas para este agente. */
  toolNames: string[]
  /** Agentes que este pode chamar: locais pelo `id`, da store como `publisher/id@versão`. */
  spawnableAgents?: string[]
  /** Quando os outros agentes devem te chamar — é o texto que o orquestrador usa para rotear. */
  spawnerPrompt?: string
  /** Quem o agente é: papel, especialidade, limites e padrão de qualidade. */
  systemPrompt: string
  /** O que o agente faz, passo a passo. */
  instructionsPrompt?: string
  /** Controle programático do passo, quando a tarefa for determinística demais para prompt. */
  handleSteps?: () => Generator<unknown, void, unknown>
}