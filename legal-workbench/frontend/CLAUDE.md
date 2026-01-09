# CLAUDE.md - Legal Workbench Frontend

Este modulo e o frontend React do Legal Workbench.

---

## Regras Especificas

### Stack
- React 18 + TypeScript
- Vite como bundler
- TanStack Router
- Zustand para estado
- MUI v7 para componentes

### Comandos Locais
```bash
cd legal-workbench/frontend
bun install
bun run dev      # Dev server
bun run build    # Build producao
bun run lint     # ESLint
```

### Antes de Modificar
1. Verificar se build passa: `bun run build`
2. Verificar lint: `bun run lint`
3. Testar no browser

### NUNCA (Especifico do Frontend)
- Usar `npm` ou `yarn` (apenas `bun`)
- Importar de `ccui-assistant/` (removido)
- Criar arquivos `.jsx` (usar `.tsx`)
- Hardcodar URLs de API (usar env vars)
- Modificar arquivos em `ferramentas/` durante tarefas de frontend

### Padrao de Componentes
```typescript
// Preferir: functional components com hooks
const Component: React.FC<Props> = ({ prop }) => {
  // hooks primeiro
  // handlers depois
  // return por ultimo
};
```

### Estrutura de Pastas
```
frontend/
├── src/
│   ├── components/    # Componentes reutilizaveis
│   ├── pages/         # Paginas/rotas
│   ├── services/      # APIs e servicos
│   ├── hooks/         # Custom hooks
│   ├── stores/        # Zustand stores
│   └── types/         # TypeScript types
├── public/
└── index.html
```

---

*Herdado de: legal-workbench/CLAUDE.md*
