# TAURI + CLAUDE CODE: Playbook Completo

**Versao:** 1.0
**Data:** 2026-01-20
**Objetivo:** Maximizar eficacia de desenvolvimento Tauri assistido por LLM

---

## Sumario Executivo

Este playbook consolida:
- Pesquisa sobre capacidades LLM com Tauri
- Tooling disponivel e como implementa-lo
- Skills e subagentes customizados
- Guardrails contra simplificacao/downgrading
- Best practices para desenvolvimento

---

# PARTE 1: CONTEXTO E FUNDAMENTOS

## 1.1 O Problema Central

### Matthew Effect em Frameworks

```
Tecnologias populares → mais dados de treino → melhor suporte AI → mais adocao
```

| Stack | Dados de Treino | Capacidade LLM |
|-------|-----------------|----------------|
| React/Tailwind | Abundante (10+ anos) | Excelente |
| Electron | Alto (VSCode, Slack, Discord) | Bom |
| **Tauri** | Limitado (framework novo) | Requer compensacao |

### Downgrading Defensivo

Quando LLMs nao tem confianca em uma stack, tendem a:
1. Simplificar frontend para evitar IPC complexo
2. Usar fallbacks web quando APIs nativas estao disponiveis
3. Evitar features que exigiriam Rust customizado
4. Otimizar para "funciona" em vez de "excelente"

**Resultado:** App Tauri que e apenas um site em WebView, sem vantagens nativas.

## 1.2 Estado Atual do Tauri (2025-2026)

| Aspecto | Status |
|---------|--------|
| Versao estavel | 2.9.5 |
| Plataformas | Windows, macOS, Linux, Android, iOS |
| GitHub Stars | 82.8k+ |
| Discord Members | 21.7k+ |
| Empresas usando | ~90 (Cloudflare, ABBYY, etc.) |
| Security Audit | Radically Open Security (NLNet/NGI) |

### Vantagens Tecnicas

| Metrica | Electron | Tauri |
|---------|----------|-------|
| Bundle size | 150-200MB | 3-10MB |
| RAM usage | ~200MB+ | ~30-50MB |
| Startup time | 2-5s | <1s |
| Backend | Node.js (JS) | Rust (nativo) |

---

# PARTE 2: TOOLING DISPONIVEL

## 2.1 Recursos Oficiais para LLMs

### llms.txt Oficial

```
URL: https://tauri.app/llms.txt
```

Conteudo estruturado em markdown com:
- Overview do projeto
- Links para documentacao principal
- Estrutura de conceitos
- Guias de desenvolvimento

**Como usar:** Injetar no inicio de sessoes ou como context file.

### Claude Skills para Tauri

```
URL: https://claude-plugins.dev/skills/@delorenj/skills/tauri
```

9 categorias de documentacao estruturada:
1. `core_concepts.md` - Arquitetura, IPC, multi-processo
2. `development.md` - Debugging, DevTools
3. `distribution.md` - Code signing, CI/CD
4. `getting_started.md` - Inicializacao, tutoriais
5. `plugins.md` - Mobile patterns, lifecycle
6. `reference.md` - API docs, config schema
7. `security.md` - CSP, IPC security, permissions
8. `tutorials.md` - Implementacoes passo-a-passo
9. `other.md` - Topicos avancados

### Cursor Rules

Disponivel em `awesome-cursorrules`:
- Regras especificas para Tauri + Svelte + TypeScript
- Adaptavel para React

## 2.2 Templates Recomendados

| Template | Features | Uso Recomendado |
|----------|----------|-----------------|
| **dannysmith/tauri-template** | Tauri v2 + React 19 + Claude Code integration + tauri-specta | Projetos com Claude Code |
| **create-tauri-react** | Vite + React + Tailwind + shadcn/ui + bulletproof-react | Projetos com design system |
| **Official create-tauri-app** | Multi-framework (Vue, Svelte, React, etc.) | Projetos vanilla |

### Template Recomendado: dannysmith/tauri-template

```bash
git clone https://github.com/dannysmith/tauri-template my-project
cd my-project
bun install
```

**Inclui:**
- Comandos Claude Code (`/check`, `/cleanup`)
- Agents especializados
- tauri-specta (type-safe IPC)
- Estrutura de projeto organizada

---

# PARTE 3: IMPLEMENTACAO DO TOOLING

## 3.1 Estrutura de Projeto Tauri + Claude Code

