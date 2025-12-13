# STJ Jurisprudence Lab - React PoC

Prova de conceito do módulo STJ (Superior Tribunal de Justiça) do Legal Workbench, implementado em React 18 + TypeScript.

## Características

### Estética Terminal/Hacker
- Background: #0a0f1a (near-black blue)
- Texto: #e2e8f0 (cool gray)
- Accent 1: #f59e0b (amber/orange) - ações e destaques
- Accent 2: #dc2626 (deep red) - warnings e desprovimento
- Accent 3: #22c55e (green) - success e provimento
- Typography: Monospace para dados, sans-serif limpo para labels

### Funcionalidades Implementadas

#### 1. Query Builder Inteligente
- **Dropdown de Domínio Jurídico**: Direito Civil, Penal, Tributário, Administrativo
- **Multi-select de Palavras-Gatilho**: Dano Moral, Lucros Cessantes, Habeas Corpus, ICMS, etc.
- **Toggle "Somente Acórdãos"**: Com badge de warning quando ativo
- **Preview SQL ao Vivo**: Atualiza em tempo real conforme os filtros são alterados
- **Templates Rápidos**: Botões para aplicar filtros pré-configurados
  - Divergência entre Turmas
  - Recursos Repetitivos
  - Súmulas Recentes

#### 2. Exibição de Resultados
- Cards com informações detalhadas de cada processo
- Badges de outcome (texto, não emoji):
  - PROVIDO (verde)
  - DESPROVIDO (vermelho)
  - PARCIAL (amarelo)
- Loading states e error handling
- Empty states informativos

### Stack Tecnológica

- **React 18**: Hooks, Context, Suspense
- **TypeScript**: Type safety completo
- **Vite**: Build tool rápido e moderno
- **Tailwind CSS**: Utility-first styling com tema customizado
- **TanStack Query**: Data fetching, caching e state management
- **TanStack Query Devtools**: Debug de queries em desenvolvimento

## Instalação e Execução

### Pré-requisitos
- Node.js 18+ ou Bun 1.3+

### Passos para Executar

```bash
# 1. Entre no diretório do projeto
cd /home/user/Claude-Code-Projetos/legal-workbench/poc-react-stj

# 2. Instale as dependências
npm install
# ou
bun install

# 3. Execute o servidor de desenvolvimento
npm run dev
# ou
bun run dev
```

O aplicativo estará disponível em `http://localhost:3000`

### Scripts Disponíveis

```bash
npm run dev      # Inicia o servidor de desenvolvimento
npm run build    # Cria build de produção
npm run preview  # Preview do build de produção
npm run lint     # Executa o linter
```

## Estrutura do Projeto

```
src/
├── components/
│   ├── STJQueryBuilder.tsx      # Componente principal
│   ├── SQLPreviewPanel.tsx      # Painel de preview SQL
│   ├── JurisprudenceResultCard.tsx  # Card de resultado
│   └── OutcomeBadge.tsx         # Badge de outcome
├── hooks/
│   └── useJurisprudenceQuery.ts # Hooks de TanStack Query
├── types/
│   └── index.ts                 # TypeScript types
├── utils/
│   └── mockData.ts              # Mock data e helpers
├── App.tsx                      # Root component
├── main.tsx                     # Entry point
└── index.css                    # Global styles + Tailwind

```

## Dados de Mock

O projeto usa dados simulados para demonstrar a funcionalidade. Em produção, os hooks em `src/hooks/useJurisprudenceQuery.ts` seriam conectados a uma API real.

### Exemplos de Resultados Mock

- REsp 1.234.567/SP - Dano Moral (PROVIDO)
- REsp 1.345.678/RJ - ICMS (DESPROVIDO)
- REsp 1.456.789/MG - Lucros Cessantes (PARCIAL)
- HC 987.654/BA - Habeas Corpus (PROVIDO)
- REsp 1.567.890/RS - Prescrição (DESPROVIDO)

## Próximos Passos (Produção)

### 1. Backend Integration
- Substituir mock data por chamadas API reais
- Implementar autenticação e autorização
- Rate limiting e caching server-side

### 2. Testes
- Unit tests com Jest + React Testing Library
- E2E tests com Playwright
- Testes de acessibilidade

### 3. Performance
- Code splitting por rota
- Lazy loading de componentes
- Virtualização de listas longas

### 4. Acessibilidade
- ARIA labels completos
- Navegação por teclado
- Screen reader support
- WCAG 2.1 AA compliance

### 5. Features Adicionais
- Exportação de resultados (PDF, CSV)
- Salvar queries favoritas
- Histórico de buscas
- Filtros avançados (data, órgão julgador, etc.)

## Deployment Checklist

- [ ] Remover console.logs de debug
- [ ] Configurar variáveis de ambiente (.env)
- [ ] Otimizar bundle size
- [ ] Configurar CSP headers
- [ ] Implementar error tracking (Sentry)
- [ ] Configurar analytics
- [ ] Testes de performance (Lighthouse)
- [ ] Review de segurança
- [ ] Documentação de API
- [ ] Smoke tests em produção

## Licença

Projeto interno - Legal Workbench
