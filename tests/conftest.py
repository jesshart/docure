import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_src(tmp_path: Path) -> Path:
    """Create a temporary source tree matching the example structure."""
    src = tmp_path / "src"
    modules = src / "modules"
    modules.mkdir(parents=True)

    (src / "app.py").write_text("# app.py\n")
    (modules / "module_a.py").write_text("# module_a.py\n")
    (modules / "module_b.py").write_text("# module_b.py\n")
    # Add a non-python file that should be ignored
    (modules / "config.yaml").write_text("key: value\n")

    return src


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary directory with git init."""
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        capture_output=True,
    )
    return tmp_path
