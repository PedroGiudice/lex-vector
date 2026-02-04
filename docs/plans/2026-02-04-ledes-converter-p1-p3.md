# LEDES Converter Improvements P1-P3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Matter Presets, Task/Activity Code Auto-Mapping, Batch Processing, and Line Item Editing for the LEDES Converter.

**Architecture:** Backend receives task_code/activity_code per line item (not global). Frontend manages presets in localStorage and allows multi-file upload. Task codes are inferred from line item descriptions using keyword matching.

**Tech Stack:** FastAPI (Python), React 18, TypeScript, Zustand, TailwindCSS

---

## Overview

| Priority | Feature | Complexity | Files |
|----------|---------|------------|-------|
| P1 | Matter Presets | Medium | Frontend only |
| P1 | Task Code Auto-Mapping | Medium | Backend + Frontend |
| P2 | Activity Code Mapping | Simple | Backend (extend P1) |
| P2 | Batch Processing | Medium | Backend + Frontend |
| P3 | Line Item Editing | High | Frontend only |

---

## Task 1: Create UTBMS Code Mapper Module (Backend)

**Files:**
- Create: `legal-workbench/docker/services/ledes-converter/api/utbms_mapper.py`
- Test: `legal-workbench/docker/services/ledes-converter/test_utbms_mapper.py`

**Step 1: Write the failing test**

```python
# test_utbms_mapper.py
import pytest
from api.utbms_mapper import infer_task_code, infer_activity_code

class TestTaskCodeMapping:
    """Test UTBMS task code inference from line item descriptions."""

    def test_appeals_task_code(self):
        """Appeals-related descriptions should map to L510."""
        assert infer_task_code("Draft and file Special Appeal") == "L510"
        assert infer_task_code("Prepare recurso especial") == "L510"
        assert infer_task_code("File agravo de instrumento") == "L510"
        assert infer_task_code("STJ appeal preparation") == "L510"

    def test_pleadings_task_code(self):
        """Pleadings descriptions should map to L210."""
        assert infer_task_code("Prepare defense motion") == "L210"
        assert infer_task_code("Draft contestacao") == "L210"
        assert infer_task_code("File answer to complaint") == "L210"

    def test_motions_task_code(self):
        """Motion descriptions should map to L250."""
        assert infer_task_code("File motion to dismiss") == "L250"
        assert infer_task_code("Prepare petition for relief") == "L250"
        assert infer_task_code("Draft requerimento") == "L250"

    def test_settlement_task_code(self):
        """Settlement/ADR descriptions should map to L160."""
        assert infer_task_code("Settlement negotiation") == "L160"
        assert infer_task_code("Mediation preparation") == "L160"
        assert infer_task_code("Draft acordo") == "L160"

    def test_research_task_code(self):
        """Research descriptions should map to L110."""
        assert infer_task_code("Legal research on precedents") == "L110"
        assert infer_task_code("Jurisprudence analysis") == "L110"
        assert infer_task_code("Case law research") == "L110"

    def test_default_task_code(self):
        """Unknown descriptions should return default L100."""
        assert infer_task_code("General legal work") == "L100"
        assert infer_task_code("") == "L100"
        assert infer_task_code("xyz random text") == "L100"

    def test_custom_default(self):
        """Should accept custom default code."""
        assert infer_task_code("unknown work", default="L999") == "L999"


class TestActivityCodeMapping:
    """Test UTBMS activity code inference from line item descriptions."""

    def test_draft_activity_code(self):
        """Draft/write descriptions should map to A103."""
        assert infer_activity_code("Draft motion") == "A103"
        assert infer_activity_code("Prepare document") == "A103"
        assert infer_activity_code("Write brief") == "A103"
        assert infer_activity_code("Redigir petição") == "A103"

    def test_review_activity_code(self):
        """Review/analyze descriptions should map to A104."""
        assert infer_activity_code("Review contract") == "A104"
        assert infer_activity_code("Analyze documents") == "A104"
        assert infer_activity_code("Revisar processo") == "A104"

    def test_communicate_activity_code(self):
        """Communication descriptions should map to A106."""
        assert infer_activity_code("Client meeting") == "A106"
        assert infer_activity_code("Phone conference") == "A106"
        assert infer_activity_code("Email correspondence") == "A106"
        assert infer_activity_code("Reunião com cliente") == "A106"

    def test_research_activity_code(self):
        """Research descriptions should map to A102."""
        assert infer_activity_code("Legal research") == "A102"
        assert infer_activity_code("Research case law") == "A102"
        assert infer_activity_code("Pesquisa jurisprudencial") == "A102"

    def test_appear_activity_code(self):
        """Appearance descriptions should map to A105."""
        assert infer_activity_code("Court appearance") == "A105"
        assert infer_activity_code("Attend hearing") == "A105"
        assert infer_activity_code("Audiência") == "A105"

    def test_default_activity_code(self):
        """Unknown descriptions should return default A103."""
        assert infer_activity_code("General work") == "A103"
        assert infer_activity_code("") == "A103"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/opc/lex-vector/legal-workbench/docker/services/ledes-converter && python -m pytest test_utbms_mapper.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'api.utbms_mapper'"

**Step 3: Write minimal implementation**

```python
# api/utbms_mapper.py
"""
UTBMS Code Mapper for LEDES 1998B

Maps line item descriptions to appropriate UTBMS task and activity codes
based on keyword matching.

UTBMS Task Codes (Litigation):
- L100: Case Assessment, Development and Administration
- L110: Fact Investigation/Development
- L120: Analysis/Strategy
- L130: Experts/Consultants
- L140: Document/File Management
- L150: Budgeting
- L160: Settlement/Non-Binding ADR
- L210: Pleadings
- L220: Interrogatories
- L230: Depositions
- L240: Document Production
- L250: Other Written Motions/Submissions
- L310: Trial Preparation
- L320: Trial/Hearing Attendance
- L330: Post-Trial Motions
- L510: Appeals

UTBMS Activity Codes:
- A101: Plan and prepare for
- A102: Research
- A103: Draft/Revise
- A104: Review/Analyze
- A105: Appear for/Attend
- A106: Communicate (with client, other counsel, etc.)
- A107: Travel
- A108: Other
"""

