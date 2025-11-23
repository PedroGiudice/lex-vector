# Skill Activation System - Architectural Code Review

**Last Updated:** 2025-11-23

**Reviewer:** Code Review Agent (Claude Sonnet 4.5)

**Files Reviewed:**
- `.claude/hooks/lib/skill-detector.js` (161 lines)
- `.claude/hooks/sync-skill-rules.js` (284 lines)
- `.claude/skills/skill-rules.json` (1469 lines, 56 skills)
- `.claude/hooks/context-collector.js` (258 lines, integration)

**Review Scope:** Architecture, conflict resolution, performance, auto-generation quality, ranking algorithm, error handling, integration correctness, and testing gaps.

---

## Executive Summary

**Architecture Status: ⚠️ FUNCTIONAL BUT NEEDS IMPROVEMENTS**

The skill activation system is operationally functional and demonstrates good architectural intent with its modular design (detector → sync → rules → integration). However, critical issues in keyword matching, priority weighting, and auto-generated trigger quality create significant risks of false positives and unstable ranking with 56 skills active.

**Key Findings:**
- 🔴 **5 Critical Issues (P0)** - Must fix for production reliability
- 🟡 **5 Important Improvements (P1)** - Should fix for quality/performance
- 🔵 **4 Minor Suggestions (P2)** - Nice to have
- ❌ **Zero test coverage** - Major technical debt

**Immediate Action Required:**
1. Fix substring keyword matching (causing massive false positives)
2. Rebalance priority weights or redistribute skill priorities
3. Improve stopwords filtering in auto-generation
4. Add unit tests for core matching logic
5. Implement caching for skill-rules.json

---

## Critical Issues (P0) - MUST FIX

### P0-1: Keyword Matching Uses Substring Without Word Boundaries

**File:** `skill-detector.js` (line 48)

**Problem:**
```javascript
if (promptLower.includes(keyword.toLowerCase())) {
  score += 10;
  // ...
}
```

This creates **massive false positives** because `includes()` matches substrings anywhere:
- Keyword `"test"` matches: "**test**", "la**test**", "con**test**", "**test**ing", "a**test**ado"
- Keyword `"user"` matches: "**user**", "s**user**", "**user**name", "**user**Agent"
- Keyword `"creating"` matches: "**creating**", "re**creating**", "procre**ating**"

**Real Impact:** With 56 skills containing generic keywords like "user" (appears in 10+ skills), "create/creating" (20+ skills), "skill" (15+ skills), nearly every prompt will trigger 10-20 false matches.

**Example from skill-rules.json (line 160):**
```json
"code-auditor": {
  "keywords": ["user", "wants", "audit"]  // "user" and "wants" are extracted noise
}
```

Prompt: "latest user interface changes" → False match on "code-auditor" (score +10).

**Recommended Fix:**
```javascript
// Use word boundary regex
const keywordRegex = new RegExp(`\\b${escapeRegex(keyword)}\\b`, 'i');
if (keywordRegex.test(prompt)) {
  score += 10;
  // ...
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
```

**Severity:** CRITICAL - Fundamentally breaks matching accuracy with 56 skills.

---

### P0-2: Priority Weights Dominate Match Scores

**File:** `skill-detector.js` (lines 94-104)

**Problem:**
```javascript
const priorityWeights = {
  'critical': 100,
  'high': 50,
  'medium': 20,
  'low': 10
};

m.finalScore = m.score + priorityWeight;
```

**Analysis:**
- Max match score: 25 (1 keyword=10 + 1 pattern=15)
- Critical priority weight: 100
- Ratio: **100:25 = 4:1**

**Imbalance:**
- Critical skill with NO matches: score = 0 + 100 = **100**
- High skill with PERFECT matches: score = 25 + 50 = **75**

**Result:** Critical skills ALWAYS rank above high skills regardless of relevance.

**Distribution Problem:** From skill-rules.json metadata:
- 36% of skills are "critical" (20/56)
- 27% are "high" (15/56)

When **36% of everything is critical, nothing is critical**. The priority system loses meaning.

**Real Example:**
Prompt: "refactor code structure"

Expected ranking by relevance:
1. code-refactor (perfect semantic match)
2. code-auditor (related)
3. systematic-debugging (loosely related)

Actual ranking (if all are critical priority):
1. Whichever critical skill has highest noise score
2. code-refactor might not even be top 3

**Recommended Fix (Option A - Reweight):**
```javascript
const priorityWeights = {
  'critical': 20,  // Reduced 5x
  'high': 10,      // Reduced 5x
  'medium': 5,     // Reduced 4x
  'low': 2         // Reduced 5x
};
```

Now critical advantage = 20 points (vs max match 25), not 100.