```
my-tauri-app/
├── .claude/
│   ├── skills/
│   │   ├── tauri-core.md           # Conceitos fundamentais
│   │   ├── tauri-ipc.md            # Padroes de IPC
│   │   ├── tauri-frontend.md       # Regras de frontend
│   │   └── tauri-native-apis.md    # APIs nativas obrigatorias
│   ├── agents/
│   │   ├── tauri-frontend-dev.md   # Subagente frontend
│   │   ├── tauri-rust-dev.md       # Subagente Rust
│   │   └── tauri-reviewer.md       # Subagente de review
│   └── hooks/
│       └── pre-commit-tauri.js     # Validacao automatica
├── CLAUDE.md                        # Regras globais do projeto
├── ARCHITECTURE.md                  # North Star arquitetural
├── src/                             # Frontend React/TS
├── src-tauri/                       # Backend Rust
│   ├── src/
│   │   ├── main.rs
│   │   ├── lib.rs
│   │   └── commands/                # Tauri commands organizados
│   ├── Cargo.toml
│   └── tauri.conf.json
├── package.json
└── vite.config.ts
```

## 3.2 CLAUDE.md para Projetos Tauri

```markdown
# CLAUDE.md - Projeto Tauri

## Stack
- **Frontend:** React 19 + TypeScript + Vite + Tailwind
- **Backend:** Rust (Tauri 2.x)
- **IPC:** tauri-specta (type-safe)

## Regras Criticas

### 1. NUNCA Simplificar Preventivamente
O objetivo e criar um app desktop NATIVO, nao um site em WebView.
Toda feature deve aproveitar capacidades nativas quando disponiveis.

### 2. Hierarquia de Implementacao
1. **Tauri plugin/API** → SEMPRE preferido
2. **Rust command custom** → Se plugin nao existe
3. **Web API** → APENAS se 1 e 2 impossiveis (com justificativa)

### 3. APIs Nativas Obrigatorias

| Necessidade | API Tauri | Web Fallback Proibido |
|-------------|-----------|----------------------|
| Selecao de arquivo | `dialog.open()` | `<input type="file">` |
| Salvar arquivo | `dialog.save()` + `fs.writeFile()` | Download link |
| Notificacoes | `notification` plugin | `alert()` ou toast web |
| Clipboard | `clipboard` plugin | `navigator.clipboard` |
| Abrir links | `shell.open()` | `window.open()` |
| Persistencia | `store` plugin | `localStorage` |

### 4. Convencoes de Codigo

**Rust (src-tauri/):**
- snake_case para funcoes e variaveis
- Commands sempre retornam `Result<T, E>`
- Errors implementam `serde::Serialize`
- Use `thiserror` para error types

**TypeScript (src/):**
- camelCase para funcoes e variaveis
- Types gerados por tauri-specta
- Nunca usar `any` em chamadas IPC

### 5. IPC Patterns

```typescript
// CORRETO: Type-safe com tauri-specta
import { commands } from './bindings';
const result = await commands.processAudio(audioData);

// INCORRETO: invoke manual sem types
const result = await invoke('process_audio', { data: audioData });
```

### 6. Styling
- Usar capacidades CSS completas (backdrop-filter, gradients complexos)
- Nao simplificar por "compatibilidade" (Tauri usa WebView moderno)
- Aproveitar que e desktop (hover states, keyboard shortcuts, etc.)

## Contexto Adicional

Para entender Tauri completamente, consultar:
- Skills em `.claude/skills/tauri-*.md`
- Documentacao oficial: https://tauri.app/llms.txt

## Erros Comuns a Evitar

| Erro | Consequencia | Prevencao |
|------|--------------|-----------|
| Usar `<input type="file">` | Perde integracao nativa | Sempre `dialog.open()` |
| localStorage para dados | Perde criptografia/sync | Sempre `store` plugin |
| alert() para notificacoes | Bloqueia UI, nao nativo | Sempre `notification` plugin |
| Ignorar keyboard shortcuts | UX inferior a apps nativos | Implementar shortcuts |
```

## 3.3 ARCHITECTURE.md para Projetos Tauri

