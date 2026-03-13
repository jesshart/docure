import subprocess
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