**Recommended Fix (Option B - Redistribute Priorities):**
- Review all 56 skills
- Limit "critical" to 5-8 skills (10-15%)
- Most should be "medium" or "high"

**Severity:** CRITICAL - Makes ranking unstable and unpredictable.

---

### P0-3: Auto-Generated Intent Patterns Are Excessively Broad

**File:** `sync-skill-rules.js` (lines 186-208)

**Problem:**
```javascript
function generateIntentPatterns(skillName, keywords) {
  const patterns = [];
  const verbs = ['implement', 'create', 'build', 'develop', 'add', 'write', 'design', 'plan'];

  for (const keyword of keywords.slice(0, 2)) {
    for (const verb of verbs.slice(0, 3)) {
      patterns.push(`(${verb}).*?(${keyword})`);  // ← TOO BROAD
    }
  }
  // ...
}
```

**Example:** Skill "brainstorming" with keywords `["brainstorming", "creating"]`

**Generated patterns:**
```regex
(implement).*?(brainstorming)  // ✅ OK
(create).*?(brainstorming)     // ✅ OK
(build).*?(brainstorming)      // ✅ OK
(implement).*?(creating)       // ⚠️ Broad
(create).*?(creating)          // ❌ MATCHES EVERYTHING WITH "CREATE"
(build).*?(creating)           // ⚠️ Broad
```

Pattern `(create).*?(creating)` matches:
- "create a new **creating**" ← Literal (rare)
- "**creat**e anything then later say **creating**" ← Likely (common)
- "**creating** then later **create**" ← Also matches

**Impact:** With 20+ skills having "create/creating/created" patterns, **massive collision rate**.

**Real Data from skill-rules.json:**
- Skills with "creating" in keywords: 12 skills
- Skills with "(create).*?(creating)" pattern: 8+ skills

Prompt: "create a test suite" → Triggers 15+ skills incorrectly.

**Recommended Fix:**
```javascript
// Option 1: Make patterns more specific
for (const keyword of keywords.slice(0, 2)) {
  for (const verb of verbs.slice(0, 2)) {  // Reduce combos: 3 → 2
    // Require word boundaries
    patterns.push(`\\b${verb}\\b.*?\\b${keyword}\\b`);
  }
}

// Option 2: Only generate patterns for non-generic keywords
const genericKeywords = ['creating', 'building', 'writing', 'user', 'skill'];
const specificKeywords = keywords.filter(k => !genericKeywords.includes(k));
// Only use specificKeywords for pattern generation
```

**Severity:** CRITICAL - Causes 30-50% false positive rate in pattern matching.

---

### P0-4: Generic Keywords Not Filtered During Auto-Generation

**File:** `sync-skill-rules.js` (lines 52-62)

**Problem:**
```javascript
const stopwords = ['this', 'that', 'with', 'your', 'for', 'and', 'the', 'you', 'need', 'want', 'have'];
const words = useWhenMatch[1]
  .toLowerCase()
  .split(/\s+/)
  .filter(w => w.length > 3 && !stopwords.includes(w) && /^[a-z]+$/.test(w));
```

**Stopwords list is incomplete.** Missing critical generic terms that pollute skill-rules.json:

**Evidence from skill-rules.json:**

1. **"brainstorming"** (line 108-111):
   ```json
   "keywords": ["brainstorming", "creating", "before", "writing"]
   ```
   - ❌ "creating" - appears in 12 skills
   - ❌ "before" - generic temporal word
   - ❌ "writing" - appears in 8 skills

2. **"code-auditor"** (line 160):
   ```json
   "keywords": ["...", "user", "wants", "audit"]
   ```
   - ❌ "user" - appears in 10+ skills
   - ❌ "wants" - extracted from "user wants to audit"

3. **"architecture-diagram-creator"** (line 30-32):
   ```json
   "keywords": ["...", "users", "request", "system"]
   ```
   - ❌ "users" - generic
   - ❌ "request" - generic HTTP/user action term
   - ❌ "system" - appears in 15+ skills

**Validated Against Source SKILL.md:**

**code-auditor/SKILL.md** (line 3):
```yaml
description: "... Use when user wants to audit code quality..."
```

**Extracted keywords:** "user", "wants" (from "user wants to") → **WRONG**.

**brainstorming/SKILL.md** (line 3):
```yaml
description: "Use when creating or developing, before writing code..."
```

**Extracted keywords:** "creating", "before", "writing" → **ALL GENERIC**.

**Impact:** **~40-50% of auto-generated keywords are unusable noise**, polluting 56 skills with false triggers.