```markdown
# ARCHITECTURE.md - North Star

## Visao
App desktop/mobile NATIVO que aproveita 100% das capacidades Tauri.
NAO e um site empacotado em WebView.

## Principios Arquiteturais

### 1. Native-First
Toda feature deve primeiro considerar implementacao nativa.
Web fallback so e aceito com justificativa documentada.

### 2. Type-Safe IPC
Toda comunicacao frontend-backend usa tauri-specta.
Nenhum `invoke()` manual sem types.

### 3. Rust para Computacao Pesada
Processamento de arquivos, audio, dados → Rust.
Frontend apenas para UI e orquestracao.

### 4. Security by Default
- CSP configurado restritivamente
- Permissions granulares por API
- Nenhum `dangerousRemoteDomainIpcAccess`

## Estrutura de Camadas

```
┌─────────────────────────────────────┐
│           UI (React/TS)             │
│  - Componentes visuais              │
│  - Estado local (Zustand/Jotai)     │
│  - Event handlers                   │
└─────────────────┬───────────────────┘
                  │ IPC (type-safe)
┌─────────────────▼───────────────────┐
│         Commands (Rust)             │
│  - Validacao de input               │
│  - Orquestracao de services         │
│  - Error handling                   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│         Services (Rust)             │
│  - Logica de negocio                │
│  - Acesso a filesystem              │
│  - Processamento de dados           │
└─────────────────────────────────────┘
```

## Decisoes Arquiteturais

| Decisao | Escolha | Alternativa Rejeitada | Motivo |
|---------|---------|----------------------|--------|
| State management | Zustand | Redux | Simplicidade, menos boilerplate |
| IPC types | tauri-specta | Manual | Type-safety garantida |
| Styling | Tailwind | CSS-in-JS | Performance, DX |
| File handling | Rust fs | Web FileReader | Performance, capacidades |
```

---

# PARTE 4: SKILLS CUSTOMIZADAS

## 4.1 Skill: tauri-core.md

```markdown
---
trigger: keywords
keywords: [tauri, desktop app, native app, rust frontend]
description: Conceitos fundamentais de Tauri para desenvolvimento
---

# Tauri Core Concepts

## O que e Tauri
Framework para criar apps desktop/mobile usando web technologies (HTML/CSS/JS)
com backend em Rust. Diferente de Electron, usa WebView do sistema (nao Chromium).

## Arquitetura

```
Frontend (WebView)          Backend (Rust)
┌──────────────┐           ┌──────────────┐
│   React/TS   │◄─────────►│    Tauri     │
│              │   IPC     │    Core      │
│  UI/Events   │           │   Commands   │
└──────────────┘           └──────────────┘
```

## IPC (Inter-Process Communication)

### Definindo Commands (Rust)
```rust
#[tauri::command]
fn greet(name: String) -> String {
    format!("Hello, {}!", name)
}

// Com error handling
#[tauri::command]
fn read_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path)
        .map_err(|e| e.to_string())
}
```

### Chamando Commands (TypeScript)
```typescript
import { invoke } from '@tauri-apps/api/core';

// Sem type safety (evitar)
const greeting = await invoke<string>('greet', { name: 'World' });

// Com tauri-specta (preferido)
import { commands } from './bindings';
const greeting = await commands.greet('World');
```

## Plugins Oficiais Principais

| Plugin | Funcionalidade |
|--------|---------------|
| `@tauri-apps/plugin-dialog` | Dialogos nativos (open, save, message) |
| `@tauri-apps/plugin-fs` | Filesystem access |
| `@tauri-apps/plugin-notification` | Notificacoes do sistema |
| `@tauri-apps/plugin-clipboard` | Clipboard read/write |
| `@tauri-apps/plugin-shell` | Executar comandos, abrir URLs |
| `@tauri-apps/plugin-store` | Persistencia key-value |

## Configuracao (tauri.conf.json)

```json
{
  "productName": "My App",
  "version": "0.1.0",
  "identifier": "com.mycompany.myapp",
  "build": {
    "frontendDist": "../dist"
  },
  "app": {
    "withGlobalTauri": false,
    "security": {
      "csp": "default-src 'self'; script-src 'self'"
    }
  }
}
```
```

## 4.2 Skill: tauri-native-apis.md

```markdown
---
trigger: keywords
keywords: [file picker, save file, notification, clipboard, tauri api]
description: APIs nativas do Tauri - uso obrigatorio
---

# Tauri Native APIs - Referencia Obrigatoria

## REGRA FUNDAMENTAL
> Sempre usar APIs nativas. Web fallback so com justificativa.

## Dialog (Arquivos)

### Selecionar Arquivo
```typescript
import { open } from '@tauri-apps/plugin-dialog';