from typing import Dict, List

# Task code patterns: code -> list of keywords (case-insensitive)
TASK_CODE_PATTERNS: Dict[str, List[str]] = {
    "L510": [  # Appeals
        "appeal", "recurso", "stj", "stf", "agravo", "embargo",
        "recurso especial", "recurso extraordinário", "apelação",
        "recurso ordinário", "embargos de declaração"
    ],
    "L210": [  # Pleadings
        "defense", "defesa", "contestação", "resposta", "answer",
        "complaint", "pleading", "réplica", "tréplica"
    ],
    "L250": [  # Other Written Motions
        "motion", "petition", "petição", "requerimento", "moção",
        "motion to dismiss", "motion for summary", "tutela"
    ],
    "L160": [  # Settlement/ADR
        "settlement", "acordo", "negociação", "mediation", "mediação",
        "arbitration", "arbitragem", "conciliação", "adr"
    ],
    "L110": [  # Fact Investigation
        "research", "pesquisa", "jurisprudência", "investigation",
        "investigação", "case law", "precedent", "diligência"
    ],
    "L120": [  # Analysis/Strategy
        "analysis", "análise", "strategy", "estratégia", "parecer",
        "opinion", "assessment", "avaliação"
    ],
    "L230": [  # Depositions
        "deposition", "interrogatório", "oitiva", "depoimento",
        "testemunha", "witness"
    ],
    "L320": [  # Trial/Hearing
        "trial", "julgamento", "hearing", "audiência",
        "sustentação oral", "oral argument"
    ],
    "L140": [  # Document Management
        "document", "documento", "file", "arquivo", "organize",
        "organizar", "index", "indexar"
    ],
}

# Activity code patterns: code -> list of keywords (case-insensitive)
ACTIVITY_CODE_PATTERNS: Dict[str, List[str]] = {
    "A103": [  # Draft/Revise
        "draft", "redigir", "prepare", "preparar", "write", "escrever",
        "elaborar", "revise", "revisar documento", "update", "atualizar"
    ],
    "A104": [  # Review/Analyze
        "review", "revisar", "analyze", "analisar", "examine", "examinar",
        "study", "estudar", "avaliar"
    ],
    "A106": [  # Communicate
        "meeting", "reunião", "conference", "conferência", "call", "ligação",
        "email", "correspond", "discuss", "discutir", "communicate", "comunicar"
    ],
    "A102": [  # Research
        "research", "pesquisa", "investigate", "investigar", "study",
        "jurisprudência", "case law", "precedent"
    ],
    "A105": [  # Appear/Attend
        "appear", "comparecer", "attend", "audiência", "hearing",
        "court", "tribunal", "fórum"
    ],
    "A101": [  # Plan and prepare
        "plan", "planejar", "prepare for", "preparar para",
        "strategy", "estratégia"
    ],
    "A107": [  # Travel
        "travel", "viagem", "deslocamento", "trip"
    ],
}


def infer_task_code(description: str, default: str = "L100") -> str:
    """
    Infer UTBMS task code from line item description.

    Args:
        description: The line item description text
        default: Default code if no pattern matches (default: L100)

    Returns:
        UTBMS task code (e.g., "L510", "L210")
    """
    if not description:
        return default

    desc_lower = description.lower()

    for code, patterns in TASK_CODE_PATTERNS.items():
        for pattern in patterns:
            if pattern in desc_lower:
                return code

    return default


