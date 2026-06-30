import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from promptcli.config import VERSION
from promptcli.ui import (
    show_banner,
    print_success,
    print_warning,
    print_error,
    print_info,
    display_prompts_table,
)

console = Console()

# Create main Typer app
app = typer.Typer(
    name="promptcli",
    rich_markup_mode="rich",
)

# Create Gemini-key subcommand Typer app
gemini_key_app = typer.Typer(
    name="gemini-key",
    rich_markup_mode="rich",
    help="Manage Gemini API key stored in the .gemini-api-key file.",
)

app.add_typer(gemini_key_app, name="gemini-key")


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show PromptCLI application version and exit.",
    ),
) -> None:
    """
    [bold cyan]PromptCLI[/bold cyan] - A Python CLI for Managing AI Prompts (Google GenAI).

    This toolkit helps manage prompt projects, send prompts to Gemini,
    and save outputs in a structured folder hierarchy.

    [bold underline]Usage Patterns:[/bold underline]
      [green]promptcli <project-dir> <prompt>[/green]        Generate output for a single prompt
      [green]promptcli <project-dir> --list[/green]          List all available prompts in a project directory
      [green]promptcli <project-dir> --feed-all[/green]      Generate outputs for all prompts in a project directory
      [green]promptcli create <project-dir>[/green]          Create a new project structure at the specified directory path
      [green]promptcli gemini-key status[/green]            Check Gemini API key status
      [green]promptcli gemini-key --save[/green]            Save Gemini API key securely

    [bold underline]Exit Codes:[/bold underline]
      [white]0[/white] - Success
      [white]1[/white] - Error (e.g. project/prompt not found, Gemini API failure)
      [white]2[/white] - CLI usage/parsing error
    """
    if version:
        typer.echo(f"PromptCLI version {VERSION}")
        raise typer.Exit()

    # Show banner on startup for normal commands
    show_banner()

    if ctx.invoked_subcommand is None:
        # If no subcommand was provided, display the default click help output
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("create", help="Create a new project structure at the specified directory path.")
def create_project_cmd(
    project_path: str = typer.Argument(
        ...,
        help="The directory path (relative or absolute) where the project structure should be created.",
    )
) -> None:
    """Creates prompts/ and outputs/ directories at the specified location."""
    from promptcli.core import create_project

    resolved_path = Path(project_path).resolve()
    success = create_project(project_path)
    if success:
        try:
            display_path = resolved_path.relative_to(Path.cwd())
        except ValueError:
            display_path = resolved_path
        print_success(f"Project directory created successfully at [cyan]{display_path}[/cyan].")
    else:
        print_warning(f"Project directory '{project_path}' already exists.")


@gemini_key_app.callback(invoke_without_command=True)
def gemini_key_main(
    ctx: typer.Context,
    save: bool = typer.Option(
        False,
        "--save",
        help="Securely prompt for the Gemini API key and save it to the local .gemini-api-key file.",
    ),
) -> None:
    """
    Manage the Gemini API key.
    
    If neither --save nor status subcommand is specified, defaults to status.
    """
    from promptcli.key_manager import check_key_status, save_key

    if save:
        status = check_key_status()
        if status == "exists":
            confirm = typer.confirm(
                "An API key is already saved. Do you want to overwrite it?",
                default=True,
            )
            if not confirm:
                print_info("API key was not modified.")
                raise typer.Exit(0)

        # Securely prompt for the key (hidden input)
        api_key = typer.prompt("Enter your Gemini API key", hide_input=True)
        if not api_key.strip():
            print_error("API key cannot be empty.")
            raise typer.Exit(1)

        save_key(api_key)
        print_success("Gemini API key saved successfully to .gemini-api-key.")
        raise typer.Exit(0)

    elif ctx.invoked_subcommand is None:
        # Default behavior: run status
        show_gemini_key_status()


@gemini_key_app.command("status", help="Check the configuration status of the Gemini API key.")
def gemini_key_status_cmd() -> None:
    """Checks if the .gemini-api-key file exists and is populated."""
    show_gemini_key_status()


def show_gemini_key_status() -> None:
    """Helper to check and output the API key status."""
    from promptcli.key_manager import check_key_status

    status = check_key_status()
    if status == "exists":
        print_success("Gemini API key is configured and present in .gemini-api-key.")
    elif status == "empty":
        print_warning("The .gemini-api-key file exists but is empty.")
    else:
        print_error("Gemini API key is missing (no .gemini-api-key file found).")