const path = await open({
  multiple: false,
  filters: [{
    name: 'Audio',
    extensions: ['wav', 'mp3', 'webm']
  }]
});
```

**PROIBIDO:** `<input type="file">`

### Salvar Arquivo
```typescript
import { save } from '@tauri-apps/plugin-dialog';
import { writeFile } from '@tauri-apps/plugin-fs';

const path = await save({
  filters: [{ name: 'Text', extensions: ['txt'] }]
});
if (path) {
  await writeFile(path, content);
}
```

**PROIBIDO:** Download via `<a href="data:...">`

## Filesystem

```typescript
import {
  readFile,
  writeFile,
  readDir,
  createDir,
  exists
} from '@tauri-apps/plugin-fs';

// Ler arquivo
const content = await readFile(path);

// Escrever arquivo
await writeFile(path, new TextEncoder().encode(text));

// Listar diretorio
const entries = await readDir(path);
```

**PROIBIDO:** FileReader API do browser

## Notifications

```typescript
import {
  sendNotification,
  requestPermission,
  isPermissionGranted
} from '@tauri-apps/plugin-notification';

// Verificar/solicitar permissao
let permitted = await isPermissionGranted();
if (!permitted) {
  const permission = await requestPermission();
  permitted = permission === 'granted';
}

// Enviar notificacao
if (permitted) {
  sendNotification({
    title: 'Processo Concluido',
    body: 'Arquivo salvo com sucesso!'
  });
}
```

**PROIBIDO:** `alert()`, toasts web-only

## Clipboard

```typescript
import { writeText, readText } from '@tauri-apps/plugin-clipboard-manager';

// Copiar
await writeText('Hello, World!');

// Colar
const text = await readText();
```

**PROIBIDO:** `navigator.clipboard` (menos capabilities)

## Shell (Links Externos)

```typescript
import { open } from '@tauri-apps/plugin-shell';

// Abrir URL no browser padrao
await open('https://tauri.app');

// Abrir arquivo com app padrao
await open('/path/to/document.pdf');
```

**PROIBIDO:** `window.open()` (comportamento inconsistente)

## Store (Persistencia)

```typescript
import { Store } from '@tauri-apps/plugin-store';

const store = new Store('settings.json');

// Salvar
await store.set('theme', 'dark');
await store.save();

// Carregar
const theme = await store.get<string>('theme');
```

**PROIBIDO:** `localStorage` (sem criptografia, sem sync)
```

## 4.3 Skill: tauri-frontend.md

```markdown
---
trigger: keywords
keywords: [tauri component, tauri react, tauri ui, desktop ui]
description: Padroes de frontend para apps Tauri
---

# Frontend Patterns para Tauri

## Filosofia
Apps Tauri sao DESKTOP apps, nao sites. O frontend deve:
- Aproveitar capacidades desktop (hover, keyboard, etc.)
- Usar CSS moderno sem restricoes de "browser compatibility"
- Integrar-se com o sistema (tray, menus, shortcuts)

## Estrutura de Componentes

```
src/
├── components/
│   ├── ui/              # Componentes base (Button, Input, etc.)
│   ├── native/          # Wrappers para APIs nativas
│   │   ├── FilePicker.tsx
│   │   ├── Notification.tsx
│   │   └── ThemeSync.tsx
│   └── features/        # Componentes de feature
├── hooks/
│   ├── useTauriEvent.ts # Subscribe a eventos Tauri
│   ├── useFileSystem.ts # Wrapper para fs plugin
│   └── useNativeTheme.ts# Sync com tema do sistema
├── lib/
│   └── tauri/           # Bindings e helpers
└── App.tsx
```

## Componente: FilePicker (Exemplo Golden Path)

```tsx
// components/native/FilePicker.tsx
import { open } from '@tauri-apps/plugin-dialog';
import { readFile } from '@tauri-apps/plugin-fs';

interface FilePickerProps {
  onSelect: (content: Uint8Array, path: string) => void;
  accept?: string[];
  label?: string;
}

