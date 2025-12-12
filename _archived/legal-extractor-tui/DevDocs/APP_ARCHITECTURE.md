# Legal Extractor TUI - Application Architecture

## Overview

The Legal Extractor TUI is a terminal-based application for extracting and cleaning text from Brazilian legal PDFs. It uses the Textual framework for UI rendering and integrates with the `legal-text-extractor` agent for PDF processing.

## Component Hierarchy

```
LegalExtractorApp (app.py)
├── Themes (5 registered themes)
├── Screens
│   ├── MainScreen (main_screen.py)
│   └── HelpScreen (help_screen.py)
└── Global Keybindings
```

## MainScreen Layout

```
┌───────────────────────────────────────────────────────────────┐
│ Header                                                         │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ Logo: Legal Extractor TUI                               │   │
│ │ Status: Ready / Extracting / Completed                  │   │
│ └─────────────────────────────────────────────────────────┘   │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────┬───────────────────────────────────────┐   │
│ │ Sidebar (30%)   │ Content Area (70%)                    │   │
│ │                 │                                       │   │
│ │ ┌─────────────┐ │ ┌───────────────────────────────────┐ │   │
│ │ │FileSelector │ │ │ ExtractionProgress (collapsible)  │ │   │
│ │ │             │ │ │ ┌───────────────────────────────┐ │ │   │
│ │ │ - Browse    │ │ │ │ Stage: Extracting...          │ │ │   │
│ │ │ - Filter    │ │ │ │ Progress: [████████░░] 80%    │ │ │   │
│ │ │ - Select    │ │ │ │ Message: Reading PDF pages... │ │ │   │
│ │ │             │ │ │ └───────────────────────────────┘ │ │   │
│ │ └─────────────┘ │ └───────────────────────────────────┘ │   │
│ │                 │                                       │   │
│ │ ┌─────────────┐ │ ┌───────────────────────────────────┐ │   │
│ │ │SystemSelect │ │ │ ResultsPanel (tabs)               │ │   │
│ │ │             │ │ │ ┌───────────────────────────────┐ │ │   │
│ │ │ ○ Auto      │ │ │ │ [Preview][Metadata][Sections] │ │ │   │
│ │ │ ○ PJE       │ │ │ │                               │ │ │   │
│ │ │ ○ E-SAJ     │ │ │ │ Extracted text preview...     │ │ │   │
│ │ │ ○ EPROC     │ │ │ │                               │ │ │   │
│ │ │             │ │ │ │ System: PJE (95% confidence)  │ │ │   │
│ │ └─────────────┘ │ │ │ Length: 45,892 chars          │ │ │   │
│ │                 │ │ │ Reduction: 67.3%              │ │ │   │
│ │ ┌─────────────┐ │ │ │                               │ │ │   │
│ │ │ConfigPanel  │ │ │ │ [Export as TXT/MD/JSON]       │ │ │   │
│ │ │             │ │ │ └───────────────────────────────┘ │ │   │
│ │ │ ☑ Sections  │ │ └───────────────────────────────────┘ │   │
│ │ │ Format: [▼] │ │                                       │   │
│ │ │   - Text    │ │ ┌───────────────────────────────────┐ │   │
│ │ │   - MD      │ │ │ LogPanel (collapsible)            │ │   │
│ │ │   - JSON    │ │ │ [INFO] Application started        │ │   │
│ │ └─────────────┘ │ │ [INFO] File selected: doc.pdf     │ │   │
│ │                 │ │ [INFO] Extraction started         │ │   │
│ └─────────────────┴─│ [DEBUG] System detected: PJE      │ │   │
│                     └───────────────────────────────────┘ │   │
├───────────────────────────────────────────────────────────────┤
│ StatusBar                                                     │
│ Status: Completed: 45,892 chars (2.3s) │ Runtime: 00:02:34   │
├───────────────────────────────────────────────────────────────┤
│ Footer                                                        │
│ [r] Extrair [Esc] Cancelar [^O] Abrir [^S] Salvar [?] Ajuda  │
└───────────────────────────────────────────────────────────────┘
```