def infer_activity_code(description: str, default: str = "A103") -> str:
    """
    Infer UTBMS activity code from line item description.

    Args:
        description: The line item description text
        default: Default code if no pattern matches (default: A103 - Draft/Revise)

    Returns:
        UTBMS activity code (e.g., "A103", "A106")
    """
    if not description:
        return default

    desc_lower = description.lower()

    for code, patterns in ACTIVITY_CODE_PATTERNS.items():
        for pattern in patterns:
            if pattern in desc_lower:
                return code

    return default
```

**Step 4: Run test to verify it passes**

Run: `cd /home/opc/lex-vector/legal-workbench/docker/services/ledes-converter && python -m pytest test_utbms_mapper.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add legal-workbench/docker/services/ledes-converter/api/utbms_mapper.py legal-workbench/docker/services/ledes-converter/test_utbms_mapper.py
git commit -m "feat(ledes): add UTBMS task/activity code mapper

- Add infer_task_code() for mapping descriptions to UTBMS task codes
- Add infer_activity_code() for mapping descriptions to activity codes
- Support Portuguese and English keywords
- Comprehensive test coverage for all code categories

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Integrate UTBMS Mapper into Backend

**Files:**
- Modify: `legal-workbench/docker/services/ledes-converter/api/main.py:275-360`

**Step 1: Write the failing test**

Add to existing `test_api.py`:

```python
# Add to test_api.py
def test_auto_task_code_mapping():
    """Test that task codes are automatically inferred per line item."""
    # Create a DOCX with multiple line items
    doc = Document()
    doc.add_paragraph("Invoice: #TEST-AUTO-001")
    doc.add_paragraph("Date of Issuance: January 15, 2026")
    doc.add_paragraph("Draft and file Special Appeal US $1200")  # Should be L510
    doc.add_paragraph("Settlement negotiation US $800")  # Should be L160
    doc.add_paragraph("Legal research on precedents US $600")  # Should be L110
    doc.add_paragraph("Total Gross Amount: US $2600")

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        doc.save(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/convert/docx-to-ledes",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"config": json.dumps({
                    "law_firm_id": "FIRM-001",
                    "law_firm_name": "Test Firm",
                    "client_id": "CLIENT-001",
                    "matter_id": "MATTER-001",
                    "auto_map_codes": True  # Enable auto-mapping
                })}
            )

        assert response.status_code == 200
        data = response.json()
        ledes_lines = data["ledes_content"].split("\r\n")

        # Check that different task codes were assigned
        # Line 3 (first data row) should have L510 for appeals
        assert "|L510|" in ledes_lines[2]
        # Line 4 should have L160 for settlement
        assert "|L160|" in ledes_lines[3]
        # Line 5 should have L110 for research
        assert "|L110|" in ledes_lines[4]
    finally:
        os.unlink(tmp_path)
```

**Step 2: Run test to verify it fails**

Run: `cd /home/opc/lex-vector/legal-workbench/docker/services/ledes-converter && python -m pytest test_api.py::test_auto_task_code_mapping -v`
Expected: FAIL (auto_map_codes not implemented)

**Step 3: Modify main.py to use UTBMS mapper**

In `main.py`, add import and modify `generate_ledes_1998b`:

```python
# Add at top of main.py after other imports
from .utbms_mapper import infer_task_code, infer_activity_code

# Modify generate_ledes_1998b function (around line 275)
def generate_ledes_1998b(data: dict) -> str:
    """
    Generate LEDES 1998B format from extracted data.

    Now supports automatic UTBMS code mapping per line item when
    auto_map_codes=True in the config.
    """
    # ... existing code ...

    # Get auto-mapping flag from config
    auto_map_codes = data.get("auto_map_codes", True)  # Default to True

    # Data rows: Each line item becomes a row with 24 fields
    for i, item in enumerate(data["line_items"], 1):
        # Infer task/activity codes if auto-mapping is enabled
        if auto_map_codes:
            item_task_code = infer_task_code(item["description"], default_task_code)
            item_activity_code = infer_activity_code(item["description"], default_activity_code)
        else:
            item_task_code = item.get("task_code", default_task_code)
            item_activity_code = item.get("activity_code", default_activity_code)

        # ... rest of row building code, using item_task_code and item_activity_code ...
```

**Step 4: Run test to verify it passes**