export function FilePicker({ onSelect, accept, label = 'Select File' }: FilePickerProps) {
  const handleClick = async () => {
    const path = await open({
      multiple: false,
      filters: accept ? [{ name: 'Files', extensions: accept }] : undefined,
    });

    if (path && typeof path === 'string') {
      const content = await readFile(path);
      onSelect(content, path);
    }
  };

  return (
    <button
      onClick={handleClick}
      className="
        px-4 py-2 rounded-lg
        bg-white/10 hover:bg-white/20
        backdrop-blur-xl
        border border-white/20
        transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-indigo-500
      "
    >
      {label}
    </button>
  );
}
```

## Hook: useTauriEvent

```tsx
// hooks/useTauriEvent.ts
import { useEffect } from 'react';
import { listen, UnlistenFn } from '@tauri-apps/api/event';

export function useTauriEvent<T>(
  event: string,
  handler: (payload: T) => void
) {
  useEffect(() => {
    let unlisten: UnlistenFn;

    listen<T>(event, (e) => handler(e.payload))
      .then((fn) => { unlisten = fn; });

    return () => { unlisten?.(); };
  }, [event, handler]);
}
```

## Hook: useNativeTheme

```tsx
// hooks/useNativeTheme.ts
import { useEffect, useState } from 'react';
import { getCurrentWindow, Theme } from '@tauri-apps/api/window';

export function useNativeTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const window = getCurrentWindow();

    window.theme().then((t) => {
      setTheme(t === Theme.Light ? 'light' : 'dark');
    });

    const unlisten = window.onThemeChanged(({ payload }) => {
      setTheme(payload === Theme.Light ? 'light' : 'dark');
    });

    return () => { unlisten.then((fn) => fn()); };
  }, []);

  return theme;
}
```

## Styling: Desktop-First

```css
/* Aproveitar capacidades desktop */

/* Hover states ricos (desktop tem mouse) */
.card:hover {
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

/* Backdrop blur (WebView moderno suporta) */
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
}

/* Custom scrollbar (desktop) */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

/* Keyboard focus visible */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

## Keyboard Shortcuts

```tsx
// hooks/useKeyboardShortcut.ts
import { useEffect } from 'react';

type Modifier = 'ctrl' | 'alt' | 'shift' | 'meta';

export function useKeyboardShortcut(
  key: string,
  callback: () => void,
  modifiers: Modifier[] = []
) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const modifiersMatch =
        modifiers.includes('ctrl') === e.ctrlKey &&
        modifiers.includes('alt') === e.altKey &&
        modifiers.includes('shift') === e.shiftKey &&
        modifiers.includes('meta') === e.metaKey;

      if (e.key.toLowerCase() === key.toLowerCase() && modifiersMatch) {
        e.preventDefault();
        callback();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [key, callback, modifiers]);
}

// Uso
useKeyboardShortcut('s', handleSave, ['ctrl']); // Ctrl+S
useKeyboardShortcut('n', handleNew, ['ctrl']);  // Ctrl+N
```
```

---

# PARTE 5: SUBAGENTES CUSTOMIZADOS

## 5.1 Subagente: tauri-frontend-dev.md

```markdown
# Tauri Frontend Developer

## Identidade
Voce e um desenvolvedor frontend especializado em apps Tauri.
Sua missao e criar UIs que aproveitam 100% das capacidades desktop/nativas.

## Regras Absolutas

### NUNCA Fazer
- Usar `<input type="file">` (sempre `dialog.open()`)
- Usar `localStorage` (sempre `store` plugin)
- Usar `alert()` ou toasts web (sempre `notification` plugin)
- Simplificar CSS por "compatibilidade" (WebView e moderno)
- Ignorar keyboard shortcuts
- Criar UI "mobile-first" (e desktop-first)

### SEMPRE Fazer
- Usar APIs nativas para file, clipboard, notification
- Implementar hover states ricos
- Adicionar keyboard shortcuts para acoes principais
- Usar backdrop-filter, gradients complexos
- Sincronizar com tema do sistema
- Type-safe IPC via tauri-specta

## Checklist Pre-Entrega

Antes de considerar codigo pronto:
- [ ] Todas as interacoes de arquivo usam dialog/fs plugins?
- [ ] Notificacoes usam plugin nativo?
- [ ] Clipboard usa plugin nativo?
- [ ] Links externos usam shell.open()?
- [ ] Keyboard shortcuts implementados?
- [ ] Hover states funcionais?
- [ ] Tema sincroniza com sistema?

## Padrao de Componentes