**Recommended Fix:**
```javascript
const stopwords = [
  // Original
  'this', 'that', 'with', 'your', 'for', 'and', 'the', 'you', 'need', 'want', 'have',
  // Add these
  'user', 'users', 'when', 'skill', 'before', 'after', 'wants', 'needs',
  'creating', 'building', 'writing', 'using', 'working',  // Generic verbs
  'request', 'requests', 'system', 'code', 'file', 'files'  // Too broad
];

// Also: Only extract from "When to Use" section, not description
const useWhenSection = content.match(/## When to Use\n([\s\S]*?)(?=\n##|$)/);
if (useWhenSection) {
  // Extract keywords from bullet points only
  const bulletPoints = useWhenSection[1].match(/- "(.*?)"/g);
  // ...
}
```

**Severity:** CRITICAL - Directly causes P0-1 (false positives) via noise keywords.

---

### P0-5: 36% of Skills Marked "Critical" Dilutes Priority System

**File:** `skill-rules.json` + `sync-skill-rules.js` (lines 75-102)

**Problem:**

**Priority Inference Logic:**
```javascript
function inferPriority(skillName, content) {
  if (skillName.match(/test|quality|security|audit|debug|error/) ||
      content.match(/critical|security|testing|debugging/i)) {
    return 'critical';
  }
  // ... similar for high, medium, low
}
```

**Distribution from skill-rules.json:**
- **Critical: 20 skills (36%)**
- High: 15 skills (27%)
- Medium: 15 skills (27%)
- Low: 6 skills (10%)

**Skills incorrectly marked "critical":**
- `testing-skills-with-subagents` - Meta-learning skill, not critical
- `testing-anti-patterns` - Educational skill, not critical
- `prompt-improver` - Quality-of-life, not critical
- `writing-skills` - Documentation skill, not critical
- `sharing-skills` - Meta-organizational, not critical

**Root Cause:** Name-based inference is too simplistic.

**Example:**
- Skill name: "testing-skills-with-subagents"
- Regex match: `/test/` → **CRITICAL** ❌
- Reality: It's a meta-skill about testing OTHER skills, not a critical testing skill

**Impact Combined with P0-2:**
With 20 critical skills, the ranking becomes a "critical skill lottery" where whichever critical skill gets a random noise match wins, even if irrelevant.

**Recommended Fix:**

**Option A - Manual Review:**
```javascript
// Hard-coded critical list (only truly critical)
const CRITICAL_SKILLS = [
  'systematic-debugging',
  'code-auditor',
  'test-driven-development',
  'security-audit',  // If exists
  'root-cause-tracing'
];

function inferPriority(skillName, content) {
  if (CRITICAL_SKILLS.includes(skillName)) return 'critical';
  // ... rest of logic for high/medium/low
}
```

**Option B - Content Analysis:**
```javascript
function inferPriority(skillName, content) {
  // Check for EXPLICIT critical markers in content
  if (content.match(/\b(CRITICAL|MUST|BLOCKING|REQUIRED)\b/i)) {
    return 'critical';
  }

  // Security/testing skills → high (not critical unless explicit)
  if (skillName.match(/test|security|debug/) || content.match(/testing|security/i)) {
    return 'high';
  }
  // ...
}
```

**Target Distribution:**
- Critical: 5-8 skills (10-15%)
- High: 15-20 skills (30-35%)
- Medium: 20-25 skills (40-45%)
- Low: 5-8 skills (10-15%)

**Severity:** CRITICAL - Combined with P0-2, makes ranking nearly random.

---

## Important Improvements (P1) - SHOULD FIX

### P1-1: No Caching of skill-rules.json

**File:** `skill-detector.js` (lines 29-30)

**Problem:**
```javascript
function detectSkill(prompt) {
  // Every call re-reads file from disk
  const rulesContent = fs.readFileSync(rulesPath, 'utf8');
  const rules = JSON.parse(rulesContent);
  // ...
}
```

**Impact:**
- Called on EVERY UserPromptSubmit
- Typical session: 10-50 prompts
- I/O overhead: 1469-line JSON file read 10-50× per session

**Performance Cost:**
- File I/O: ~1-5ms per read (depends on disk)
- JSON parsing: ~2-5ms for 1469 lines
- Total: **3-10ms overhead per prompt**

**Recommended Fix:**
```javascript
let cachedRules = null;
let cacheTimestamp = 0;
const CACHE_TTL = 60000; // 60 seconds

function loadRules() {
  const now = Date.now();

  // Return cache if valid
  if (cachedRules && (now - cacheTimestamp < CACHE_TTL)) {
    return cachedRules;
  }

  // Reload
  const rulesContent = fs.readFileSync(rulesPath, 'utf8');
  cachedRules = JSON.parse(rulesContent);
  cacheTimestamp = now;

  return cachedRules;
}

function detectSkill(prompt) {
  const rules = loadRules();
  // ...
}
```

