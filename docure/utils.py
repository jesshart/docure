import subprocess
import tomllib
from pathlib import Path


def find_git_root(start: Path) -> Path | None:
    """Find the git repository root from a starting path."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=start if start.is_dir() else start.parent,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return None


def list_git_files(directory: Path) -> set[Path] | None:
    """List files tracked by git (respecting .gitignore) under a directory.

    Returns a set of absolute Paths, or None if not in a git repo.
    Uses `git ls-files` for tracked files and `git ls-files --others --exclude-standard`
    for untracked-but-not-ignored files, giving us all files git knows about.
    """
    try:
        # Tracked files
        tracked = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            cwd=directory,
        )
        if tracked.returncode != 0:
            return None

        # Untracked but not ignored (new files the user hasn't staged yet)
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            cwd=directory,
        )

        files: set[Path] = set()
        for line in tracked.stdout.strip().splitlines():
            if line:
                files.add((directory / line).resolve())
        if untracked.returncode == 0:
            for line in untracked.stdout.strip().splitlines():
                if line:
                    files.add((directory / line).resolve())
        return files
    except FileNotFoundError:
        return None


def load_root_self_instructions(search_from: Path) -> str | None:
    """Load custom root self.md instructions from config.

    Checks in order:
    1. pyproject.toml [tool.docure] root_self_instructions
    2. .docure.toml root_self_instructions

    The value should be a path to a markdown file, resolved relative
    to the config file's directory.

    Returns the file contents, or None if no config found.
    """
    search_dir = search_from if search_from.is_dir() else search_from.parent

    # Walk up to find config files
    git_root = find_git_root(search_dir)
    dirs_to_check = [search_dir]
    if git_root and git_root != search_dir:
        dirs_to_check.append(git_root)

    for check_dir in dirs_to_check:
        # Check pyproject.toml
        pyproject = check_dir / "pyproject.toml"
        if pyproject.exists():
            path = _read_instructions_path(pyproject, ("tool", "docure"))
            if path:
                resolved = _resolve_instructions(pyproject.parent, path)
                if resolved:
                    return resolved

        # Check .docure.toml
        docure_toml = check_dir / ".docure.toml"
        if docure_toml.exists():
            path = _read_instructions_path(docure_toml, ())
            if path:
                resolved = _resolve_instructions(docure_toml.parent, path)
                if resolved:
                    return resolved

    return None


def _read_instructions_path(
    toml_path: Path, key_prefix: tuple[str, ...]
) -> str | None:
    """Read root_self_instructions value from a TOML file."""
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        for key in key_prefix:
            data = data.get(key, {})
        return data.get("root_self_instructions")
    except (tomllib.TOMLDecodeError, AttributeError):
        return None


def _resolve_instructions(base_dir: Path, rel_path: str) -> str | None:
    """Resolve and read a markdown instructions file."""
    instructions_file = base_dir / rel_path
    if instructions_file.exists():
        return instructions_file.read_text()
    return None