Sempre seguir estrutura:
```
components/
  native/      # Wrappers para APIs Tauri
  ui/          # Componentes visuais puros
  features/    # Componentes de dominio
```

## Contexto Tecnico

- Tauri 2.x (plugins no formato @tauri-apps/plugin-*)
- React 19 + TypeScript
- Tailwind CSS
- tauri-specta para IPC type-safe

Consultar skills `tauri-native-apis` e `tauri-frontend` para detalhes.
```

## 5.2 Subagente: tauri-rust-dev.md

```markdown
# Tauri Rust Developer

## Identidade
Voce e um desenvolvedor Rust especializado em backends Tauri.
Sua missao e criar commands eficientes, seguros e bem tipados.

## Regras de Commands

### Assinatura Correta
```rust
// CORRETO: Result com error serializavel
#[tauri::command]
async fn process_file(path: String) -> Result<ProcessedData, AppError> {
    // ...
}

// INCORRETO: Panic possivel
#[tauri::command]
fn process_file(path: String) -> String {
    std::fs::read_to_string(&path).unwrap() // PANIC!
}
```

### Error Handling

```rust
use thiserror::Error;
use serde::Serialize;

#[derive(Debug, Error, Serialize)]
pub enum AppError {
    #[error("File not found: {0}")]
    FileNotFound(String),

    #[error("Processing failed: {0}")]
    ProcessingError(String),

    #[error("Permission denied")]
    PermissionDenied,
}

// Converter de std::io::Error
impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        match err.kind() {
            std::io::ErrorKind::NotFound => AppError::FileNotFound(err.to_string()),
            std::io::ErrorKind::PermissionDenied => AppError::PermissionDenied,
            _ => AppError::ProcessingError(err.to_string()),
        }
    }
}
```

### Naming Convention

```rust
// Rust: snake_case
#[tauri::command]
fn get_user_settings() -> Settings { ... }

// Se precisar camelCase no JS:
#[tauri::command(rename_all = "camelCase")]
fn get_user_settings() -> Settings { ... }
// JS recebe: getUserSettings
```

### Async Commands

```rust
// Para operacoes I/O, SEMPRE async
#[tauri::command]
async fn read_large_file(path: String) -> Result<Vec<u8>, AppError> {
    tokio::fs::read(&path).await.map_err(Into::into)
}

// Sync apenas para operacoes CPU-bound rapidas
#[tauri::command]
fn calculate_hash(data: Vec<u8>) -> String {
    // Calculo rapido, nao bloqueia
}
```

### Large Data

```rust
// Para dados grandes, usar Response
use tauri::ipc::Response;

#[tauri::command]
fn get_binary_data() -> Response {
    let data: Vec<u8> = load_data();
    Response::new(data)
}
```

## Estrutura de Projeto

```
src-tauri/
├── src/
│   ├── main.rs           # Entry point
│   ├── lib.rs            # Exports publicos
│   ├── commands/         # Modulo de commands
│   │   ├── mod.rs
│   │   ├── file.rs       # Commands de arquivo
│   │   └── process.rs    # Commands de processamento
│   ├── services/         # Logica de negocio
│   │   ├── mod.rs
│   │   └── processor.rs
│   └── models/           # Tipos de dados
│       ├── mod.rs
│       └── settings.rs
├── Cargo.toml
└── tauri.conf.json
```

## Checklist Pre-Entrega

- [ ] Todos os commands retornam Result?
- [ ] Errors implementam Serialize?
- [ ] Async para operacoes I/O?
- [ ] Nenhum unwrap() em paths de usuario?
- [ ] Types exportados para tauri-specta?
```

## 5.3 Subagente: tauri-reviewer.md

```markdown
# Tauri Code Reviewer

## Identidade
Voce e um revisor de codigo especializado em apps Tauri.
Sua missao e garantir que o codigo aproveita capacidades nativas
e nao contem simplificacoes desnecessarias.

## Checklist de Review

### Frontend

#### APIs Nativas (CRITICO)
- [ ] `<input type="file">` encontrado? → REJEITAR
- [ ] `localStorage` encontrado? → REJEITAR
- [ ] `alert()` ou `confirm()` encontrado? → REJEITAR
- [ ] `window.open()` encontrado? → REJEITAR
- [ ] `navigator.clipboard` encontrado? → VERIFICAR