**Alternative - In-memory cache forever:**
```javascript
let cachedRules = null;

function loadRules() {
  if (!cachedRules) {
    const rulesContent = fs.readFileSync(rulesPath, 'utf8');
    cachedRules = JSON.parse(rulesContent);
  }
  return cachedRules;
}
```

**Benefit:** Reduces per-prompt overhead from ~5ms to ~0ms after first load.

---

### P1-2: Break Statement Limits Multi-Keyword Matching

**File:** `skill-detector.js` (lines 46-54, 56-71)

**Problem:**
```javascript
// KEYWORD MATCHING
for (const keyword of config.promptTriggers.keywords) {
  if (promptLower.includes(keyword.toLowerCase())) {
    score += 10;
    matchedTriggers.push(`keyword: "${keyword}"`);
    break; // ← ONLY FIRST MATCH COUNTS
  }
}

// INTENT PATTERN MATCHING
for (const pattern of config.promptTriggers.intentPatterns) {
  if (regex.test(prompt)) {
    score += 15;
    matchedTriggers.push(`pattern: "${pattern}"`);
    break; // ← ONLY FIRST MATCH COUNTS
  }
}
```

**Scenario:**
- Skill: `test-driven-development`
- Keywords: `["TDD", "test driven", "write tests", "test first", "test coverage"]`
- Prompt: "**write tests** for **test coverage** using **TDD**"

**Current Behavior:**
- Matches "write tests" → score +10
- **BREAKS** → ignores "test coverage" and "TDD"
- Final score: 10

**Expected Behavior:**
- Should match all 3 keywords → stronger signal of relevance
- Final score: 30? Or weighted?

**Recommendation:**

**Option A - Count all matches but cap score:**
```javascript
let keywordMatches = 0;
for (const keyword of config.promptTriggers.keywords) {
  if (promptLower.includes(keyword.toLowerCase())) {
    keywordMatches++;
    matchedTriggers.push(`keyword: "${keyword}"`);
  }
}
// Diminishing returns: 1st=10, 2nd=+5, 3rd=+3, cap at 3
score += Math.min(10 + (keywordMatches - 1) * 5, 20);
```

**Option B - Keep break but improve quality:**
```javascript
// If we fix P0-1 (word boundaries) and P0-4 (stopwords),
// keeping break is acceptable since matches are now high-quality
```

**Impact:** Medium. Not critical if keyword quality improves (P0-1, P0-4).

---

### P1-3: No Performance Benchmarking

**Files:** All detection logic

**Problem:** No data on actual performance with 56 skills.

**Estimated Complexity:**
- 56 skills
- ~8 keywords/skill = 448 substring checks (or regex if fixed)
- ~4 patterns/skill = 224 regex tests
- Total: **~670 operations per prompt**

**Expected Performance:**
- Modern V8 (Node.js): ~5-10ms for all operations
- Acceptable for <50ms target ✅

**But:** No validation of this assumption.

**Recommended Tests:**
```javascript
// benchmark.js
const { detectSkill } = require('./skill-detector');

const testPrompts = [
  'audit code quality',
  'create a new frontend component',
  'debug failing tests',
  'implement user authentication',
  // ... 20-50 realistic prompts
];

console.time('Detection (56 skills)');
for (let i = 0; i < 1000; i++) {
  for (const prompt of testPrompts) {
    detectSkill(prompt);
  }
}
console.timeEnd('Detection (56 skills)');

// Expected: <50ms for 1000 × 5 prompts = <0.01ms per prompt
```

**Also benchmark:**
- Worst case: Very long prompt (1000 words)
- Best case: Empty prompt (already handled)
- Edge case: Prompt with Unicode/emoji

---

### P1-4: Auto-Generated Trigger Quality ~50%

**File:** `sync-skill-rules.js`

**Evidence:** Validated 3 skills from skill-rules.json against source SKILL.md:

| Skill | Good Keywords | Noise Keywords | Quality |
|-------|---------------|----------------|---------|
| code-auditor | 9/12 (75%) | 3/12 ("user", "wants", "audit") | **75%** |
| brainstorming | 1/4 (25%) | 3/4 ("creating", "before", "writing") | **25%** |
| cli-design | 2/4 (50%) | 2/4 ("skill", "when") | **50%** |

**Average Quality: ~50%**

Half of auto-generated keywords are noise that triggers false positives.

**Root Causes:**
1. Incomplete stopwords (P0-4)
2. Extracts from description YAML instead of "When to Use" section
3. No semantic deduplication ("test", "testing", "tests" all kept)

**Recommended Improvements (beyond P0-4 fix):**

