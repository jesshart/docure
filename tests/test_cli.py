import subprocess
from pathlib import Path

from click.testing import CliRunner

from docure.cli import cli


def _make_src(base: Path) -> Path:
    """Create a source tree inside base and return its path."""
    src = base / "src"
    modules = src / "modules"
    modules.mkdir(parents=True)
    (src / "app.py").write_text("# app\n")
    (modules / "module_a.py").write_text("# a\n")
    return src


def _git_init(path: Path):
    """Initialize a git repo at path."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True)


def test_cli_init_creates_tree(tmp_path: Path):
    _git_init(tmp_path)
    src = _make_src(tmp_path)
    output = tmp_path / "docs"

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])

    assert result.exit_code == 0
    assert (output / "src" / "self.md").exists()
    assert (output / "src" / "app.md").exists()
    assert (output / "src" / "modules" / "self.md").exists()
    assert (output / "src" / "modules" / "module_a.md").exists()
    assert "Created" in result.output


def test_cli_init_custom_output(tmp_path: Path):
    src = _make_src(tmp_path)
    output = tmp_path / "custom" / "path"

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])

    assert result.exit_code == 0
    assert (output / "src" / "self.md").exists()


def test_cli_init_default_skips_existing(tmp_path: Path):
    """Default behavior skips existing files (non-destructive)."""
    src = _make_src(tmp_path)
    output = tmp_path / "docs"

    runner = CliRunner()
    # First run
    runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])
    # Second run — default should skip existing
    result = runner.invoke(
        cli, ["init", str(src), "-o", str(output), "-y"]
    )

    assert result.exit_code == 0
    assert "skipped" in result.output.lower()
    assert "Nothing to do" in result.output


def test_cli_init_force_overwrites(tmp_path: Path):
    """--force overwrites existing files."""
    src = _make_src(tmp_path)
    output = tmp_path / "docs"

    runner = CliRunner()
    # First run
    runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])
    # Modify a file to verify it gets overwritten
    existing_file = output / "src" / "app.md"
    existing_file.write_text("custom content\n")
    # Second run with --force
    result = runner.invoke(
        cli, ["init", str(src), "-o", str(output), "--force", "-y"]
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    # File should have been overwritten with template content
    assert existing_file.read_text() != "custom content\n"


def test_cli_init_nonexistent_path_errors():
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "/nonexistent/path", "-y"])

    assert result.exit_code != 0


def test_cli_init_prompts_for_default_output(tmp_path: Path):
    _git_init(tmp_path)
    src = _make_src(tmp_path)

    runner = CliRunner()
    # Send "n" to decline the default output prompt
    result = runner.invoke(cli, ["init", str(src)], input="n\n")

    assert "Output directory not specified" in result.output
    assert "Continue with this output path?" in result.output


def test_cli_init_aborts_on_no(tmp_path: Path):
    _git_init(tmp_path)
    src = _make_src(tmp_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src)], input="n\n")

    assert result.exit_code != 0
    assert "Aborted" in result.output


def test_cli_init_yes_flag_skips_prompts(tmp_path: Path):
    _git_init(tmp_path)
    src = _make_src(tmp_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "-y"])

    assert result.exit_code == 0
    assert "Created" in result.output
    # Should have written to thoughts/ at git root
    assert (tmp_path / "thoughts" / "src" / "self.md").exists()


def test_cli_init_force_prompts_for_overwrite(tmp_path: Path):
    """--force without -y prompts before overwriting."""
    src = _make_src(tmp_path)
    output = tmp_path / "docs"

    runner = CliRunner()
    # First run
    runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])
    # Second run with --force — decline overwrite
    result = runner.invoke(
        cli, ["init", str(src), "-o", str(output), "--force"], input="n\n"
    )

    assert "already exist" in result.output
    assert "Aborted" in result.output


def test_cli_init_dot_path(tmp_path: Path):
    """docure init . should use the actual directory name, not '.'."""
    # Create .py files directly in tmp_path
    (tmp_path / "app.py").write_text("# app\n")
    output = tmp_path / "docs"

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(tmp_path), "-o", str(output), "-y"])

    assert result.exit_code == 0
    # Should use the resolved directory name, not "."
    dir_name = tmp_path.name
    assert (output / dir_name / "self.md").exists()
    content = (output / dir_name / "self.md").read_text()
    assert dir_name in content
    assert content.startswith(f"# {dir_name}/")  # Should use actual dir name, not "."


def test_cli_init_ignores_pycache(tmp_path: Path):
    """__pycache__ directories should be skipped."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("# app\n")
    pycache = src / "__pycache__"
    pycache.mkdir()
    (pycache / "app.cpython-313.pyc").write_text("bytecode\n")
    output = tmp_path / "docs"

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])

    assert result.exit_code == 0
    assert not (output / "src" / "__pycache__").exists()


def test_cli_init_handles_init_py(tmp_path: Path):
    """__init__.py should produce __init__.md."""
    src = tmp_path / "pkg"
    src.mkdir()
    (src / "__init__.py").write_text("# init\n")
    (src / "core.py").write_text("# core\n")
    output = tmp_path / "docs"

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])

    assert result.exit_code == 0
    assert (output / "pkg" / "__init__.md").exists()
    assert (output / "pkg" / "core.md").exists()


def test_cli_init_hidden_dirs_skipped(tmp_path: Path):
    """Hidden directories (starting with .) should be skipped."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("# app\n")
    hidden = src / ".hidden"
    hidden.mkdir()
    (hidden / "secret.py").write_text("# secret\n")
    output = tmp_path / "docs"

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])

    assert result.exit_code == 0
    assert not (output / "src" / ".hidden").exists()


def test_cli_init_deeply_nested(tmp_path: Path):
    """Handles 3+ levels of nesting correctly."""
    src = tmp_path / "src"
    deep = src / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "deep.py").write_text("# deep\n")
    output = tmp_path / "docs"

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "-o", str(output), "-y"])

    assert result.exit_code == 0
    assert (output / "src" / "a" / "b" / "c" / "deep.md").exists()
    assert (output / "src" / "a" / "b" / "c" / "self.md").exists()
    assert (output / "src" / "a" / "b" / "self.md").exists()
    assert (output / "src" / "a" / "self.md").exists()
    assert (output / "src" / "self.md").exists()


def test_cli_init_custom_name(tmp_path: Path):
    """--name flag changes the root documentation directory name."""
    _git_init(tmp_path)
    src = _make_src(tmp_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "--name", "docs", "-y"])

    assert result.exit_code == 0
    assert (tmp_path / "docs" / "src" / "self.md").exists()
    assert not (tmp_path / "thoughts").exists()


def test_cli_init_default_name_is_thoughts(tmp_path: Path):
    """Default --name is 'thoughts'."""
    _git_init(tmp_path)
    src = _make_src(tmp_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(src), "-y"])

    assert result.exit_code == 0
    assert (tmp_path / "thoughts" / "src" / "self.md").exists()
