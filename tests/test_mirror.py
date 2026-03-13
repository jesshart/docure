from pathlib import Path

from docure.mirror import build_mirror, plan_mirror
from docure.templates import root_self_md


def test_plan_mirror_produces_correct_files(tmp_src: Path, tmp_path: Path):
    output = tmp_path / "thoughts" / "src"
    planned = plan_mirror(tmp_src, output)
    paths = {p for p, _ in planned}

    assert output / "self.md" in paths
    assert output / "app.md" in paths
    assert output / "modules" / "self.md" in paths
    assert output / "modules" / "module_a.md" in paths
    assert output / "modules" / "module_b.md" in paths


def test_plan_mirror_ignores_non_py_files(tmp_src: Path, tmp_path: Path):
    output = tmp_path / "thoughts" / "src"
    planned = plan_mirror(tmp_src, output)
    paths = {p for p, _ in planned}

    # config.yaml should not appear
    assert output / "modules" / "config.md" not in paths


def test_build_mirror_creates_correct_structure(tmp_src: Path, tmp_path: Path):
    output = tmp_path / "thoughts" / "src"
    result = build_mirror(tmp_src, output, step_over=False)

    assert (output / "self.md").exists()
    assert (output / "app.md").exists()
    assert (output / "modules" / "self.md").exists()
    assert (output / "modules" / "module_a.md").exists()
    assert (output / "modules" / "module_b.md").exists()
    assert len(result.created) == 5
    assert len(result.skipped) == 0
    assert len(result.existing) == 0


def test_build_mirror_creates_self_md_for_directories(
    tmp_src: Path, tmp_path: Path
):
    output = tmp_path / "thoughts" / "src"
    build_mirror(tmp_src, output, step_over=False)

    root_self = (output / "self.md").read_text()
    assert "type: directory-index" in root_self
    assert "self.md Pattern" in root_self
    assert "Frontmatter Standard" in root_self

    modules_self = (output / "modules" / "self.md").read_text()
    assert "type: directory-index" in modules_self
    assert "modules" in modules_self


def test_build_mirror_only_mirrors_py_files(tmp_src: Path, tmp_path: Path):
    output = tmp_path / "thoughts" / "src"
    build_mirror(tmp_src, output, step_over=False)

    # config.yaml should not have a corresponding .md
    assert not (output / "modules" / "config.md").exists()


def test_build_mirror_reports_existing_files(tmp_src: Path, tmp_path: Path):
    output = tmp_path / "thoughts" / "src"
    # First run
    build_mirror(tmp_src, output, step_over=False)
    # Second run without step_over — existing files get overwritten but tracked
    result = build_mirror(tmp_src, output, step_over=False)

    assert len(result.existing) > 0
    assert len(result.created) > 0  # they still get written


def test_build_mirror_skips_existing_with_step_over(
    tmp_src: Path, tmp_path: Path
):
    output = tmp_path / "thoughts" / "src"
    # First run
    build_mirror(tmp_src, output, step_over=False)
    # Second run with step_over
    result = build_mirror(tmp_src, output, step_over=True)

    assert len(result.skipped) == 5
    assert len(result.created) == 0


def test_root_self_md_contains_instructions():
    content = root_self_md("src", ["app.py", "modules/"])
    assert "type: directory-index" in content
    assert "self.md Pattern" in content
    assert "Frontmatter Standard" in content
    assert "File Size Guidance" in content
    assert "`app.py`" in content
    assert "`modules/`" in content