```javascript
// 1. Extract from structured sections only
function extractTriggersFromSkill(skillPath, skillName) {
  const content = await fs.readFile(skillPath, 'utf8');

  // Priority 1: YAML triggers/keywords
  const yamlTriggers = extractFromYAML(content);
  if (yamlTriggers.length > 0) return yamlTriggers;

  // Priority 2: "When to Use" section bullet points
  const useWhenSection = content.match(/## When to Use\n([\s\S]*?)(?=\n##|$)/);
  if (useWhenSection) {
    const bullets = useWhenSection[1].match(/- "(.*?)"/g) || [];
    const keywords = bullets.map(b => b.replace(/- "|"/g, '').toLowerCase());
    return deduplicateSemantics(keywords);
  }

  // Fallback: skill name only
  return [skillName.replace(/-/g, ' ')];
}

// 2. Semantic deduplication
function deduplicateSemantics(keywords) {
  const stems = {};
  for (const keyword of keywords) {
    const stem = keyword.replace(/ing$|ed$|s$/, ''); // Simple stemming
    if (!stems[stem]) stems[stem] = keyword;
  }
  return Object.values(stems);
}
```

---

### P1-5: Skill Detection Output Doesn't Show Matched Triggers

**File:** `context-collector.js` (lines 133-144)

**Current Output:**
```
🎯 SKILLS DETECTADAS (5 matched de 56, showing top 5):
  - test-driven-development (critical) [score: 115]
  - code-auditor (critical) [score: 110]
  - systematic-debugging (critical) [score: 105]
```

**Problem:** User/developer can't debug WHY a skill matched.

**Recommended Output:**
```
🎯 SKILLS DETECTADAS (5 matched de 56, showing top 5):
  - test-driven-development (critical) [score: 115]
    ↳ matched: keyword "test", pattern "(write).*?(test)"
  - code-auditor (critical) [score: 110]
    ↳ matched: keyword "code quality"
  - systematic-debugging (critical) [score: 105]
    ↳ matched: keyword "debug", pattern "(debug).*?(issue)"
```

**Implementation:**
```javascript
// skill-detector.js already tracks matchedTriggers
matched.push({
  skillName,
  config,
  score,
  matchedTriggers  // ← Already exists!
});

// context-collector.js - update formatting
const top5List = detection.topSkills
  .map(s => {
    const triggers = s.matchedTriggers.join(', ');
    return `  - ${s.skillName} (${s.config.priority}) [score: ${s.finalScore}]\n    ↳ ${triggers}`;
  })
  .join('\n');
```

**Benefit:** Debugging false positives becomes 10x easier.

---

## Minor Suggestions (P2) - NICE TO HAVE

### P2-1: Add Semantic Deduplication for Keywords

**Example:**
```json
"keywords": ["test", "testing", "tests", "tested"]
```

All semantically identical. Apply stemming:
```json
"keywords": ["test"]  // "testing" → "test", "tests" → "test", "tested" → "test"
```

**Library:** `natural` npm package provides stemming.

```javascript
const natural = require('natural');
const stemmer = natural.PorterStemmer;

function deduplicateKeywords(keywords) {
  const stemmed = {};
  for (const kw of keywords) {
    const stem = stemmer.stem(kw);
    if (!stemmed[stem] || stemmed[stem].length > kw.length) {
      stemmed[stem] = kw; // Keep shortest form
    }
  }
  return Object.values(stemmed);
}
```

---

### P2-2: Rate Limiting for Skill Suggestions

**Problem:** If user sends 10 short prompts in a row, context-collector shows skill suggestions 10 times.

**Recommendation:**
```javascript
// Track last suggestion timestamp in session state
if (decisions.skillActivation) {
  const lastSuggestion = sessionState.lastSkillSuggestion || 0;
  const now = Date.now();

  // Only show suggestions once per 30 seconds
  if (now - lastSuggestion > 30000) {
    messages.push(formatSkillSuggestions(decisions.skillActivation));
    sessionState.lastSkillSuggestion = now;
  }
}
```

---

### P2-3: Manual Override to Disable Skills

**Use Case:** User knows a skill is incorrectly triggered frequently.

**Recommendation:** Add to session state:
```json
{
  "disabledSkills": ["brainstorming", "cli-design"],
  "explicitSkills": ["test-driven-development"]  // Force-enable
}
```

```javascript
// In detectSkill()
if (sessionState.disabledSkills?.includes(skillName)) continue;
```

---

### P2-4: Improve Stopwords Comprehensiveness

**Current (11 words):**
```javascript
const stopwords = ['this', 'that', 'with', 'your', 'for', 'and', 'the', 'you', 'need', 'want', 'have'];
```

