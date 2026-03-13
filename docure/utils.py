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
