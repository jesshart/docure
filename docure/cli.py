from pathlib import Path

import click

from docure.mirror import build_mirror, plan_mirror
from docure.utils import find_git_root, list_git_files, load_root_self_instructions


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Docure - Mirror your code structure into documentation."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _resolve_output(
    path: Path, output: Path | None, name: str, yes: bool
) -> Path | None:
    """Resolve the output directory path. Returns None if user aborts."""
    if output is not None:
        return output / path.name

    resolved_path = path.resolve()
    git_root = find_git_root(resolved_path)
    if git_root:
        base = git_root / name
        click.echo("Output directory not specified.")
        click.echo(f"  → Detected git root: {click.style(str(git_root), bold=True)}")
    else:
        base = Path.cwd() / name
        click.echo("Output directory not specified.")
        click.echo(f"  → No git root detected, using CWD")

    # If path is the root itself, write directly to base (no extra nesting)
    if git_root and resolved_path == git_root:
        resolved = base
    elif not git_root and resolved_path == Path.cwd():
        resolved = base
    else:
        resolved = base / path.name
    click.echo(f"  → Will write to: {click.style(str(resolved), bold=True)}")
    click.echo()

    if not yes:
        if not click.confirm("Continue with this output path?", default=False):
            click.echo()
            click.echo("Aborted. Re-run with -o to specify a custom output path:")
            click.echo(f"  docure init {path} -o path/to/output")
            return None

    return resolved


def _format_tree(files: list[tuple[Path, str]], output_root: Path) -> str:
    """Format a list of planned files as a simple indented tree."""
    lines = []
    rel_paths = sorted(p.relative_to(output_root.parent) for p, _ in files)

    # Group by directory depth for tree-like display
    for rel in rel_paths:
        depth = len(rel.parts) - 1
        prefix = "  " * depth + ("├── " if depth > 0 else "")
        lines.append(f"  {prefix}{rel.parts[-1]}")

    return "\n".join(lines)


@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory. Defaults to thoughts/ at git root or CWD.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing files (prompts for confirmation unless -y).",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    default=False,
    help="Auto-confirm all prompts.",
)
@click.option(
    "--name",
    type=str,
    default="thoughts",
    show_default=True,
    help="Name of the root documentation directory.",
)
@click.option(
    "--file-types",
    multiple=True,
    default=None,
    help="File extensions to include (e.g. .py .js .ts) or 'all'. Defaults to .py only.",
)
@click.option(
    "--root-self-instructions",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to a markdown file with custom root self.md instructions.",
)
def init(
    path: Path,
    output: Path | None,
    force: bool,
    yes: bool,
    name: str,
    file_types: tuple[str, ...],
    root_self_instructions: Path | None,
):
    """Initialize documentation tree mirroring PATH."""
    # Resolve "." and trailing slashes to the actual directory name
    path = Path(path.resolve())

    # Resolve custom root self.md instructions
    # Priority: --root-self-instructions flag > pyproject.toml > .docure.toml > default
    if root_self_instructions is not None:
        custom_instructions = root_self_instructions.read_text()
        click.echo(
            click.style(
                f"Using custom root instructions from: {root_self_instructions}",
                fg="cyan",
            )
        )
    else:
        custom_instructions = load_root_self_instructions(path)
        if custom_instructions is not None:
            click.echo(
                click.style(
                    "Using custom root instructions from config.",
                    fg="cyan",
                )
            )

    # Resolve file types — default to .py with a warning
    if not file_types:
        ft_list = [".py"]
        click.echo(
            click.style(
                "No --file-types specified. Defaulting to .py files only.",
                fg="yellow",
            )
        )
        click.echo(
            click.style(
                "  Use --file-types to include other extensions (e.g. --file-types .py .js .ts)",
                fg="yellow",
            )
        )
        click.echo(
            click.style(
                "  Use --file-types all to include all files.",
                fg="yellow",
            )
        )
        click.echo()
        if not yes:
            if not click.confirm("Continue with .py files only?", default=False):
                click.echo("Aborted.")
                raise SystemExit(1)
    else:
        ft_list = list(file_types)

    resolved_output = _resolve_output(path, output, name, yes)
    if resolved_output is None:
        raise SystemExit(1)

    # Get git-tracked files to respect .gitignore
    git_files = list_git_files(path)
    if git_files is not None:
        click.echo(
            click.style("Respecting .gitignore (git repo detected).", fg="cyan")
        )
    else:
        click.echo(
            click.style("No git repo detected — all files on disk will be considered.", fg="cyan")
        )

    # Plan the mirror to show preview
    planned = plan_mirror(path, resolved_output, file_types=ft_list, git_files=git_files, custom_instructions=custom_instructions)

    if not planned:
        click.echo("No matching files found to document.")
        return

    # Check for existing files
    existing = [p for p, _ in planned if p.exists()]
    new_files = [p for p, _ in planned if not p.exists()]

    # Show preview
    click.echo()
    click.echo("Will create the following documentation tree:")
    click.echo()
    click.echo(_format_tree(planned, resolved_output))
    click.echo()

    if existing and force:
        click.echo(
            click.style(
                f"⚠ {len(existing)} file(s) already exist and will be overwritten:",
                fg="yellow",
            )
        )
        for p in existing:
            click.echo(click.style(f"  - {p}", fg="yellow"))
        click.echo()
        if not yes:
            if not click.confirm("Overwrite these files?", default=False):
                click.echo("Aborted.")
                raise SystemExit(1)
    elif existing:
        click.echo(
            click.style(
                f"{len(existing)} existing file(s) will be skipped.",
                fg="yellow",
            )
        )

    total = len(new_files) + (len(existing) if force else 0)
    if total > 0:
        click.echo(f"  {total} file(s) will be written.")
        click.echo()
        if not yes:
            if not click.confirm("Proceed?", default=False):
                click.echo("Aborted.")
                raise SystemExit(1)
    else:
        click.echo("Nothing to do — all files already exist. Use --force to overwrite.")
        return

    # Execute: default is skip existing (step_over=True), --force overwrites (step_over=False)
    result = build_mirror(path, resolved_output, step_over=not force, file_types=ft_list, git_files=git_files, custom_instructions=custom_instructions)

    # Report results
    click.echo()
    if result.created:
        click.echo(click.style(f"✓ Created {len(result.created)} file(s):", fg="green"))
        for p in result.created:
            click.echo(click.style(f"  + {p}", fg="green"))

    if result.skipped:
        click.echo(
            click.style(
                f"Skipped {len(result.skipped)} existing file(s).",
                fg="yellow",
            )
        )

    click.echo()
    click.echo(click.style("Done!", fg="green", bold=True))


if __name__ == "__main__":
    cli()