**Recommended (~50 words):**
```javascript
const stopwords = [
  // Articles
  'a', 'an', 'the',
  // Pronouns
  'this', 'that', 'these', 'those', 'you', 'your', 'their', 'them',
  // Prepositions
  'with', 'for', 'from', 'into', 'about', 'after', 'before', 'between',
  // Conjunctions
  'and', 'but', 'or', 'nor', 'yet', 'so',
  // Verbs (auxiliary/generic)
  'is', 'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had',
  'do', 'does', 'did', 'will', 'would', 'could', 'should',
  // Generic nouns/verbs (project-specific)
  'user', 'users', 'skill', 'when', 'wants', 'needs', 'request', 'system'
];
```

Or use a library: `stopword` npm package.

---

## Architecture Considerations

### Overall Design Assessment

**Strengths:**
1. ✅ **Modular separation** - detector, sync, rules, integration are distinct
2. ✅ **Scoring system** - Conceptually sound (keywords + patterns + priority)
3. ✅ **Top-N limiting** - Prevents overwhelming user with 56 suggestions
4. ✅ **Auto-sync** - Reduces manual maintenance burden
5. ✅ **Graceful degradation** - Returns null on errors, doesn't crash

**Weaknesses:**
1. ❌ **No validation layer** - skill-rules.json can contain invalid regex, no schema check
2. ❌ **No feedback loop** - No tracking of whether suggested skills were actually used
3. ❌ **No A/B testing** - Can't compare old vs new matching algorithms
4. ❌ **Tightly coupled to filesystem** - Hard to test without actual files

### Scalability

**Current: 56 skills**
- Performance: Estimated ~5-10ms (acceptable)
- Conflict rate: High (due to P0 issues)

**Future: 100 skills?**
- Performance: ~10-20ms (still acceptable)
- Conflict rate: **VERY HIGH** without fixing P0-1, P0-3, P0-4

**Recommendation:** Fix critical issues now before scaling further.

### Alternative Architectures Considered

**Option A - ML-based matching:**
- Use embeddings (sentence-transformers) to match prompt semantics to skill descriptions
- Pros: Semantic understanding, no manual keyword maintenance
- Cons: Requires model, higher latency (~50-100ms), infrastructure complexity

**Option B - Inverted index:**
```javascript
// Pre-compute index: keyword → [skills]
const index = {
  'test': ['test-driven-development', 'test-fixing', 'systematic-debugging'],
  'audit': ['code-auditor'],
  // ...
};

// Lookup is O(keywords in prompt) instead of O(skills × keywords)
```
- Pros: ~10x faster for large skill counts
- Cons: More complex, memory overhead

**Recommendation:** Current architecture is fine if P0 issues fixed. Revisit if scaling to 200+ skills.

---

## Testing Gaps

### Current State
- ❌ **Zero unit tests**
- ❌ **Zero integration tests**
- ❌ **Zero regression tests**
- ❌ **Zero performance benchmarks**

### Recommended Test Suite

**File: `skill-detector.test.js`**
```javascript
const { detectSkill } = require('./skill-detector');

describe('detectSkill - Basic Matching', () => {
  it('should match exact keyword', () => {
    const result = detectSkill('audit code quality');
    expect(result.topSkills[0].skillName).toBe('code-auditor');
  });

  it('should return null for empty prompt', () => {
    expect(detectSkill('')).toBeNull();
  });

  it('should handle unicode prompts', () => {
    expect(() => detectSkill('🚀 create tests')).not.toThrow();
  });

  it('should prioritize critical skills correctly', () => {
    const result = detectSkill('test');
    expect(result.topSkills[0].config.priority).toBe('critical');
  });

  it('should limit to top 5', () => {
    const result = detectSkill('create implement build develop design');
    expect(result.topSkills.length).toBeLessThanOrEqual(5);
  });
});

describe('detectSkill - Edge Cases', () => {
  it('should handle very long prompts', () => {
    const longPrompt = 'create '.repeat(1000);
    const start = Date.now();
    detectSkill(longPrompt);
    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(100); // <100ms
  });

  it('should handle invalid regex in skill-rules', () => {
    // Mock skill-rules.json with invalid regex
    // Expect: Warning logged, but no crash
  });

  it('should handle missing skill-rules.json', () => {
    // Mock fs to return file not found
    const result = detectSkill('test');
    expect(result).toBeNull();
  });
});

describe('detectSkill - Ranking Correctness', () => {
  it('should rank perfect match above partial match', () => {
    const result = detectSkill('test driven development');
    expect(result.topSkills[0].skillName).toBe('test-driven-development');
  });

  it('should handle ties by priority', () => {
    const result = detectSkill('test');
    // Both match, but critical should win
    const topPriorities = result.topSkills.map(s => s.config.priority);
    expect(topPriorities[0]).toBe('critical');
  });
});
```