## Data Flow

### Extraction Pipeline

```
1. User selects file
   ↓
   FileSelector → FileSelected message
   ↓
   MainScreen.on_file_selected()
   - Store selected_file
   - Clear previous results
   - Update status

2. User presses 'r' (run extraction)
   ↓
   action_run_extraction()
   - Validate file exists
   - Check not already running
   - Create ExtractionWorker
   ↓
   ExtractionWorker.run()
   - Post ExtractionStarted
   - Extract text (stage 1)
   - Clean text (stage 2)
   - Analyze sections (stage 3, optional)
   - Post progress updates
   ↓
   MainScreen.on_extraction_progress()
   - Update ExtractionProgress widget
   - Log to LogPanel
   - Update StatusBar
   ↓
   ExtractionWorker completes
   - Post ExtractionCompleted
   ↓
   MainScreen.on_extraction_completed()
   - Hide progress panel
   - Display results in ResultsPanel
   - Log completion stats

3. User presses '^S' (save)
   ↓
   action_save_result()
   - Build filename from original + format
   - Post ExportRequested
   ↓
   MainScreen.on_export_requested()
   - Format content (text/md/json)
   - Write to file
   - Log success/failure
```

### Message Types

**User Interaction Messages**:
- `FileSelected(path)` - From FileSelector when file chosen
- `SystemChanged(system)` - From SystemSelector dropdown
- `ConfigChanged(config)` - From ConfigPanel toggles/selects
- `ExportRequested(format, destination)` - From save action

**Worker Lifecycle Messages**:
- `ExtractionStarted(file_path, system, separate_sections)`
- `ExtractionProgress(stage, progress, message, details)`
- `ExtractionCompleted(result, elapsed_time)`
- `ExtractionError(error, stage, message)`
- `ExtractionCancelled(stage)`

**System Messages**:
- `LogMessage(message, level)` - For LogPanel
- `StatusUpdate(text)` - For StatusBar

## Widget Responsibilities

### FileSelector
**Purpose**: Browse and select PDF files
**Emits**: FileSelected(path)
**Methods**:
- `focus()` - Focus for keyboard navigation
**State**: Currently selected path

### SystemSelector
**Purpose**: Choose judicial system (auto-detect or manual)
**Emits**: SystemChanged(system)
**Options**: auto, pje, esaj, eproc, projudi, stf, stj
**State**: Selected system code

### ConfigPanel
**Purpose**: Configure extraction settings
**Emits**: ConfigChanged(config)
**Settings**:
- `separate_sections` (bool): Enable section analysis
- `output_format` (str): Export format (text/markdown/json)
**State**: Configuration dictionary

### ExtractionProgress
**Purpose**: Show multi-stage extraction progress
**Methods**:
- `reset()` - Reset to initial state
- `update_progress(stage, progress, message)` - Update display
**Stages**: extracting → cleaning → analyzing
**Display**: Stage name, progress bar, status message

### ResultsPanel
**Purpose**: Display extraction results with tabs
**Methods**:
- `clear()` - Clear all content
- `display_result(result_dict)` - Show extraction result
**Tabs**:
- Preview: Text preview (first 2000 chars)
- Metadata: System, confidence, lengths, reduction
- Sections: Identified document sections (if available)

### LogPanel
**Purpose**: Real-time logging with level filtering
**Receives**: LogMessage(message, level)
**Levels**: DEBUG, INFO, SUCCESS, WARNING, ERROR
**Features**: Colored levels, timestamps, auto-scroll

### StatusBar
**Purpose**: Show current status and runtime
**Receives**: StatusUpdate(text)
**Display**: Status text (left), runtime (right)

## Worker Architecture

### ExtractionWorker
**Base**: `BaseWorker` (provides cancellation, message posting)
**Integration**: Uses `LegalTextExtractor` from legal-text-extractor agent
**Async**: Runs extraction in thread pool to avoid blocking UI