@app.command("run", hidden=True)
def run_project(
    project: str = typer.Argument(..., help="The path to the project directory"),
    prompt: Optional[str] = typer.Argument(
        None,
        help="The prompt file name (extension optional)",
    ),
    list_prompts_flag: bool = typer.Option(
        False,
        "--list",
        help="List all available prompts in the project directory",
    ),
    feed_all: bool = typer.Option(
        False,
        "--feed-all",
        help="Generate outputs for all prompts in the project directory",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing output files without confirmation",
    ),
) -> None:
    """Internal command to handle project-specific prompts and feeds."""
    from promptcli.core import (
        ProjectNotFoundError,
        PromptNotFoundError,
        GenerationError,
        list_prompts,
        find_prompt_file,
        generate_output,
    )
    from promptcli.key_manager import load_key

    resolved_project_path = Path(project).resolve()

    # 1. Check if listing prompts
    if list_prompts_flag:
        try:
            prompts = list_prompts(project)
            if not prompts:
                print_info(f"No prompts found in project directory '{project}'.")
            else:
                display_prompts_table(project, prompts)
        except ProjectNotFoundError as e:
            print_error(str(e))
            raise typer.Exit(1)
        return

    # 2. Check if feeding all prompts
    if feed_all:
        api_key = load_key()
        if not api_key:
            print_error("Gemini API key is missing. Please save it first using: promptcli gemini-key --save")
            raise typer.Exit(1)

        try:
            prompts = list_prompts(project)
            if not prompts:
                print_warning(f"No prompts found in project directory '{project}' to feed.")
                return

            from rich.progress import (
                Progress,
                SpinnerColumn,
                TextColumn,
                BarColumn,
                TaskProgressColumn,
            )

            print_info(f"Feeding all {len(prompts)} prompts in project directory '{project}'...")

            success_count = 0
            failed_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Generating responses...", total=len(prompts))

                for p in prompts:
                    prompt_file = resolved_project_path / "prompts" / p["filename"]
                    progress.update(task, description=f"Processing {p['filename']}...")

                    try:
                        out_path = resolved_project_path / "outputs" / f"{prompt_file.stem}.md"
                        if out_path.exists() and not force:
                            # Suspend progress bar for interactive overwrite confirmation
                            progress.stop()
                            confirm = typer.confirm(
                                f"Output file '{out_path.name}' already exists. Overwrite?",
                                default=True,
                            )
                            progress.start()
                            if not confirm:
                                print_info(f"Skipped '{p['filename']}'.")
                                failed_count += 1
                                progress.advance(task)
                                continue

                        generate_output(project, prompt_file, api_key)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        print_error(f"Failed '{p['filename']}': {str(e)}")
                    progress.advance(task)

            # Summarize the run
            if success_count > 0:
                print_success(f"Successfully generated {success_count} prompt response(s).")
            if failed_count > 0:
                print_warning(f"Failed or skipped {failed_count} prompt response(s).")

        except ProjectNotFoundError as e:
            print_error(str(e))
            raise typer.Exit(1)
        return

    # 3. Handle single prompt generation
    if not prompt:
        print_error("Missing argument 'PROMPT'. Please specify a prompt file name or use --list / --feed-all.")
        raise typer.Exit(1)

    api_key = load_key()
    if not api_key:
        print_error("Gemini API key is missing. Please save it first using: promptcli gemini-key --save")
        raise typer.Exit(1)

    try:
        prompt_file = find_prompt_file(project, prompt)

        out_path = resolved_project_path / "outputs" / f"{prompt_file.stem}.md"
        if out_path.exists() and not force:
            confirm = typer.confirm(
                f"Output file '{out_path.name}' already exists. Overwrite?",
                default=True,
            )
            if not confirm:
                print_info("Cancelled response generation.")
                return

        with console.status(
            f"[bold green]Contacting Gemini API for '{prompt_file.name}'...",
            spinner="dots",
        ):
            out_file = generate_output(project, prompt_file, api_key)

        try:
            display_out = out_file.relative_to(Path.cwd())
        except ValueError:
            display_out = out_file

        print_success(f"Generated response saved to [cyan]{display_out}[/cyan].")

    except (ProjectNotFoundError, PromptNotFoundError) as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GenerationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1)


def main() -> None:
    """CLI entry point which transforms positional arguments to subcommand if needed."""
    # Reconfigure stdout/stderr to UTF-8 to prevent encoding errors on Windows console
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

    # Pre-parse arguments: if first argument is not a known subcommand/option,

    # route it dynamically to the hidden "run" subcommand.
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        known_commands = {
            "create",
            "gemini-key",
            "run",
            "--help",
            "-h",
            "--version",
            "-v",
        }
        if first_arg not in known_commands and not first_arg.startswith("-"):
            sys.argv.insert(1, "run")

    app()

