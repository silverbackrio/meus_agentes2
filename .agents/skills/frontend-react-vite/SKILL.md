---
name: frontend-react-vite
description: "Desenvolva frontend em React com Vite e TypeScript: componentes e hooks, data fetching com TanStack Query, roteamento com React Router, formulários, estado de UI, estilos, code splitting, acessibilidade, testes com Vitest e Testing Library e configuração do build. Use quando a tarefa envolver criar ou alterar componente, página, hook, store, rota, chamada de API no front ou build do frontend."
metadata:
  category: desenvolvimento
  linguagem: typescript
  framework: react
  build: vite
  atualizado_em: 2026-10
---
# Frontend: React + Vite

Guia para SPA em React com Vite e TypeScript, do componente ao build, com verificação antes de
entregar.

## Quando usar

- Criar ou alterar componente, página, hook, rota ou chamada de API.
- Decidir onde vive o estado, como tratar dado assíncrono ou acessibilidade.
- Diagnóstico de build, code splitting, re-render ou teste quebrado.

## Stack de referência (outubro de 2026)

| Peça | Escolha | Nota |
|---|---|---|
| React | **19.3.x** | Actions, `useActionState`, `useOptimistic`, `useFormStatus`, `use`, `ref` como prop; 19.2 trouxe `<Activity>` e `useEffectEvent` |
| Build | **Vite 8** (Rolldown como bundler unificado) | exige **Node 20.19+ ou 22.12+**; revisar guia de migração se a config usar opções antigas de esbuild/Rollup |
| Plugin | `@vitejs/plugin-react` major **6** | transform com Oxc, sem Babel por padrão |
| Linguagem | TypeScript em modo estrito | |
| Dado remoto | **TanStack Query v5** | cache, revalidação e estado de servidor |
| Rota | **React Router v7** | loaders/actions quando fizer sentido |
| Teste | **Vitest** + `@testing-library/react` + `user-event` | reusa a configuração do Vite |

**Server Components não entram aqui:** RSC é capacidade de framework/bundler, não vem "de
graça" com React. Em SPA com Vite, use React no cliente e ignore RSC — adotar por novidade custa
complexidade.

> Alternativa de stack: **Vue 3 + Vite** (`@vitejs/plugin-vue`) usa exatamente o mesmo tooling.
> Se o projeto escolher Vue, criar a skill `frontend-vue-vite` em vez de adaptar esta por fora.

## Estrutura

```
src/
  app/            # providers, router, queryClient, entry
  routes/         # páginas, uma por rota
  features/<dominio>/
    components/  hooks/  api/  types.ts
  shared/         # ui/, lib/, hooks/ genéricos
  test/           # setup, helpers
```

## Onde vive o estado — hierarquia de decisão

1. **Props** → 2. **estado local** (`useState`/`useReducer`) → 3. **cache de servidor**
   (TanStack Query) → 4. **contexto** para estado verdadeiramente global (tema, sessão) →
5. **store** (Zustand ou equivalente) só para estado de UI complexo e fora do servidor.

Nunca copie dado do servidor para `useState`: quem guarda dado assíncrono é a query.

## Padrões de componente

- Componente pequeno e semântico; **funções puras** quando não houver efeito.
- Separar container (dados/efeitos) de presentational (markup/estilo).
- `key` sempre estável e de domínio — nunca índice em lista que reordena.
- Efeitos só para sincronizar com sistemas externos; dados assíncronos vão para a query, não
  para `useEffect`.
- `useMemo`/`useCallback`/`React.memo` apenas com medição de problema — otimização às cegas
  piora legibilidade sem ganho.
- Erros: `ErrorBoundary` por rota; estado de vazio, carregando e erro é **padrão**, não extra.

## Data fetching

```ts
useQuery({ queryKey: ['recurso', id], queryFn: () => api.get(id) })
useMutation({ mutationFn: api.create, onSuccess: () => invalidate(['recurso']) })
```
- Chave de query por identidade de domínio; invalidação no `onSuccess`, não `refetch` manual.
- Retry/backoff e `staleTime` definidos no `queryClient`, não espalhados por componente.
- Erro de rede vira estado da query com mensagem e ação de retry — nunca `alert`.

## Roteamento e formulários

- Uma rota por página; lazy por rota para dividir o bundle.
- Formulário: validação no submit com mensagem junto ao campo, `aria-invalid`, estado de
  enviando/sucesso/erro controlado fora do input; React 19 permite Actions com
  `useActionState`/`useFormStatus`.

## Performance

- Medir com as *trilhas* do React antes de otimizar.
- Dividir bundle por rota e carregar biblioteca pesada sob demanda.
- Evitar re-render: props estáveis, estado o mais perto possível do consumo.
- Imagem moderna (`loading="lazy"`, dimensões declaradas) e memoizar cálculo caro.

## Acessibilidade

- Landmarks e headings em ordem, foco visível, alvo de toque ≥ 44px.
- Controle semântico: `button` para ação, `a` para navegação, `label` associado ao input.
- Teclado completo: navegação, `Esc` fecha, foco gerenciado em modal.
- Contraste e `prefers-reduced-motion`; texto alternativo em imagem informativa.

## Testes

```
src/features/<dominio>/__tests__/  componente.test.tsx   # comportamento visível
src/shared/lib/                    regra pura            # unit de lógica
```
- Testar como usuário: papel, interação, resultado visível — não implementação interna.
- Dado de rede mockado no nível da função `api`, não do `fetch`.
- Comandos: `npx vitest run`, `npx tsc --noEmit`, `npm run build`.

## Build e configuração

- `vite.config.ts` com plugins `react()` e alias `@/`; env só com prefixo `VITE_` e nada de
  segredo no bundle.
- Variáveis de ambiente lidas em um único módulo; trocar API base não pode vazar para o
  componente.
- Produção: `npm run build` limpo e `vite preview` para conferir o bundle.
- Migração de Vite maior: revisar opções de esbuild/Rollup e plugins antes de subir.

## Instruções

1. Confirme a rota/feature e o contrato da API que consome.
2. Escreva tipos das respostas primeiro (`types.ts`) e só então o componente.
3. Implemente com a hierarquia de estado acima; dado de servidor vive na query.
4. Trate os quatro estados: carregando, vazio, erro, sucesso.
5. Rode a verificação antes de entregar: `npx tsc --noEmit && npx vitest run && npm run build`.
6. Deixe explícito o que mudou de contrato, de rota e de bundle.

## Fontes

- React: https://react.dev
- Vite: https://vite.dev
- TanStack Query: https://tanstack.com/query/latest
- React Router: https://reactrouter.com
- Vitest: https://vitest.dev
- Testing Library: https://testing-library.com/docs/react-testing-library/intro