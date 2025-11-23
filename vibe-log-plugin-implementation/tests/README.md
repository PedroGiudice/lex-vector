# Test Suite Documentation

Comprehensive test suite for the orchestration-tracker plugin.

## Test Structure

```
tests/
├── setup.ts                           # Global test setup and mocks
├── helpers.ts                         # Test utilities and helpers
├── fixtures/                          # Test data and mock structures
│   ├── mock-agents.ts                # Sample agent definitions
│   ├── mock-hooks.ts                 # Sample hook configurations
│   └── mock-skills.ts                # Sample skill definitions
├── unit/                             # Unit tests (isolated components)
│   ├── plugin-registry.test.ts       # PluginRegistry tests
│   ├── agent-discovery.test.ts       # AgentDiscovery tests
│   ├── hook-monitor.test.ts          # HookMonitor tests
│   └── skill-tracker.test.ts         # SkillTracker tests
└── integration/                      # Integration tests (full workflows)
    ├── orchestration-full-cycle.test.ts  # End-to-end lifecycle tests
    └── performance.test.ts           # Performance benchmarks
```

## Running Tests

### All Tests
```bash
npm test
```

### Unit Tests Only
```bash
npm run test:unit
```

### Integration Tests Only
```bash
npm run test:integration
```

### Watch Mode (Development)
```bash
npm run test:watch
```

### Coverage Report
```bash
npm run test:coverage
```

### Performance Benchmarks
```bash
npm run test:perf
```

## Test Categories

### Unit Tests

**plugin-registry.test.ts** (45 tests)
- Plugin registration and validation
- Plugin lifecycle (init, cleanup)
- Hook triggering and execution
- Error handling and recovery
- Singleton pattern verification

**agent-discovery.test.ts** (15 tests)
- Agent file discovery from `.claude/agents`
- YAML frontmatter parsing
- Markdown header parsing
- Custom marker parsing
- Error handling for invalid files
- Performance benchmarks (<50ms for 10 agents)

**hook-monitor.test.ts** (18 tests)
- Hook discovery from settings.json
- Hook name extraction from commands
- Execution metrics tracking
- Statistics calculation (avg duration, failure rate)
- Performance benchmarks (<20ms for parsing)

**skill-tracker.test.ts** (22 tests)
- Skill discovery from `skills/` directory
- Multi-format support (SKILL.md, skill.yaml, skill.json)
- Trigger-based skill detection from prompts
- Usage statistics tracking
- Performance benchmarks (<50ms for 10 skills, <5ms for detection)

### Integration Tests

**orchestration-full-cycle.test.ts** (10 tests)
- Complete session lifecycle (SessionStart → prompts → SessionEnd)
- Resource discovery (agents, hooks, skills)
- Data persistence to storage
- Concurrent session handling
- Session summary generation

**performance.test.ts** (10 tests)
- Agent discovery: 10 agents <50ms, 50 agents <100ms
- Skill discovery: 10 skills <50ms, 30 skills <100ms
- Hook parsing: <20ms for 10 hooks
- Full cycle: <100ms (5 agents + 10 skills + 2 hooks)
- Memory leak detection (100 iterations)
- Concurrent session processing

## Test Utilities

### Mock Factories (`tests/helpers.ts`)

```typescript
// Create mock plugin
const plugin = createMockPlugin({ name: 'test-plugin' });

// Create mock config
const config = createMockConfig({ enabled: true });

// Create mock session
const session = createMockSession({ sessionId: 'test-123' });

// Measure execution time
const { result, duration } = await measureTime(() => asyncFunction());
```

### Test Fixtures

All fixtures are in `tests/fixtures/`:
- `mock-agents.ts`: Sample agent definitions in various formats
- `mock-hooks.ts`: Sample hook configurations and settings.json
- `mock-skills.ts`: Sample skill definitions and detection prompts

## Coverage Goals

| Metric       | Target | Status |
|--------------|--------|--------|
| Lines        | >95%   | TBD    |
| Functions    | >95%   | TBD    |
| Branches     | >90%   | TBD    |
| Statements   | >95%   | TBD    |

## Performance Targets

| Operation            | Target  | Current |
|---------------------|---------|---------|
| Agent discovery (10) | <50ms   | TBD     |
| Skill discovery (10) | <50ms   | TBD     |
| Hook parsing        | <20ms   | TBD     |
| Skill detection     | <5ms    | TBD     |
| Full cycle          | <100ms  | TBD     |

## Writing New Tests

### AAA Pattern
All tests follow the Arrange-Act-Assert pattern:

```typescript
it('should do something', async () => {
  // Arrange: Setup test data
  const plugin = createMockPlugin();
  const config = createMockConfig();

  // Act: Execute the operation
  await registry.register(plugin, config);

  // Assert: Verify the outcome
  expect(registry.has('test-plugin')).toBe(true);
});
```

### Test Naming Convention
- Use descriptive names: `should [expected behavior] when [condition]`
- Examples:
  - `should register plugin successfully`
  - `should reject invalid plugin name`
  - `should handle missing files gracefully`

### Mocking File System
File system operations are automatically mocked in `tests/setup.ts`:

```typescript
import { readFile, readdir } from 'fs/promises';
import { vi } from 'vitest';

vi.mocked(readdir).mockResolvedValue(['file1.md', 'file2.md'] as any);
vi.mocked(readFile).mockResolvedValue('file contents');
```

### Skip Tests for Unimplemented Features
Use `.skipIf()` for tests that depend on unimplemented code:

```typescript
it.skipIf(!AgentDiscovery)('should discover agents', async () => {
  // Test implementation
});
```

## Debugging Tests

### Run Single Test File
```bash
npm test -- agent-discovery.test.ts
```

### Run Single Test
```bash
npm test -- -t "should register plugin successfully"
```

### Verbose Output
```bash
npm test -- --reporter=verbose
```

### Debug Mode
```bash
node --inspect-brk ./node_modules/.bin/vitest run
```

## CI/CD Integration

Tests are designed to run in CI environments:
- No external dependencies
- All file operations mocked
- Deterministic results
- Performance benchmarks with reasonable tolerances

Add to `.github/workflows/test.yml`:
```yaml
- name: Run tests
  run: npm test

- name: Check coverage
  run: npm run test:coverage

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
```

## Troubleshooting

### Tests Timeout
Increase timeout in `vitest.config.ts`:
```typescript
testTimeout: 20000 // 20 seconds
```

### Mock Not Working
Ensure mock is defined before import:
```typescript
vi.mock('fs/promises');  // Before importing module
const module = await import('./module.js');
```

### Performance Tests Fail
Performance benchmarks may fail on slow machines. Adjust thresholds:
```typescript
expect(duration).toBeLessThan(100); // Increase if needed
```

## Resources

- [Vitest Documentation](https://vitest.dev)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Mock Service Worker](https://mswjs.io) (for future HTTP mocking)
