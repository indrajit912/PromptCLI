# PromptCLI – AI Prompt Management Toolkit

PromptCLI is a modern Python command-line environment powered by the **google-genai** SDK. It enables developers and prompt engineers to manage prompt projects, run prompts against Google's Gemini models, and organize generated outputs into a clean folder structure.

Featuring beautiful terminal formatting with **Rich**, real-time progress bars, and secure API key storage, PromptCLI serves as an all-in-one CLI cockpit. Users rarely need to leave their shell to manage their entire prompt-engineering lifecycle.

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration & Settings](#configuration--settings)
- [Path Resolution Rules](#path-resolution-rules)
- [Command Reference](#command-reference)
  - [1. Workspace Management (`workspace`)](#1-workspace-management-workspace)
  - [2. Project Management (`project`)](#2-project-management-project)
  - [3. Prompt Management (`prompt`)](#3-prompt-management-prompt)
  - [4. Output Management (`output`)](#4-output-management-output)
  - [5. API Key Management (`gemini-key`)](#5-api-key-management-gemini-key)
- [Practical Examples](#practical-examples)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [Development Setup](#development-setup)
- [Contribution Guidelines](#contribution-guidelines)
- [License Information](#license-information)

---

## Overview

A PromptCLI project directory holds a strict, standard structure:

```text
<project-directory>/             # Any folder (e.g., ./expensewise or workspace project)
├── prompts/                    # Directory containing prompt text files
│   ├── hello.txt
│   └── summarize-report.md
└── outputs/                    # Directory containing generated Gemini responses
    ├── hello.md
    └── summarize-report.md
```

PromptCLI automates this directory creation, lets you open files directly in terminal editors (like `vim`), lists prompts or outputs, runs prompts, and updates your responses in real time.

---

## Requirements

* **Python:** 3.12 or newer
* **Dependencies:**
  * `google-genai` (Official Google GenAI SDK)
  * `typer` (Modern CLI library)
  * `rich` (Terminal styling, tables, and progress bars)
  * `pytest` (For testing)

---

## Installation

You can install PromptCLI directly from the official GitHub repository.

### Recommended (using pipx)

`pipx` is the recommended installation method because it installs PromptCLI in an isolated environment while making the `promptcli` command globally available:

```bash
pipx install git+https://github.com/indrajit912/PromptCLI.git
```

### Alternative (using pip)

You can also install PromptCLI using `pip` inside your active virtual environment:

```bash
pip install git+https://github.com/indrajit912/PromptCLI.git
```

---

## Configuration & Settings

PromptCLI stores its configuration file (`settings.json`) in standard, platform-specific config directories:
* **Windows:** `%APPDATA%\PromptCLI\settings.json`
* **Linux/macOS:** `~/.config/promptcli/settings.json`

### Default Settings Schema

```json
{
    "workspace_dir": "C:\\Users\\username\\Documents\\ai-prompts",
    "editor": "vim"
}
```

### Default Workspace Fallback

If you have not configured a workspace directory, PromptCLI automatically falls back to:
```text
~/Documents/ai-prompts
```
On first use, if this directory does not exist, PromptCLI will offer to create it automatically. You can override it at any time using `promptcli workspace set <dir>`.

### Editor Configuration

PromptCLI integrates with terminal editors to open prompts and outputs. The default editor is `vim`, but you can customize this in `settings.json` to anything on your system PATH (e.g., `nano`, `nvim`, `code --wait`, `notepad`, `helix`).

---

## Path Resolution Rules

When you pass a project argument (e.g., `<project>`) to any Command, PromptCLI resolves it using the following hierarchy:

1. **Explicit Path Check:** If the path exists on disk, is absolute, starts with `.`, or contains path separators (`/` or `\`), it is used directly (e.g., `./expensewise`, `D:\Projects\Thesis`).
2. **Workspace Fallback:** If not, and a default workspace is configured (e.g., `D:\AI-Prompts`), PromptCLI checks if `<workspace>/<project>` exists.
3. **CWD Fallback:** If no workspace is configured, it defaults to checking relative to the current working directory (`./<project>`).

---

## Command Reference

### 1. Workspace Management (`workspace`)

Manage default workspace folders.

* **Set default workspace:**
  ```bash
  promptcli workspace set <directory-path>
  ```
  *Resolves the absolute path and registers it in config.*
* **Show configured workspace:**
  ```bash
  promptcli workspace show
  ```
* **Show workspace status:**
  ```bash
  promptcli workspace status
  ```
  *Prints path, verifies existence, and counts/lists active projects.*
* **Clear workspace config:**
  ```bash
  promptcli workspace clear
  ```

---

### 2. Project Management (`project`)

Manage prompt projects.

* **Create a new project:**
  ```bash
  promptcli project create <project-name>
  ```
  *Initializes a folder with prompts/ and outputs/ structures. (You can also use the shortcut: `promptcli create <project-name>`).*
* **Delete a project:**
  ```bash
  promptcli project delete <project-name>
  ```
  *Deletes the folder recursively after user confirmation.*
* **List all projects in workspace:**
  ```bash
  promptcli project list
  ```
  *Lists projects with their prompt and output file counts in a Rich table.*

---

### 3. Prompt Management (`prompt`)

Manage prompt files inside projects.

* **Create a prompt:**
  ```bash
  promptcli prompt create <project> <prompt-name>
  ```
  *Creates a blank file under `prompts/` (default extension `.txt`, override with `--extension` / `-e`) and opens it in the configured editor.*
* **Edit a prompt:**
  ```bash
  promptcli prompt edit <project> <prompt-name>
  ```
  *Opens the prompt file in the configured editor (e.g., `vim`).*
* **Delete a prompt:**
  ```bash
  promptcli prompt delete <project> <prompt-name>
  ```
  *Asks for confirmation, deletes the prompt file, and offers to clean up the corresponding generated output file.*
* **List prompts:**
  ```bash
  promptcli prompt list <project>
  ```
  *Displays prompt name, extension, file size, and last modified timestamp in a styled table.*

---

### 4. Output Management (`output`)

Manage generated prompt outputs.

* **Open an output:**
  ```bash
  promptcli output open <project> <prompt-name>
  ```
  *Opens `outputs/<prompt-name>.md` in your configured editor.*
* **List outputs:**
  ```bash
  promptcli output list <project>
  ```
  *Lists outputs in a table with size and modification timestamp.*
* **Delete an output:**
  ```bash
  promptcli output delete <project> <prompt-name>
  ```

---

### 5. API Key Management (`gemini-key`)

* **Check API Key Status:**
  ```bash
  promptcli gemini-key status
  ```
* **Save API Key:**
  ```bash
  promptcli gemini-key --save
  ```
  *Prompts for input with hidden characters and saves it securely in `.gemini-api-key`.*

---

## Practical Examples

### Typical Workflow: Setting up and running prompts

```bash
# 1. Check Gemini API key status
promptcli gemini-key status

# 2. Configure a workspace directory
promptcli workspace set ~/Documents/ai-prompts

# 3. Create a project
promptcli project create expensewise

# 4. Create a prompt (will open in your default editor automatically)
promptcli prompt create expensewise summarize-report --extension .txt

# 5. List prompts in the project
promptcli prompt list expensewise

# 6. Generate Gemini output for the prompt
promptcli expensewise summarize-report

# 7. Open the generated markdown output file
promptcli output open expensewise summarize-report
```

---

## Troubleshooting & FAQ

#### Q: I get a `FileNotFoundError` or "editor not found" error when creating/editing files.
**A:** This happens because your configured editor (default: `vim`) is not installed or available on your system's PATH. Open your configuration `settings.json` (printed in the error message) and change `"editor"` to an editor available on your machine (e.g., `"notepad"` on Windows, `"nano"` on Linux).

#### Q: How do I run a prompt without typing `promptcli run`?
**A:** PromptCLI utilizes a dynamic positional parser. Any command that does not begin with a registered subcommand is automatically intercepted. Running `promptcli expensewise summary` translates to `promptcli run expensewise summary`.

#### Q: Windows console gives Unicode encoding errors when printing.
**A:** PromptCLI automatically reconfigures streams to use UTF-8 on Windows. If problems persist, set the active code page in your command prompt: `chcp 65001`.

### Exit Codes
* `0` - Success
* `1` - Error (e.g. project/prompt not found, Gemini API failure, missing configuration)
* `2` - CLI usage/parsing error

---

## Development Setup

If you want to contribute or run tests locally:

1. Clone and navigate to the repository:
   ```bash
   git clone https://github.com/indrajit912/PromptCLI.git
   cd PromptCLI
   ```

2. Setup virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1   # Windows
   source .venv/bin/activate    # Unix
   ```

3. Install editable package with dev dependencies:
   ```bash
   pip install -e .
   pip install pytest
   ```

4. Run tests:
   ```bash
   pytest
   ```

---

## Contribution Guidelines

1. Fork the Repository on GitHub.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Write clean Python code conforming to PEP 8 standards.
4. Ensure all unit tests pass (`pytest`).
5. Commit your changes and open a Pull Request.

---

## License Information

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
