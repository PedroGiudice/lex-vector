# GEMINI.md

## Project Overview

This project, "Claude Code Projetos," is a system for Brazilian legal automation. It consists of a collection of Python agents, command-line tools, and shared utilities designed to interact with and process legal data from various Brazilian sources. The system is built on a modular architecture that separates code, environment, and data, with a strong emphasis on using isolated Python virtual environments for each agent.

The core functionalities of the project include:

*   **Data Monitoring and Collection:** Agents like `oab-watcher` and `djen-tracker` monitor legal publications and official journals.
*   **Data Extraction and Processing:** Tools for extracting information from PDFs and other legal documents.
*   **Natural Language Processing:** The `legal-lens` agent is dedicated to NLP tasks.
*   **Data Analysis and Reporting:** Agents and tools for collecting and analyzing legal data.
*   **Textual User Interfaces (TUIs):** The `legal-extractor-tui` provides a user-friendly terminal interface for PDF text extraction.

The project is primarily built with Python 3.11 and utilizes a set of libraries for data handling, PDF processing, and web scraping. The TUIs are built with the `textual` library. It runs on a Linux environment, specifically Ubuntu 24.04 within WSL2.

## Building and Running

Each Python agent in this project has its own isolated environment and dependencies. To run an agent, you need to navigate to its directory, activate its virtual environment, and then run its main script.

### Running a Command-Line Agent (Example: `oab-watcher`)

1.  **Navigate to the agent's directory:**
    ```bash
    cd agentes/oab-watcher
    ```

2.  **Create and activate the virtual environment (if it doesn't exist):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the agent:**
    ```bash
    python main.py
    ```

### Running a Textual TUI (Example: `legal-extractor-tui`)

1.  **Navigate to the TUI's directory:**
    ```bash
    cd legal-extractor-tui
    ```
2. **Run the launch script**
   ```bash
   ./run.sh
   ```
   The TUI can be run in development mode with hot reloading by using the `--dev` flag:
   ```bash
   ./run.sh --dev
   ```

## Development Conventions

*   **Virtual Environments:** Every Python agent or tool **must** have its own `.venv` directory for managing dependencies. This is a strict project rule.
*   **Data Separation:** All data generated or used by the agents is stored outside the project's Git repository, in the `~/claude-code-data/` directory. The `shared/utils/path_utils.py` module provides helper functions for accessing this directory.
*   **Git Usage:** The Git repository is used exclusively for code. Data files, virtual environments, and other artifacts are excluded via the `.gitignore` file.
*   **Context Offloading:** For analyzing large files or multiple files, the use of the `gemini-assistant` agent is mandatory to keep the context clean and analysis efficient.
*   **Modularity:** The project is organized into distinct modules: `agentes` for autonomous agents, `comandos` for CLI utilities, `shared` for shared code, and `skills` for custom functionalities.
*   **Error Handling and Debugging:** The project encourages a "5 Whys" technique for root cause analysis of bugs. Logging is configured for each agent to aid in debugging.
*   **TUI Development:** TUIs are built with the `textual` library and should follow the established patterns in the `legal-extractor-tui` application.
