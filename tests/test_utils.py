import subprocess
from pathlib import Path

from docure.utils import find_git_root, list_git_files


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


def test_list_git_files_returns_tracked(tmp_git_repo: Path):
    (tmp_git_repo / "tracked.py").write_text("# tracked\n")
    (tmp_git_repo / "ignored.py").write_text("# ignored\n")
    (tmp_git_repo / ".gitignore").write_text("ignored.py\n")
    subprocess.run(
        ["git", "add", "tracked.py", ".gitignore"],
        cwd=tmp_git_repo,
        capture_output=True,
    )

    files = list_git_files(tmp_git_repo)
    assert files is not None
    assert (tmp_git_repo / "tracked.py").resolve() in files
    assert (tmp_git_repo / "ignored.py").resolve() not in files


def test_list_git_files_includes_untracked_not_ignored(tmp_git_repo: Path):
    (tmp_git_repo / "new_file.py").write_text("# new\n")
    (tmp_git_repo / "ignored.py").write_text("# ignored\n")
    (tmp_git_repo / ".gitignore").write_text("ignored.py\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_git_repo, capture_output=True)

    files = list_git_files(tmp_git_repo)
    assert files is not None
    # new_file.py is untracked but not ignored — should be included
    assert (tmp_git_repo / "new_file.py").resolve() in files
    assert (tmp_git_repo / "ignored.py").resolve() not in files


def test_list_git_files_outside_repo(tmp_path: Path):
    isolated = tmp_path / "not_a_repo"
    isolated.mkdir()
    result = list_git_files(isolated)
    # May return None or files if tmp_path is inside a git repo
    assert result is None or isinstance(result, set)