#### Qualidade de UI
- [ ] Hover states implementados?
- [ ] Keyboard shortcuts para acoes principais?
- [ ] Tema sincroniza com sistema?
- [ ] Transicoes/animacoes suaves?
- [ ] Scrollbar customizada?

#### Type Safety
- [ ] IPC usa tauri-specta?
- [ ] Nenhum `any` em chamadas Tauri?
- [ ] Types bem definidos?

### Backend (Rust)

#### Error Handling
- [ ] Commands retornam Result?
- [ ] Errors sao Serialize?
- [ ] Nenhum unwrap() em input de usuario?
- [ ] Nenhum panic possivel em runtime?

#### Performance
- [ ] Async para I/O?
- [ ] Response para dados grandes?
- [ ] Processamento pesado em thread separada?

#### Seguranca
- [ ] Paths validados (nao aceitar "../")?
- [ ] Permissoes minimas no tauri.conf.json?
- [ ] CSP configurado?

## Formato de Review

Para cada arquivo, reportar:

```markdown
## [filename]

### Problemas Criticos
- Linha X: [descricao] → [acao necessaria]

### Melhorias Sugeridas
- Linha Y: [sugestao]

### Aprovado
- [aspectos que estao corretos]
```

## Red Flags Automaticos

Se encontrar QUALQUER um destes, REJEITAR imediatamente:

1. `<input type="file"` sem wrapper Tauri
2. `localStorage.` sem justificativa
3. `alert(` ou `confirm(`
4. `.unwrap()` em input de usuario
5. `any` em tipos de IPC
6. `invoke(` sem tauri-specta
```

---

# PARTE 6: HOOKS E AUTOMACAO

## 6.1 Hook: Pre-Commit Tauri

```javascript
// .claude/hooks/pre-commit-tauri.js

const FORBIDDEN_PATTERNS = [
  {
    pattern: /<input[^>]*type=["']file["']/gi,
    message: 'Use dialog.open() instead of <input type="file">',
    severity: 'error'
  },
  {
    pattern: /localStorage\.(get|set)Item/g,
    message: 'Use @tauri-apps/plugin-store instead of localStorage',
    severity: 'error'
  },
  {
    pattern: /\balert\s*\(/g,
    message: 'Use @tauri-apps/plugin-notification instead of alert()',
    severity: 'error'
  },
  {
    pattern: /window\.open\s*\(/g,
    message: 'Use shell.open() instead of window.open()',
    severity: 'warning'
  },
  {
    pattern: /\.unwrap\(\)/g,
    file: /\.rs$/,
    message: 'Avoid .unwrap() - use proper error handling',
    severity: 'warning'
  },
  {
    pattern: /: any\b/g,
    file: /\.tsx?$/,
    message: 'Avoid "any" type - use proper typing',
    severity: 'warning'
  }
];

function validateFile(content, filename) {
  const issues = [];

  for (const rule of FORBIDDEN_PATTERNS) {
    if (rule.file && !rule.file.test(filename)) continue;

    const matches = content.match(rule.pattern);
    if (matches) {
      issues.push({
        rule: rule.message,
        severity: rule.severity,
        count: matches.length
      });
    }
  }

  return issues;
}

module.exports = { validateFile, FORBIDDEN_PATTERNS };
```

## 6.2 Configuracao de Hooks

```json
// .claude/settings.json (parcial)
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "node .claude/hooks/pre-commit-tauri.js validate $FILE"
      }
    ]
  }
}
```

---

# PARTE 7: WORKFLOW RECOMENDADO

## 7.1 Iniciando Projeto Novo

```bash
# 1. Clonar template com integracao Claude Code
git clone https://github.com/dannysmith/tauri-template my-app
cd my-app

# 2. Instalar dependencias
bun install
cd src-tauri && cargo build && cd ..

# 3. Copiar skills e subagentes deste playbook
mkdir -p .claude/skills .claude/agents
# (copiar arquivos .md)

# 4. Configurar CLAUDE.md e ARCHITECTURE.md
# (usar templates deste playbook)

# 5. Injetar contexto inicial
curl https://tauri.app/llms.txt > .claude/context/tauri-docs.md