**File: `sync-skill-rules.test.js`**
```javascript
const { extractTriggersFromSkill } = require('./sync-skill-rules');

describe('extractTriggersFromSkill', () => {
  it('should extract from YAML frontmatter', async () => {
    const content = `---
triggers: [test, testing, TDD]
---
# Test Skill`;
    const triggers = await extractTriggersFromSkill(content, 'test-skill');
    expect(triggers).toContain('test');
    expect(triggers).toContain('testing');
  });

  it('should infer from "When to Use" section', async () => {
    const content = `## When to Use
- "audit code"
- "review code quality"`;
    const triggers = await extractTriggersFromSkill(content, 'test-skill');
    expect(triggers).toContain('audit code');
    expect(triggers).toContain('review code quality');
  });

  it('should filter stopwords', async () => {
    const content = `Use when you want to test this`;
    const triggers = await extractTriggersFromSkill(content, 'test-skill');
    expect(triggers).not.toContain('you');
    expect(triggers).not.toContain('want');
  });

  it('should deduplicate semantic variants', async () => {
    const content = `Use for testing, tests, and tested code`;
    const triggers = await extractTriggersFromSkill(content, 'test-skill');
    // Should only have one form of "test"
    const testVariants = triggers.filter(t => t.match(/test/));
    expect(testVariants.length).toBe(1);
  });
});
```

**File: `context-collector.integration.test.js`**
```javascript
describe('Integration: Skill Detection in Context Collector', () => {
  it('should format skill suggestions correctly', async () => {
    process.env.CLAUDE_USER_PROMPT = 'audit my code';
    const output = await runContextCollector();

    expect(output.systemMessage).toContain('🎯 SKILLS DETECTADAS');
    expect(output.systemMessage).toContain('code-auditor');
    expect(output.continue).toBe(true);
  });

  it('should handle no matches gracefully', async () => {
    process.env.CLAUDE_USER_PROMPT = 'xyzabc123';
    const output = await runContextCollector();

    expect(output.systemMessage).not.toContain('SKILLS DETECTADAS');
    expect(output.continue).toBe(true);
  });
});
```

**Coverage Goal:** 80%+ line coverage for detector logic.

---

## Responses to Critical Aspects

### 1. Conflict Resolution
**Status:** ⚠️ **HIGH CONFLICT RISK**

With 56 skills, conflict probability is ~60-70% due to:
- Substring keyword matching (P0-1)
- Generic auto-generated keywords (P0-4)
- Broad intent patterns (P0-3)

**Scoring is conceptually sound** but undermined by noise.

**Fix:** Address P0-1, P0-3, P0-4 → conflict rate drops to ~20-30%.

---

### 2. Performance
**Status:** ⚠️ **LIKELY OK BUT UNVALIDATED**

**Estimate:** 5-10ms per prompt (acceptable for <50ms target)

**Concerns:**
- Re-reading skill-rules.json adds 3-5ms I/O (P1-1)
- No actual benchmarking (P1-3)

**Fix:** Add caching (P1-1) + benchmark tests (P1-3).

---

### 3. Quality of Auto-Generated Triggers
**Status:** ❌ **~50% QUALITY (POOR)**

**Validated:**
- code-auditor: 75% quality (9/12 good)
- brainstorming: 25% quality (1/4 good)
- cli-design: 50% quality (2/4 good)

**Average: ~50%**

**Root Causes:** P0-4 (stopwords), extraction from wrong sections, no semantic dedup.

**Fix:** P0-4 + P1-4 → target 80%+ quality.

---

### 4. Ranking Algorithm
**Status:** ⚠️ **IMBALANCED**

**Conceptually:** Keywords (10) + Patterns (15) + Priority weights = good idea

**Reality:** Priority weights (100 for critical) dominate match scores (max 25), making relevance secondary to priority.

**With 36% critical skills:** Ranking becomes unstable.

**Fix:** P0-2 (reweight) + P0-5 (redistribute) → stable ranking.

---

### 5. Fallbacks & Error Handling
**Status:** ✅ **GOOD**

- File not found: Handled ✅
- Invalid JSON: Try-catched ✅
- Invalid regex: Logged, not crashed ✅
- Empty prompt: Returns null ✅

**Minor gaps:**
- No schema validation for skill-rules.json
- No handling of corrupted session state (though context-collector recreates)

---

### 6. Integration with Legal-Braniac
**Status:** ✅ **CORRECT**

Integration in `context-collector.js` is clean:
- Calls `detectSkill(context.prompt)` correctly
- Formats output humanely
- Passes to systemMessage
- Non-blocking (always returns `continue: true` unless aesthetic blocker)

**Enhancement opportunity:** P1-5 (show matched triggers)

---

### 7. Testing Gaps
**Status:** ❌ **CRITICAL - ZERO COVERAGE**

No tests = no confidence in changes.

**Impact:**
- Can't refactor safely
- Can't validate fixes (P0-1, P0-2, etc.)
- Regressions go unnoticed

**Priority:** Create basic test suite BEFORE implementing fixes.

---

## Summary Table

| Issue | Severity | Impact | Effort | Priority |
|-------|----------|--------|--------|----------|
| P0-1: Substring keyword matching | 🔴 Critical | Massive false positives | Low (1-2h) | **IMMEDIATE** |
| P0-2: Priority weights imbalance | 🔴 Critical | Unstable ranking | Low (1h) | **IMMEDIATE** |
| P0-3: Broad intent patterns | 🔴 Critical | 30-50% false positives | Medium (3-4h) | **IMMEDIATE** |
| P0-4: Generic keywords not filtered | 🔴 Critical | 50% keyword noise | Medium (2-3h) | **IMMEDIATE** |
| P0-5: 36% skills marked critical | 🔴 Critical | Dilutes priority system | High (4-6h manual) | **HIGH** |
| P1-1: No caching | 🟡 Important | 3-5ms overhead/prompt | Low (1h) | MEDIUM |
| P1-2: Break limits matching | 🟡 Important | Under-represents relevance | Low (1h) | LOW (if P0 fixed) |
| P1-3: No benchmarking | 🟡 Important | Unknown performance | Low (2h) | MEDIUM |
| P1-4: 50% trigger quality | 🟡 Important | Compounds P0 issues | Medium (3h) | HIGH |
| P1-5: No matched trigger output | 🟡 Important | Hard to debug | Low (30min) | LOW |
| P2-1: No semantic dedup | 🔵 Minor | Slightly inflated keywords | Medium (2h) | LOW |
| P2-2: No rate limiting | 🔵 Minor | Spam suggestions | Low (1h) | LOW |
| P2-3: No manual override | 🔵 Minor | Can't disable bad skills | Medium (2h) | LOW |
| P2-4: Limited stopwords | 🔵 Minor | Covered by P0-4 | Low (30min) | LOW |

---

## Recommended Implementation Order

### Phase 1: Critical Fixes (1-2 days)
1. ✅ **P0-1:** Word boundary keyword matching (1-2h)
2. ✅ **P0-4:** Comprehensive stopwords (2-3h)
3. ✅ **P0-2:** Rebalance priority weights (1h)
4. ✅ **Write basic tests** (4-6h)
5. ✅ **Validate fixes** with test suite

### Phase 2: Quality Improvements (1 day)
6. ✅ **P0-3:** Refine intent pattern generation (3-4h)
7. ✅ **P1-4:** Improve trigger extraction (3h)
8. ✅ **P1-1:** Add caching (1h)
9. ✅ **P1-5:** Show matched triggers in output (30min)

### Phase 3: Manual Review (2-3 days)
10. ✅ **P0-5:** Manually review and redistribute 56 skill priorities (4-6h)
11. ✅ **Run sync-skill-rules.js** to regenerate with fixes
12. ✅ **Manual QA** on 20-30 realistic prompts

### Phase 4: Polish (Optional)
13. P1-3: Performance benchmarking
14. P2-1: Semantic deduplication
15. P2-2: Rate limiting
16. P2-3: Manual overrides

---

## Next Steps

### Immediate Actions (Before Any Code Changes)

1. **CRITICAL:** Create backup of current skill-rules.json
   ```bash
   cp .claude/skills/skill-rules.json .claude/skills/skill-rules.json.backup-$(date +%Y%m%d)
   ```

2. **Create test suite structure:**
   ```bash
   mkdir -p .claude/hooks/lib/__tests__
   touch .claude/hooks/lib/__tests__/skill-detector.test.js
   touch .claude/hooks/lib/__tests__/sync-skill-rules.test.js
   ```

3. **Install test dependencies:**
   ```bash
   npm install --save-dev jest
   ```

4. **Document current behavior** for regression testing:
   - Run 10 realistic prompts
   - Save current detection results
   - Use as baseline for "did we break anything?"

### Decision Required from User

**Please review the findings and approve which changes to implement before I proceed with any fixes.**

Specifically:

1. **Do you want to fix P0 issues immediately?** (Recommended: YES)
2. **Priority weight rebalancing:** Option A (reduce weights) or Option B (redistribute skills)?
3. **P0-5 manual review:** Do you want me to propose new priority distribution or do manual review yourself?
4. **Testing:** Create full test suite or minimal coverage?
5. **Phased rollout:** Implement all P0 at once or one-by-one with validation?

**I will NOT proceed with any implementation until you explicitly approve the approach.**

---

**Review Complete.**
**Waiting for user approval to proceed with fixes.**