**Pipeline**:
1. **Validation**: File exists, is PDF
2. **Scanned check**: Detect if OCR needed (not yet implemented)
3. **Text extraction**: Extract raw text from PDF
4. **System detection**: Auto-detect judicial system
5. **Text cleaning**: Remove noise, signatures, headers
6. **Section analysis**: Identify document sections (optional)

**Progress reporting**:
- 0.1: Starting extraction
- 0.2: Reading PDF pages
- 0.5: System detection
- 0.7: Text cleaning
- 0.8: Section analysis start
- 0.95: Finalizing
- 1.0: Complete

**Error handling**:
- FileNotFoundError → ExtractionError (validation stage)
- NotImplementedError → ExtractionError (OCR not implemented)
- Exception → ExtractionError (unexpected failure)

**Cancellation**:
- Checks `self.is_cancelled` between stages
- Posts `ExtractionCancelled` and returns None
- Worker cleanup handled by BaseWorker

## Theme System

**Available themes**:
1. **vibe-neon** (default) - Dracula/Cyberpunk colors
2. **matrix** - Green on black Matrix style
3. **synthwave** - Pink/purple retro
4. **minimal-dark** - Simple dark mode
5. **minimal-light** - Simple light mode

**Theme registration**:
- All themes registered in `LegalExtractorApp.__init__()`
- Theme set in `on_mount()` before screens pushed
- Theme can be switched with 'd' keybinding (toggles dark/light)

## Configuration

### App-level config
**File**: `config.py`
**Constants**:
- `JUDICIAL_SYSTEMS` - System codes and descriptions
- `OUTPUT_FORMATS` - Export format metadata
- `EXTRACTION_STAGES` - Pipeline stage definitions
- `COLORS` - Status colors (success, warning, error, info)
- `LOGO_SMALL`, `LOGO_LARGE` - ASCII art

### User settings
**Runtime**:
- `--theme` - Theme selection (neon/matrix/synthwave/dark/light)
- `--dev` - Enable development mode
- `file` - Optional initial PDF file path

## Keybindings

**Global (App-level)**:
- `q` - Quit application
- `?` - Show help screen
- `d` - Toggle dark/light mode
- `ctrl+p` - Command palette (hidden)

**MainScreen**:
- `r` - Run extraction (start processing)
- `escape` - Cancel extraction (abort running operation)
- `ctrl+o` - Open file (focus file selector)
- `ctrl+s` - Save result (export to file)

## Error Handling

### Validation errors
- No file selected → Warning log, status error
- File not found → Error log, status error
- Not a PDF → ExtractionError message

### Extraction errors
- Scanned PDF (OCR) → ExtractionError "not yet implemented"
- Parsing failure → ExtractionError with exception details
- Section analysis failure → Fallback to single section

### Export errors
- No results → Warning log
- Write failure → Error log, status error
- Permission denied → Error log with exception

### User feedback
All errors logged to LogPanel with appropriate level and displayed in StatusBar.

## Performance Considerations

### Background processing
- Extraction runs in thread pool (async to_thread)
- UI remains responsive during processing
- Progress updates every major stage

### Memory management
- Results stored only after successful extraction
- Previous results cleared on new file selection
- Worker instance replaced on each run

### UI optimization
- Progress panel hidden when not in use
- Log panel collapsible to save space
- Results preview limited to prevent lag

## Testing Strategy

### Unit tests
- Message handler logic
- Export formatting (_format_as_markdown)
- Validation logic (file checks)

### Integration tests
- Full extraction pipeline with test PDF
- Theme switching
- Export all formats

### Manual tests
- All keybindings
- Widget interactions
- Error scenarios (invalid file, permissions)
- Cancellation during extraction

---

## File Locations

**Application**:
- `/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-extractor-tui/src/legal_extractor_tui/app.py`
- `/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-extractor-tui/src/legal_extractor_tui/screens/main_screen.py`

**Supporting**:
- `config.py` - Constants
- `messages/` - Message definitions
- `widgets/` - UI components
- `workers/` - Background tasks
- `themes/` - Color schemes
- `styles/` - TCSS styling

**Agent Integration**:
- `/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/ferramentas/legal-text-extractor/` - PDF extraction tool