Run: `cd /home/opc/lex-vector/legal-workbench/docker/services/ledes-converter && python -m pytest test_api.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add legal-workbench/docker/services/ledes-converter/api/main.py legal-workbench/docker/services/ledes-converter/test_api.py
git commit -m "feat(ledes): integrate auto UTBMS code mapping per line item

- Import and use infer_task_code/infer_activity_code
- Each line item gets appropriate code based on description
- Add auto_map_codes config flag (default: true)
- Add test for multi-code invoice

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Add Matter Presets to Frontend Types

**Files:**
- Modify: `legal-workbench/frontend/src/types/index.ts:71-89`

**Step 1: Add MatterPreset interface**

```typescript
// Add after LedesConfig interface (around line 89)

/**
 * Matter Preset - Pre-configured settings for a specific client/matter combination.
 * Allows users to save and quickly apply configurations.
 */
export interface MatterPreset {
  id: string;
  name: string;                    // Display name (e.g., "Salesforce Litigation")
  // Client/Matter identifiers
  clientId: string;
  clientName: string;
  matterId: string;
  matterName: string;
  clientMatterId?: string;
  // Firm info
  lawFirmId: string;
  lawFirmName: string;
  // Timekeeper defaults
  timekeeperId: string;
  timekeeperName: string;
  timekeeperClassification: string;
  unitCost: number;
  // Default UTBMS codes (can be overridden by auto-mapping)
  defaultTaskCode: string;
  defaultActivityCode: string;
  // Metadata
  createdAt: string;
  updatedAt: string;
}

/**
 * Input for creating a new preset (id and timestamps auto-generated)
 */
export type MatterPresetInput = Omit<MatterPreset, 'id' | 'createdAt' | 'updatedAt'>;
```

**Step 2: Run build to verify**

Run: `cd /home/opc/lex-vector/legal-workbench/frontend && bun run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add legal-workbench/frontend/src/types/index.ts
git commit -m "feat(ledes): add MatterPreset type definitions

- Add MatterPreset interface for saved configurations
- Include all fields needed for quick matter selection
- Add MatterPresetInput type for creation

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Create Matter Presets Store

**Files:**
- Create: `legal-workbench/frontend/src/store/matterPresetsStore.ts`

**Step 1: Create the store**

```typescript
// matterPresetsStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { MatterPreset, MatterPresetInput } from '@/types';

const STORAGE_KEY = 'ledes_matter_presets';

interface MatterPresetsState {
  presets: MatterPreset[];
  selectedPresetId: string | null;

  // Actions
  addPreset: (input: MatterPresetInput) => MatterPreset;
  updatePreset: (id: string, updates: Partial<MatterPresetInput>) => void;
  deletePreset: (id: string) => void;
  selectPreset: (id: string | null) => void;
  getPreset: (id: string) => MatterPreset | undefined;
  getSelectedPreset: () => MatterPreset | undefined;
}

/**
 * Generate a simple unique ID (no external deps needed)
 */
const generateId = (): string => {
  return `preset_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
};

export const useMatterPresetsStore = create<MatterPresetsState>()(
  persist(
    (set, get) => ({
      presets: [],
      selectedPresetId: null,

      addPreset: (input: MatterPresetInput): MatterPreset => {
        const now = new Date().toISOString();
        const newPreset: MatterPreset = {
          ...input,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        };

        set((state) => ({
          presets: [...state.presets, newPreset],
        }));

        return newPreset;
      },

      updatePreset: (id: string, updates: Partial<MatterPresetInput>) => {
        set((state) => ({
          presets: state.presets.map((preset) =>
            preset.id === id
              ? { ...preset, ...updates, updatedAt: new Date().toISOString() }
              : preset
          ),
        }));
      },

      deletePreset: (id: string) => {
        set((state) => ({
          presets: state.presets.filter((preset) => preset.id !== id),
          selectedPresetId: state.selectedPresetId === id ? null : state.selectedPresetId,
        }));
      },

      selectPreset: (id: string | null) => {
        set({ selectedPresetId: id });
      },

      getPreset: (id: string): MatterPreset | undefined => {
        return get().presets.find((preset) => preset.id === id);
      },

      getSelectedPreset: (): MatterPreset | undefined => {
        const { presets, selectedPresetId } = get();
        return selectedPresetId ? presets.find((p) => p.id === selectedPresetId) : undefined;
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        presets: state.presets,
        // Don't persist selectedPresetId - user should re-select each session
      }),
    }
  )
);
```

**Step 2: Run build to verify**

Run: `cd /home/opc/lex-vector/legal-workbench/frontend && bun run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add legal-workbench/frontend/src/store/matterPresetsStore.ts
git commit -m "feat(ledes): add Matter Presets Zustand store

- CRUD operations for presets
- localStorage persistence via zustand/persist
- Selection state for active preset

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Add Matter Preset Selector to UI

**Files:**
- Modify: `legal-workbench/frontend/src/pages/LedesConverterModule.tsx`

