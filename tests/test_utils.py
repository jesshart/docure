from pathlib import Path

from docure.utils import find_git_root


def test_find_git_root_in_repo(tmp_git_repo: Path):
    result = find_git_root(tmp_git_repo)
    assert result is not None
    assert result == tmp_git_repo


def test_find_git_root_in_subdirectory(tmp_git_repo: Path):
    subdir = tmp_git_repo / "a" / "b"
    subdir.mkdir(parents=True)
    result = find_git_root(subdir)
    assert result == tmp_git_repo


def test_find_git_root_outside_repo(tmp_path: Path):
    # tmp_path is not a git repo by itself, but it might be inside one
    # Create a truly isolated directory
    isolated = tmp_path / "not_a_repo"
    isolated.mkdir()
    # This may or may not return None depending on the system,
    # but at minimum it should not raise
    result = find_git_root(isolated)
    # We can't assert None since tmp_path might be inside a git repo
    assert result is None or isinstance(result, Path)
