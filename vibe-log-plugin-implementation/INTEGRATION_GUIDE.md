# Integration Guide: vibe-log-cli Fork

**Target:** Submit PR to [vibe-log/vibe-log-cli](https://github.com/vibe-log/vibe-log-cli)

---

## 🎯 Quick Integration (Copy & Paste)

### 1. Fork & Clone vibe-log-cli

```bash
# Fork on GitHub first (click Fork button)
git clone https://github.com/YOUR-USERNAME/vibe-log-cli
cd vibe-log-cli
```

### 2. Create Feature Branch

```bash
git checkout -b feature/orchestration-tracking-plugin
```

### 3. Copy Plugin Files

```bash
# From this implementation directory
cd /home/user/Claude-Code-Projetos/vibe-log-plugin-implementation

# Copy to vibe-log-cli fork
cp -r src/plugins <vibe-log-cli-path>/src/
cp -r src/cli/commands/orchestration.ts <vibe-log-cli-path>/src/cli/commands/
cp -r tests <vibe-log-cli-path>/
cp -r docs <vibe-log-cli-path>/
cp -r examples <vibe-log-cli-path>/
cp vitest.config.ts <vibe-log-cli-path>/
```

### 4. Update vibe-log-cli Files

#### A) `src/index.ts` (or main entry point)

Add plugin system initialization:

```typescript
import { pluginRegistry } from './plugins/core/plugin-registry.js';
import { orchestrationTracker } from './plugins/orchestration-tracker/index.js';

// During CLI initialization
export async function initializePlugins() {
  const config = await loadConfig(); // Your existing config loader

  // Load orchestration tracker if enabled
  if (config.plugins?.['orchestration-tracker']?.enabled) {
    await pluginRegistry.register(
      orchestrationTracker,
      config.plugins['orchestration-tracker']
    );
  }
}

// Call before CLI starts
await initializePlugins();
```

#### B) `src/cli/index.ts` (or CLI setup)

Register orchestration command:

```typescript
import { Command } from 'commander';
import { createOrchestrationCommand } from './commands/orchestration.js';

const program = new Command();

// ... existing commands

// Add orchestration command
program.addCommand(createOrchestrationCommand());

program.parse();
```

#### C) Hook integration points

Find where hooks are triggered (likely in session management):

```typescript
import { pluginRegistry } from '../plugins/core/plugin-registry.js';
import { HookTrigger } from '../plugins/core/types.js';

// SessionStart hook
async function onSessionStart(session) {
  await pluginRegistry.triggerHook(
    HookTrigger.SessionStart,
    {
      sessionId: session.id,
      startTime: session.startTime,
      projectDir: session.projectDir
    }
  );
}

// UserPromptSubmit hook
async function onPromptSubmit(session, prompt) {
  await pluginRegistry.triggerHook(
    HookTrigger.UserPromptSubmit,
    {
      sessionId: session.id,
      startTime: session.startTime,
      projectDir: session.projectDir
    },
    { prompt }
  );
}

// SessionEnd hook
async function onSessionEnd(session) {
  await pluginRegistry.triggerHook(
    HookTrigger.SessionEnd,
    {
      sessionId: session.id,
      startTime: session.startTime,
      endTime: Date.now(),
      projectDir: session.projectDir
    }
  );
}
```

### 5. Update package.json

Merge scripts (if not already present):

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:plugins": "vitest run tests/unit/plugin* tests/unit/agent* tests/unit/hook* tests/unit/skill*"
  }
}
```

### 6. Test Locally

```bash
cd <vibe-log-cli-path>

# Install dependencies
npm install

# Run type check
npm run type-check

# Run tests
npm test

# Run linter
npm run lint

# Build
npm run build

# Test CLI locally
npm link
npx vibe-log-cli orchestration --help
```

### 7. Commit & Push

```bash
git add .
git commit -m "$(cat <<'EOF'
feat: add orchestration tracking plugin

Implements multi-agent orchestration tracking for Claude Code workflows.

Features:
- Plugin system architecture (opt-in, modular)
- Agent lifecycle tracking (spawning, execution, completion)
- Hook performance monitoring (duration, failure rate)
- Skill usage analytics (invocations, effectiveness)
- Generic design (works with any Claude Code project structure)

Technical:
- TypeScript strict mode compliant
- 120+ test cases (>95% coverage target)
- Performance optimized (<50ms overhead)
- Comprehensive documentation

Breaking changes: None (backward compatible, opt-in only)

Closes #XXX (if there's a related issue)
EOF
)"

git push -u origin feature/orchestration-tracking-plugin
```

### 8. Create Pull Request

Go to GitHub and create PR with this description:

```markdown
Copy from: /home/user/Claude-Code-Projetos/vibe-log-plugin-implementation/PR_DESCRIPTION.md
```

**Link to proposal:**
https://github.com/PedroGiudice/Claude-Code-Projetos/blob/main/VIBE-LOG-INTEGRATION-PROPOSAL.md

---

## 🔍 Validation Checklist

Before submitting PR, verify:

- [ ] TypeScript compiles without errors (`npm run type-check`)
- [ ] All tests pass (`npm test`)
- [ ] Linter passes (`npm run lint`)
- [ ] Build succeeds (`npm run build`)
- [ ] CLI command works (`npx vibe-log-cli orchestration --help`)
- [ ] Documentation is complete
- [ ] CHANGELOG.md updated
- [ ] No breaking changes

---

## 🐛 Troubleshooting

### Type Errors

If you get type errors related to vibe-log-cli's existing types:

1. Check vibe-log-cli's type definitions
2. Adjust plugin types to match (our types are generic)
3. Add type casts if necessary (but avoid `any`)

### Import Errors

All imports use `.js` extensions (ESM standard). If vibe-log-cli uses different convention:

```bash
# Find all .ts files and update imports
find src tests -name "*.ts" -exec sed -i "s/from '\\(.*\\)\\.js'/from '\\1'/g" {} +
```

### Test Failures

Tests are designed with `.skipIf()` for missing modules. If tests fail:

1. Check that core modules are implemented
2. Verify mock fixtures match vibe-log-cli's data structures
3. Adjust test expectations if needed

---

## 📞 Support

If you encounter issues:

1. Check `IMPLEMENTATION_SPEC.md` for detailed specs
2. Review `IMPLEMENTATION_SUMMARY.md` (from desenvolvimento agent)
3. Check `TEST_SUITE_SUMMARY.md` (from qualidade-codigo agent)
4. Review `docs/plugins/orchestration-tracker.md` (from documentacao agent)

---

**Ready to submit! 🚀**
