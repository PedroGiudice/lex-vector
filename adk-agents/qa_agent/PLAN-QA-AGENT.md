# Plan: ADK QA Architect Agent (React E2E & Backend)

## 1. Executive Summary
This document outlines the architecture for a new **ADK Agent** designed to perform autonomous **End-to-End (E2E)** and **Back-to-Back** testing for React applications. The agent, acting as a "Technical QA Architect," will leverage the Google Agent Development Kit (ADK) to plan, generate, execute, and analyze tests using **Playwright** (for E2E) and **Requests/Pytest** (for Backend API testing).

## 2. Goals & Objectives
*   **Autonomous E2E Testing:** Navigate React applications, interact with UI elements, and verify visual/functional states.
*   **Back-to-Back Testing:** Verify backend API endpoints directly to ensure data integrity and contract adherence.
*   **Self-Correction:** Analyze test failures (logs, screenshots) and attempt to fix test scripts or suggest code fixes.
*   **Zero-Fluff Reporting:** Produce strict, evidence-based Markdown reports (Pass/Fail tables, error traces, reproduction steps).

## 3. Architecture

### 3.1. Core Tech Stack
*   **Framework:** Google ADK (`google-adk`) + `google-genai` SDK.
*   **Model:** `gemini-2.5-flash` (High speed/throughput for tool use) or `gemini-2.5-pro` (Complex reasoning for test planning).
*   **E2E Engine:** `playwright-python` (Chosen for seamless Python integration with ADK).
*   **API Engine:** `requests` library.
*   **Environment:** Python 3.10+ Virtual Environment.

### 3.2. Agent Persona: "The QA Architect"
*   **Role:** Technical QA Architect.
*   **Tone:** Clinical, precise, evidence-based. No "I think," only "The log shows."
*   **Directives:**
    *   Prioritize "Happy Path" verification first.
    *   Use exact selectors (data-testid preferred, then text/role).
    *   Always capture screenshots on failure.
    *   Output results in structured Markdown tables.

### 3.3. Directory Structure
```
adk-agents/qa_agent/
├── .venv/                  # Dedicated Virtual Environment
├── agent.py                # Main ADK Agent definition (System Instruction + Tools)
├── tools/
│   ├── __init__.py
│   ├── e2e_runner.py       # Playwright wrapper (browser control)
│   ├── api_runner.py       # API test runner (requests)
│   └── repo_scanner.py     # Simple static analysis (find routes in React code)
├── tests_generated/        # Directory where the agent writes executable test scripts
│   ├── e2e/
│   └── api/
├── reports/                # Output directory for test reports
├── requirements.txt        # Dependencies
├── run_qa.sh               # Entry point script (Setup + Run)
└── PLAN-QA-AGENT.md        # This document
```

## 4. Operational Workflow

The agent operates in a loop: **Scan -> Plan -> Generate -> Execute -> Analyze**.

1.  **Input**: User provides `TARGET_URL` (e.g., http://localhost:3000) and optional `REPO_PATH`.
2.  **Scan (Static Analysis)**:
    *   If `REPO_PATH` is provided, use `repo_scanner` to find `react-router` definitions or API endpoints in `server.js` / `app.py`.
    *   Goal: Map the "Attack Surface" (Routes: `/login`, `/dashboard`; APIs: `GET /api/users`).
3.  **Plan (Test Strategy)**:
    *   Agent creates a list of test scenarios (e.g., "Login with valid credentials", "Verify Dashboard loads").
4.  **Generate (Scripting)**:
    *   Agent writes Python/Playwright scripts into `tests_generated/e2e/`.
    *   Agent writes Python/Requests scripts into `tests_generated/api/`.
    *   *Constraint*: Scripts must be standalone and executable.
5.  **Execute**:
    *   Agent calls `e2e_runner.execute(script_path)` or `api_runner.execute(script_path)`.
    *   Tools capture Stdout, Stderr, and Screenshots.
6.  **Analyze & Report**:
    *   Agent parses output.
    *   If Success: Mark as PASS in report.
    *   If Fail: Analyze error, look at screenshot. Optionally retry with a fixed script (Self-Healing).
    *   Generate `reports/QA_REPORT_<TIMESTAMP>.md`.

## 5. Tool Definitions (Draft)

### 5.1. `e2e_runner` (Playwright)
*   **Function**: `run_playwright_script(script_code: str, script_name: str) -> dict`
*   **Capabilities**:
    *   Writes `script_code` to `tests_generated/e2e/<script_name>.py`.
    *   Executes via `python <script_name>.py`.
    *   Returns: `{ "status": "success/fail", "output": "...", "screenshot_path": "..." }`.

### 5.2. `api_runner` (Requests)
*   **Function**: `run_api_test(method: str, url: str, payload: dict, expected_status: int) -> dict`
*   **Capabilities**:
    *   Executes HTTP request.
    *   Validates Status Code and basic Response Schema.
    *   Returns: `{ "status": "success/fail", "response_time": "ms", "body": "..." }`.

### 5.3. `repo_scanner`
*   **Function**: `scan_react_routes(repo_path: str) -> list[str]`
*   **Capabilities**:
    *   Greps for `<Route path="...">` or `createBrowserRouter`.
    *   Returns list of discovered frontend paths.

## 6. Zero-Fail & Safety Strategy
*   **Sandboxing**: All generated scripts run in the `qa_agent` subdirectory.
*   **Timeouts**: Playwright scripts will have strict timeouts (e.g., 30s) to prevent hanging.
*   **Cleanup**: `run_qa.sh` ensures browser processes are killed on exit.
*   **Retry Logic**: The Agent will catch `ClientError` (ADK) and retry generation if the LLM fails, but test failures are treated as "True Negatives" unless self-healing is requested.

## 7. Implementation Steps
1.  **Setup**: Create `.venv` and install `google-adk`, `google-genai`, `playwright`, `pytest`.
2.  **Tooling**: Implement `tools/e2e_runner.py` (ensure `playwright install` is handled).
3.  **Agent**: Implement `agent.py` with the "QA Architect" prompt.
4.  **Runner**: Create `run_qa.sh` to orchestrate the environment.
5.  **Validation**: Test against a simple mock React app or public demo site.