# 6. Primeira execucao
bun run tauri dev
```

## 7.2 Desenvolvendo Features

### Antes de Codar

1. Verificar se existe API nativa para a necessidade
2. Consultar skill `tauri-native-apis`
3. Definir se e frontend, backend, ou ambos

### Durante Desenvolvimento

1. Usar subagente apropriado (frontend-dev ou rust-dev)
2. Seguir padroes das skills
3. Type-safe IPC sempre

### Antes de Commit

1. Rodar review com subagente `tauri-reviewer`
2. Verificar checklist de APIs nativas
3. Testar em todas as plataformas alvo

## 7.3 Prompts Efetivos

### Para Features de Arquivo

```
Criar componente de selecao de arquivo que:
1. USA dialog.open() do Tauri (NAO <input type="file">)
2. Filtra por extensoes [wav, mp3, webm]
3. Le conteudo com fs.readFile()
4. Mostra preview do arquivo selecionado

Seguir padrao do skill tauri-native-apis.
```

### Para Styling

```
Criar card com efeito glassmorphism que:
1. USA backdrop-filter (WebView moderno suporta)
2. Tem hover state com elevation
3. Keyboard focusable
4. Transicoes suaves

NAO simplificar por "compatibilidade" - e app desktop.
```

### Para Commands Rust

```
Criar command para processar arquivo de audio que:
1. Retorna Result<AudioMetrics, AppError>
2. AppError implementa Serialize
3. E async (operacao I/O)
4. Tem types exportados para tauri-specta

Seguir padrao do skill tauri-rust-dev.
```

---

# PARTE 8: TROUBLESHOOTING

## 8.1 Erros Comuns de LLMs

| Erro | Sintoma | Correcao |
|------|---------|----------|
| Fallback web | `<input type="file">` | Rejeitar, exigir dialog.open() |
| Type unsafe | `invoke('cmd', {...})` | Exigir tauri-specta |
| Panic possivel | `.unwrap()` em input | Exigir Result handling |
| CSS timido | Evita backdrop-filter | Lembrar que WebView e moderno |
| Ignora nativo | alert() para feedback | Exigir notification plugin |

## 8.2 Debugging

### Frontend
- Chrome DevTools via WebView
- `console.log` funciona normalmente
- React DevTools (instalar extensao)

### Backend (Rust)
- `println!` aparece no terminal
- `dbg!()` para inspecao rapida
- VS Code + rust-analyzer + CodeLLDB

### IPC
- Eventos podem ser monitorados com listen()
- tauri-specta gera types em build time
- Erros de serializacao aparecem no console

## 8.3 Recursos de Emergencia

Se LLM insistir em simplificar:

1. Citar diretamente o CLAUDE.md
2. Mostrar exemplo do skill correspondente
3. Usar subagente reviewer para rejeitar
4. Em ultimo caso, prompt explicito:

```
PARA. O codigo que voce gerou usa [X] que e PROIBIDO neste projeto.
Consulte CLAUDE.md secao "APIs Nativas Obrigatorias".
Refaca usando [Y] conforme documentado.
```

---

# APENDICE A: Links de Referencia

| Recurso | URL |
|---------|-----|
| Tauri llms.txt | https://tauri.app/llms.txt |
| Tauri Docs v2 | https://v2.tauri.app/ |
| Tauri Plugins | https://github.com/tauri-apps/plugins-workspace |
| Claude Skills Tauri | https://claude-plugins.dev/skills/@delorenj/skills/tauri |
| dannysmith template | https://github.com/dannysmith/tauri-template |
| awesome-tauri | https://github.com/tauri-apps/awesome-tauri |

---

# APENDICE B: Exemplo Completo de Projeto

Estrutura minima funcional:

```
my-tauri-app/
├── .claude/
│   ├── skills/
│   │   ├── tauri-core.md
│   │   ├── tauri-native-apis.md
│   │   └── tauri-frontend.md
│   ├── agents/
│   │   ├── tauri-frontend-dev.md
│   │   ├── tauri-rust-dev.md
│   │   └── tauri-reviewer.md
│   └── context/
│       └── tauri-docs.md          # Conteudo do llms.txt
├── CLAUDE.md
├── ARCHITECTURE.md
├── src/
│   ├── App.tsx
│   ├── components/
│   │   └── native/
│   │       └── FilePicker.tsx
│   └── hooks/
│       └── useTauriEvent.ts
├── src-tauri/
│   ├── src/
│   │   ├── main.rs
│   │   └── commands/
│   │       └── file.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
├── package.json
└── vite.config.ts
```

---

*Playbook gerado em 2026-01-20*
*Baseado em pesquisa web-research-specialist + analise arquitetural*