**Step 1: Add preset selector component and integration**

Add after the Icons object (around line 227), before the main component:

```typescript
// Add import at top
import { useMatterPresetsStore } from '@/store/matterPresetsStore';
import type { MatterPreset, MatterPresetInput } from '@/types';

// Add PresetSelector component after Icons object
const PresetSelector = ({
  onSelect,
  onSaveNew,
  currentConfig,
}: {
  onSelect: (preset: MatterPreset) => void;
  onSaveNew: (name: string) => void;
  currentConfig: LEDESConfig;
}) => {
  const { presets, selectedPresetId, selectPreset, deletePreset } = useMatterPresetsStore();
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');

  const handleSelect = (presetId: string) => {
    const preset = presets.find(p => p.id === presetId);
    if (preset) {
      selectPreset(presetId);
      onSelect(preset);
    }
  };

  const handleSave = () => {
    if (newPresetName.trim()) {
      onSaveNew(newPresetName.trim());
      setNewPresetName('');
      setShowSaveDialog(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Preset Dropdown */}
      <div className="flex flex-col gap-2">
        <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
          Matter Preset
        </label>
        <div className="flex gap-2">
          <select
            value={selectedPresetId || ''}
            onChange={(e) => handleSelect(e.target.value)}
            className="flex-1 bg-[#121214] border-2 border-zinc-800 rounded-sm px-4 py-3 text-sm text-zinc-200 outline-none focus:border-violet-500"
          >
            <option value="">-- Select Preset --</option>
            {presets.map((preset) => (
              <option key={preset.id} value={preset.id}>
                {preset.name} ({preset.clientId})
              </option>
            ))}
          </select>
          {selectedPresetId && (
            <button
              onClick={() => {
                if (confirm('Delete this preset?')) {
                  deletePreset(selectedPresetId);
                }
              }}
              className="px-3 py-2 bg-rose-950/30 border border-rose-900 text-rose-400 rounded-sm hover:bg-rose-900/40"
            >
              <Icons.Trash size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Save New Preset */}
      {!showSaveDialog ? (
        <Button
          variant="ghost"
          onClick={() => setShowSaveDialog(true)}
          className="w-full text-xs"
          icon={Icons.Save}
        >
          Save Current as Preset
        </Button>
      ) : (
        <div className="flex gap-2">
          <input
            type="text"
            value={newPresetName}
            onChange={(e) => setNewPresetName(e.target.value)}
            placeholder="Preset name..."
            className="flex-1 bg-[#121214] border-2 border-zinc-800 rounded-sm px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500"
            autoFocus
          />
          <Button variant="primary" onClick={handleSave} className="px-4">
            Save
          </Button>
          <Button variant="ghost" onClick={() => setShowSaveDialog(false)} className="px-3">
            X
          </Button>
        </div>
      )}
    </div>
  );
};
```

Then in the main component, add the preset handling:

```typescript
// Inside LedesConverterModule, add after existing state declarations:
const { addPreset } = useMatterPresetsStore();

// Add handlers:
const handlePresetSelect = useCallback((preset: MatterPreset) => {
  setConfig({
    ...config,
    lawFirmId: preset.lawFirmId,
    lawFirmName: preset.lawFirmName,
    clientId: preset.clientId,
    clientName: preset.clientName,
    matterId: preset.matterId,
    matterName: preset.matterName,
    timekeeperId: preset.timekeeperId,
    timekeeperName: preset.timekeeperName,
    timekeeperClassification: preset.timekeeperClassification,
    unitCost: preset.unitCost,
    taskCode: preset.defaultTaskCode,
    activityCode: preset.defaultActivityCode,
  });
  addLog(`Loaded preset: ${preset.name}`);
}, [config, addLog]);

const handleSavePreset = useCallback((name: string) => {
  const presetInput: MatterPresetInput = {
    name,
    clientId: config.clientId,
    clientName: config.clientName,
    matterId: config.matterId,
    matterName: config.matterName,
    lawFirmId: config.lawFirmId,
    lawFirmName: config.lawFirmName,
    timekeeperId: config.timekeeperId,
    timekeeperName: config.timekeeperName,
    timekeeperClassification: config.timekeeperClassification,
    unitCost: config.unitCost,
    defaultTaskCode: config.taskCode,
    defaultActivityCode: config.activityCode,
  };
  addPreset(presetInput);
  addLog(`Saved preset: ${name}`);
}, [config, addPreset, addLog]);
```

Add PresetSelector to the sidebar (after the Config header):

```tsx
{/* Add after the Config header div, before Navigation Pills */}
<div className="px-8 py-4 border-b border-zinc-800/50">
  <PresetSelector
    onSelect={handlePresetSelect}
    onSaveNew={handleSavePreset}
    currentConfig={config}
  />
</div>
```

