# PromptCLI – AI Prompt Management Toolkit

PromptCLI is a modern Python command-line utility powered by the **google-genai** SDK. It allows you to organize prompt files in any directory, run them against Google's Gemini models, and store the output in a clean, structured directory. It is built with a focus on developer experience, featuring beautiful terminal formatting with **Rich**, comprehensive error handling, and robust key management.

With PromptCLI, you can store your prompt projects anywhere on your filesystem (e.g. `./expensewise`, `D:\Projects\ExpenseWise`, or `../my-prompts`). As long as your project directory contains a `prompts/` directory, PromptCLI will operate on it and generate outputs into a corresponding `outputs/` directory.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Gemini API Key Configuration](#gemini-api-key-configuration)
- [Command Usage Guide](#command-usage-guide)
  - [1. Creating a Prompt Project](#1-creating-a-prompt-project)
  - [2. Listing Prompts](#2-listing-prompts)
  - [3. Running a Single Prompt](#3-running-a-single-prompt)
  - [4. Running All Prompts (Feed All)](#4-running-all-prompts-feed-all)
  - [5. API Key Management](#5-api-key-management)
- [Help Manual & Banner](#help-manual--banner)
- [Exit Codes](#exit-codes)
- [Development and Testing](#development-and-testing)
- [Future Extensibility](#future-extensibility)

---

## Project Structure

A PromptCLI project directory follows this structure at any location on your filesystem:

```text
<project-directory>/             # Any folder on your machine (e.g., ./expensewise)
├── prompts/                    # Directory containing your prompt files (.txt, .md, etc.)
│   ├── hello.txt
│   └── summary.md
└── outputs/                    # Directory containing generated Gemini responses (.md)
    ├── hello.md
    └── summary.md
```

The PromptCLI repository structure is organized as:

```text
PromptCLI/
├── promptcli/                  # Core package directory
│   ├── __init__.py
│   ├── cli.py                  # CLI command routes and dynamic parser
│   ├── config.py               # Constants and configuration
│   ├── core.py                 # File searching & Google GenAI SDK integration
│   ├── key_manager.py          # API key file read/writes
│   └── ui.py                   # Rich banner, table formatter, & status print utilities
├── tests/                      # Comprehensive unit test suites
│   ├── test_cli.py
│   ├── test_core.py
│   └── test_key_manager.py
├── main.py                     # Entry point script
├── pyproject.toml              # Build backend, dependencies, and test configurations
├── requirements.txt            # Runtime dependencies list
├── LICENSE                     # MIT License
└── README.md                   # Project documentation (this file)
```

---

## Requirements

* **Python:** 3.12 or newer
* **Dependencies:**
  * `google-genai` (Official Google GenAI SDK)
  * `typer` (Modern CLI builder)
  * `rich` (Terminal styling, tables, and progress bars)
  * `pytest` (For testing)

---

## Installation

You can install PromptCLI locally in editable mode so that the `promptcli` command becomes available globally on your system.

1. Clone or navigate to the project directory:
   ```bash
   cd C:\Users\indra\Documents\hello_world\PromptCLI
   ```

2. Create and activate a virtual environment:
   * **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   * **Linux/macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Install the package:
   ```bash
   pip install .
   ```
   *(Or in editable development mode: `pip install -e .`)*

Once installed, you can run the CLI using the `promptcli` executable command directly:
```bash
promptcli --help
```

---

## Gemini API Key Configuration

To call Google's Gemini models, you must provide a Gemini API key. PromptCLI looks for the key in two places:
1. The `.gemini-api-key` file located in the PromptCLI project root.
2. The `GEMINI_API_KEY` environment variable.

You can configure the key securely using the CLI (see below).

---

## Command Usage Guide

All commands support arbitrary directories passed as relative or absolute paths.

### 1. Creating a Prompt Project
Initialize a new project structure at the specified directory path.
```bash
promptcli create <project-directory-path>
```
* **Examples:**
  * `promptcli create expensewise` (creates `./expensewise` in the current working directory)
  * `promptcli create ../paper-prompts`
  * `promptcli create D:\Projects\ExpenseWise`
* **Behavior:** Creates `<directory>/prompts` and `<directory>/outputs`. If the directories already exist, displays a friendly warning.

### 2. Listing Prompts
List all prompts inside a project directory's `prompts` folder in a formatted table.
```bash
promptcli <project-directory-path> --list
```
* **Examples:**
  * `promptcli ./expensewise --list`
  * `promptcli D:\Projects\ExpenseWise --list`
* **Output:** Displays columns for Prompt Name, File Extension, File Size, and Last Modified timestamp.

### 3. Running a Single Prompt
Generate output for a prompt file and save the result as Markdown.
```bash
promptcli <project-directory-path> <prompt-name>
```
* **Examples:**
  * `promptcli ./expensewise hello`
  * `promptcli D:\Projects\ExpenseWise hello.txt`
* **Details:**
  * The file extension is optional. If omitted, PromptCLI searches for matching stems (e.g. `hello.txt`, `hello.md`).
  * Response is saved to `<project-directory-path>/outputs/<prompt-name>.md`.
  * If the output file already exists, PromptCLI asks you to confirm (`y/n`) before overwriting.
  * You can skip confirmation by passing the `-f` or `--force` flag: `promptcli ./expensewise hello --force`.

### 4. Running All Prompts (Feed All)
Feed every prompt in a project's `prompts` folder to Gemini sequentially.
```bash
promptcli <project-directory-path> --feed-all
```
* **Examples:**
  * `promptcli ./expensewise --feed-all`
  * `promptcli ../paper-prompts --feed-all`
* **Details:**
  * Renders a real-time progress bar.
  * Prompts for overwrite confirmation if an output markdown file already exists (can be bypassed with `--force`).
  * Prints a summary of successful and failed/skipped generation tasks.

### 5. API Key Management
#### Check API Key Status
```bash
promptcli gemini-key status
```
* **Output:** Reports whether the key is configured, empty, or missing.

#### Save API Key
```bash
promptcli gemini-key --save
```
* **Behavior:** Prompts securely for the key (characters hidden). Saves the key in `.gemini-api-key`. If a key already exists, requests confirmation before overwriting.

---

## Help Manual & Banner

### Banner
When PromptCLI executes any project configuration or execution command, it displays a startup banner containing authorship details:
```text
┌────────────────────────────────────────────┐
│                                            │
│              PromptCLI                     │
│     AI Prompt Management Toolkit           │
│   ──────────────────────────────────────   │
│   Author   : Indrajit Ghosh                │
│   Position : Postdoctoral Fellow           │
│   Institute: IIT Kanpur                    │
│   Version  : 1.0.0                         │
│                                            │
└────────────────────────────────────────────┘
```

### Help Manual
Get help for commands and options using `--help`:
```bash
promptcli --help
promptcli create --help
promptcli gemini-key --help
```

---

## Exit Codes

PromptCLI follows standard exit codes to facilitate automation:
* `0`: Success (commands executed, list displayed, response generated)
* `1`: Application/Runtime Error (prompt not found, invalid API key, Gemini connection issues)
* `2`: Usage Error (invalid flags, missing arguments)

---

## Development and Testing

The application uses `pytest` for unit testing. The test suite covers CLI endpoints, file manipulation, stem fallbacks, key management, and API calls (with mock clients).

### Running Tests
Execute the tests inside the virtual environment:
```bash
pytest
```

---

## Future Extensibility

PromptCLI's modular architecture makes it easy to integrate additional capabilities:
1. **Model Selection:** Add a `--model` option to select other Gemini models (`gemini-2.5-pro`, `gemini-1.5-flash`).
2. **Parameters Configuration:** Pass system instructions, temperature, top-p, and max tokens.
3. **Response Streaming:** Support streaming responses directly to stdout.
4. **Export/Import:** Export generated markdown structures to HTML or PDF, or import prompts from public repositories.
5. **Project Management:** Add commands to delete, rename, or archive projects.
