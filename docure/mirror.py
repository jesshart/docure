from dataclasses import dataclass, field
from pathlib import Path

from docure.templates import directory_self_md, file_md, root_self_md


@dataclass
class MirrorResult:
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    existing: list[Path] = field(default_factory=list)


def _matches_file_types(filename: str, file_types: list[str]) -> bool:
    """Check if a filename matches the given file type extensions."""
    if "all" in file_types:
        return True
    return any(filename.endswith(ext) for ext in file_types)


def plan_mirror(
    src: Path,
    output_root: Path,
    file_types: list[str] | None = None,
    git_files: set[Path] | None = None,
) -> list[tuple[Path, str]]:
    """Plan the mirror tree without writing anything.

    Args:
        src: Source directory to mirror.
        output_root: Root of the output documentation tree.
        file_types: List of file extensions (e.g. [".py", ".js"]) or ["all"].
            Defaults to [".py"].
        git_files: Set of absolute paths from git ls-files. When provided,
            only files in this set are included (respects .gitignore).
            When None, all files on disk are considered.

    Returns a list of (output_path, content) tuples.
    """
    if file_types is None:
        file_types = [".py"]

    planned: list[tuple[Path, str]] = []

    def _skip_dir(name: str) -> bool:
        return name.startswith((".", "__"))

    def _include_file(dir_path: Path, filename: str) -> bool:
        if not _matches_file_types(filename, file_types):
            return False
        if git_files is not None:
            return (dir_path / filename).resolve() in git_files
        return True

    def _has_git_files_in_dir(dir_path: Path) -> bool:
        """Check if a directory has any git-tracked files under it."""
        if git_files is None:
            return True
        dir_resolved = dir_path.resolve()
        return any(str(f).startswith(str(dir_resolved)) for f in git_files)

    for dir_path, dirnames, filenames in src.walk():
        # Skip __pycache__ and hidden directories
        dirnames[:] = sorted(d for d in dirnames if not _skip_dir(d))

        # When using git files, also skip directories with no tracked content
        if git_files is not None:
            dirnames[:] = [d for d in dirnames if _has_git_files_in_dir(dir_path / d)]

        rel = dir_path.relative_to(src)
        out_dir = output_root / rel

        # Collect matching files
        matched_files = sorted(
            f for f in filenames if _include_file(dir_path, f)
        )
        subdirs = dirnames  # already sorted/filtered above
        contents = [f"{d}/" for d in subdirs] + matched_files

        # Generate self.md
        is_root = dir_path == src
        if is_root:
            content = root_self_md(src.name, contents)
        else:
            content = directory_self_md(dir_path.name, contents)
        planned.append((out_dir / "self.md", content))

        # Generate file .md stubs
        for f in matched_files:
            planned.append((out_dir / f"{Path(f).stem}.md", file_md(f)))

    return planned


def build_mirror(
    src: Path,
    output_root: Path,
    step_over: bool,
    file_types: list[str] | None = None,
    git_files: set[Path] | None = None,
) -> MirrorResult:
    """Build the mirror documentation tree.

    Args:
        src: Source directory to mirror.
        output_root: Root of the output documentation tree.
        step_over: If True, skip existing files. If False, overwrite them.
        file_types: List of file extensions or ["all"]. Defaults to [".py"].
        git_files: Set of git-tracked file paths (respects .gitignore).

    Returns:
        MirrorResult with lists of created, skipped, and existing files.
    """
    result = MirrorResult()
    planned = plan_mirror(src, output_root, file_types=file_types, git_files=git_files)

    for out_path, content in planned:
        if out_path.exists():
            if step_over:
                result.skipped.append(out_path)
                continue
            else:
                result.existing.append(out_path)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content)
        result.created.append(out_path)

    return result