**Step 2: Run build to verify**

Run: `cd /home/opc/lex-vector/legal-workbench/frontend && bun run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add legal-workbench/frontend/src/pages/LedesConverterModule.tsx
git commit -m "feat(ledes): add Matter Preset selector UI

- Add PresetSelector component with dropdown
- Save current config as new preset
- Delete presets
- Auto-fill config when preset selected

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Add Batch Processing Backend Endpoint

**Files:**
- Modify: `legal-workbench/docker/services/ledes-converter/api/main.py`
- Modify: `legal-workbench/docker/services/ledes-converter/api/models.py`

**Step 1: Add batch models**

```python
# Add to models.py
from typing import List

class BatchConversionRequest(BaseModel):
    """Request for batch conversion (multiple files)."""
    config: Optional[LedesConfig] = None
    consolidate: bool = Field(default=False, description="Combine all into single LEDES file")

class BatchFileResult(BaseModel):
    """Result for a single file in batch processing."""
    filename: str
    status: str  # "success" or "error"
    error: Optional[str] = None
    extracted_data: Optional[LedesData] = None
    ledes_content: Optional[str] = None

class BatchConversionResponse(BaseModel):
    """API response for batch conversion."""
    total_files: int
    successful: int
    failed: int
    results: List[BatchFileResult]
    consolidated_content: Optional[str] = None  # If consolidate=True
```

**Step 2: Add batch endpoint to main.py**

```python
# Add after the existing /convert/docx-to-ledes endpoint

@app.post("/convert/batch", response_model=BatchConversionResponse)
async def convert_batch(
    request: Request,
    files: Annotated[list[UploadFile], File(description="DOCX files to convert (max 10)")],
    config: Annotated[Optional[str], Form(description="JSON config")] = None,
    consolidate: Annotated[bool, Form(description="Combine into single LEDES")] = False
) -> BatchConversionResponse:
    """
    Convert multiple DOCX invoice files to LEDES 1998B format.

    - **files**: List of DOCX files (max 10, each max 10MB)
    - **config**: Optional JSON string with LEDES configuration
    - **consolidate**: If True, combine all line items into single LEDES file
    """
    # Validate file count
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch.")

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    # Rate limiting (stricter for batch)
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit_check(client_ip, max_requests=5, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many requests.")

    # Parse config once
    ledes_config = None
    if config:
        try:
            config_dict = json.loads(config)
            ledes_config = LedesConfig(**config_dict)
        except (json.JSONDecodeError, Exception) as e:
            raise HTTPException(status_code=400, detail=f"Invalid config: {e}")

    results = []
    all_line_items = []
    base_data = None

    for file in files:
        try:
            # Reuse existing single-file logic
            content = await file.read()

            # Validate
            if len(content) > MAX_FILE_SIZE:
                results.append(BatchFileResult(
                    filename=file.filename or "unknown",
                    status="error",
                    error="File too large (max 10MB)"
                ))
                continue

            if not validate_file_type(content, file.filename or ""):
                results.append(BatchFileResult(
                    filename=file.filename or "unknown",
                    status="error",
                    error="Invalid file format"
                ))
                continue

            # Process
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", mode='wb') as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                doc = docx.Document(tmp_path)
                full_text = []
                for para in doc.paragraphs:
                    if para.text:
                        full_text.append(para.text)
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text:
                                full_text.append(cell.text)

                text_content = "\n".join(full_text)
                extracted_data = extract_ledes_data(text_content)

                # Apply config
                if ledes_config:
                    extracted_data["law_firm_id"] = ledes_config.law_firm_id
                    extracted_data["client_id"] = ledes_config.client_id
                    extracted_data["matter_id"] = ledes_config.matter_id
                    # ... (same as single file)

                # Generate LEDES for this file
                ledes_content = generate_ledes_1998b(extracted_data)

                # Collect for consolidation
                if consolidate:
                    if base_data is None:
                        base_data = extracted_data.copy()
                    all_line_items.extend(extracted_data["line_items"])

                line_items = [LineItem(**item) for item in extracted_data["line_items"]]
                ledes_data = LedesData(
                    invoice_date=extracted_data["invoice_date"],
                    invoice_number=extracted_data["invoice_number"],
                    client_id=extracted_data["client_id"],
                    matter_id=extracted_data["matter_id"],
                    invoice_total=extracted_data["invoice_total"],
                    line_items=line_items
                )

                results.append(BatchFileResult(
                    filename=file.filename or "unknown",
                    status="success",
                    extracted_data=ledes_data,
                    ledes_content=ledes_content
                ))
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            logger.error(f"Batch file error: {e}")
            results.append(BatchFileResult(
                filename=file.filename or "unknown",
                status="error",
                error=str(e)
            ))

    # Generate consolidated LEDES if requested
    consolidated_content = None
    if consolidate and base_data and all_line_items:
        base_data["line_items"] = all_line_items
        base_data["invoice_total"] = sum(item["amount"] for item in all_line_items)
        consolidated_content = generate_ledes_1998b(base_data)

    successful = sum(1 for r in results if r.status == "success")

    return BatchConversionResponse(
        total_files=len(files),
        successful=successful,
        failed=len(files) - successful,
        results=results,
        consolidated_content=consolidated_content
    )
```

**Step 3: Run tests**

Run: `cd /home/opc/lex-vector/legal-workbench/docker/services/ledes-converter && python -m pytest test_api.py -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add legal-workbench/docker/services/ledes-converter/api/main.py legal-workbench/docker/services/ledes-converter/api/models.py
git commit -m "feat(ledes): add batch processing endpoint

- POST /convert/batch for up to 10 files
- Optional consolidate mode for single output
- Stricter rate limiting for batch
- Individual error handling per file

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Add Batch Processing UI

**Files:**
- Modify: `legal-workbench/frontend/src/pages/LedesConverterModule.tsx`
- Modify: `legal-workbench/frontend/src/services/ledesConverterApi.ts`
- Modify: `legal-workbench/frontend/src/store/ledesConverterStore.ts`

**Step 1: Update API service**

```typescript
// Add to ledesConverterApi.ts

export interface BatchFileResult {
  filename: string;
  status: 'success' | 'error';
  error?: string;
  extracted_data?: LedesExtractedData;
  ledes_content?: string;
}

export interface BatchConversionResponse {
  total_files: number;
  successful: number;
  failed: number;
  results: BatchFileResult[];
  consolidated_content?: string;
}

// Add to ledesConverterApi object:
convertBatch: async (
  files: File[],
  config?: LedesConfig,
  consolidate: boolean = false,
  onProgress?: (progress: number) => void
): Promise<BatchConversionResponse> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  if (config) {
    formData.append('config', JSON.stringify({
      law_firm_id: config.lawFirmId,
      law_firm_name: config.lawFirmName,
      client_id: config.clientId,
      matter_id: config.matterId,
      // ... other fields
    }));
  }

  formData.append('consolidate', String(consolidate));

  const response = await axios.post<BatchConversionResponse>(
    `${API_BASE_URL}/convert/batch`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
      timeout: 120000, // 2 min for batch
    }
  );

  return response.data;
},
```

**Step 2: Update store for batch mode**

```typescript
// Add to ledesConverterStore.ts state interface:
files: File[];  // Change from single file to array
batchMode: boolean;
batchResults: BatchFileResult[];

// Add actions:
setFiles: (files: File[]) => void;
setBatchMode: (enabled: boolean) => void;
convertBatch: () => Promise<void>;
```

**Step 3: Update UI for multi-file selection**

Modify the file input in LedesConverterModule.tsx:

```tsx
<input
  type="file"
  ref={fileInputRef}
  onChange={handleFileUpload}
  className="hidden"
  accept=".docx"
  multiple  // Enable multi-select
/>
```

Add batch mode toggle and file list display.

**Step 4: Run build and test**

Run: `cd /home/opc/lex-vector/legal-workbench/frontend && bun run build`
Expected: Build succeeds

**Step 5: Commit**

```bash
git add legal-workbench/frontend/src/pages/LedesConverterModule.tsx legal-workbench/frontend/src/services/ledesConverterApi.ts legal-workbench/frontend/src/store/ledesConverterStore.ts
git commit -m "feat(ledes): add batch processing UI

- Multi-file selection support
- Batch mode toggle
- Per-file status display
- Consolidated download option

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 8: Add Line Item Editor (P3)

**Files:**
- Create: `legal-workbench/frontend/src/components/ledes/LineItemEditor.tsx`
- Modify: `legal-workbench/frontend/src/pages/LedesConverterModule.tsx`

**Step 1: Create LineItemEditor component**

```tsx
// LineItemEditor.tsx
import React, { useState } from 'react';

interface LineItem {
  description: string;
  amount: number;
  taskCode?: string;
  activityCode?: string;
}

interface LineItemEditorProps {
  items: LineItem[];
  onChange: (items: LineItem[]) => void;
  unitCost: number;
}

const TASK_CODES = [
  { code: 'L100', label: 'Case Assessment' },
  { code: 'L110', label: 'Fact Investigation' },
  { code: 'L160', label: 'Settlement/ADR' },
  { code: 'L210', label: 'Pleadings' },
  { code: 'L250', label: 'Motions' },
  { code: 'L510', label: 'Appeals' },
];

const ACTIVITY_CODES = [
  { code: 'A102', label: 'Research' },
  { code: 'A103', label: 'Draft/Revise' },
  { code: 'A104', label: 'Review/Analyze' },
  { code: 'A105', label: 'Appear/Attend' },
  { code: 'A106', label: 'Communicate' },
];

export const LineItemEditor: React.FC<LineItemEditorProps> = ({
  items,
  onChange,
  unitCost,
}) => {
  const updateItem = (index: number, updates: Partial<LineItem>) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], ...updates };
    onChange(newItems);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const addItem = () => {
    onChange([...items, { description: '', amount: 0 }]);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-bold text-zinc-300">Line Items</h3>
        <button
          onClick={addItem}
          className="px-3 py-1 text-xs bg-teal-500 text-black rounded"
        >
          + Add Item
        </button>
      </div>

      <div className="space-y-3">
        {items.map((item, index) => (
          <div
            key={index}
            className="p-4 bg-zinc-900 border border-zinc-800 rounded space-y-3"
          >
            <div className="flex gap-4">
              <input
                type="text"
                value={item.description}
                onChange={(e) => updateItem(index, { description: e.target.value })}
                placeholder="Description"
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm"
              />
              <input
                type="number"
                value={item.amount}
                onChange={(e) => updateItem(index, { amount: parseFloat(e.target.value) || 0 })}
                placeholder="Amount"
                className="w-28 bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm"
              />
              <button
                onClick={() => removeItem(index)}
                className="px-3 text-rose-400 hover:text-rose-300"
              >
                X
              </button>
            </div>

            <div className="flex gap-4">
              <select
                value={item.taskCode || ''}
                onChange={(e) => updateItem(index, { taskCode: e.target.value })}
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm"
              >
                <option value="">Auto Task Code</option>
                {TASK_CODES.map((tc) => (
                  <option key={tc.code} value={tc.code}>
                    {tc.code} - {tc.label}
                  </option>
                ))}
              </select>

              <select
                value={item.activityCode || ''}
                onChange={(e) => updateItem(index, { activityCode: e.target.value })}
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm"
              >
                <option value="">Auto Activity Code</option>
                {ACTIVITY_CODES.map((ac) => (
                  <option key={ac.code} value={ac.code}>
                    {ac.code} - {ac.label}
                  </option>
                ))}
              </select>

              <div className="w-28 text-right text-sm text-zinc-400">
                {unitCost > 0 ? `${(item.amount / unitCost).toFixed(2)} hrs` : '-'}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="text-right text-sm text-zinc-400">
        Total: ${items.reduce((sum, item) => sum + item.amount, 0).toFixed(2)}
      </div>
    </div>
  );
};

export default LineItemEditor;
```

**Step 2: Integrate into LedesConverterModule**

Add state for editable line items and show editor after extraction.

**Step 3: Run build**

Run: `cd /home/opc/lex-vector/legal-workbench/frontend && bun run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add legal-workbench/frontend/src/components/ledes/LineItemEditor.tsx legal-workbench/frontend/src/pages/LedesConverterModule.tsx
git commit -m "feat(ledes): add Line Item Editor component (P3)

- Editable table for line items
- Manual task/activity code override
- Add/remove line items
- Auto-calculated hours display

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Final Integration Testing

**Files:**
- Test all features end-to-end

**Step 1: Start services**

```bash
cd /home/opc/lex-vector/legal-workbench
podman compose up -d ledes-converter frontend-react
```

**Step 2: Test checklist**

- [ ] Single file conversion works
- [ ] UTBMS codes auto-mapped correctly per line item
- [ ] Matter preset save/load works
- [ ] Batch upload (2-3 files) works
- [ ] Consolidated batch output works
- [ ] Line item editing works
- [ ] Hours calculated correctly (amount / 300)

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat(ledes): complete P1-P3 implementation

P1: Matter Presets + UTBMS Auto-Mapping
P2: Activity Code Mapping + Batch Processing
P3: Line Item Editor

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Summary

| Task | Description | Status |
|------|-------------|--------|
| 1 | Create UTBMS Mapper Module | Pending |
| 2 | Integrate Mapper into Backend | Pending |
| 3 | Add Matter Preset Types | Pending |
| 4 | Create Presets Store | Pending |
| 5 | Add Preset Selector UI | Pending |
| 6 | Batch Processing Backend | Pending |
| 7 | Batch Processing UI | Pending |
| 8 | Line Item Editor (P3) | Pending |
| 9 | Integration Testing | Pending |

**Estimated Total Time:** 4-6 hours

**Dependencies:**
- Task 2 depends on Task 1
- Tasks 3-5 can run in parallel with Tasks 1-2
- Tasks 6-7 can run after Tasks 1-2
- Task 8 can run independently
- Task 9 requires all others complete
