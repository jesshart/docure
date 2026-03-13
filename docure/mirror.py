from dataclasses import dataclass, field
from pathlib import Path

from docure.templates import directory_self_md, file_md, root_self_md


@dataclass
class MirrorResult:
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    existing: list[Path] = field(default_factory=list)


def plan_mirror(src: Path, output_root: Path) -> list[tuple[Path, str]]:
    """Plan the mirror tree without writing anything.

    Returns a list of (output_path, content) tuples.
    """
    planned: list[tuple[Path, str]] = []

    def _skip(name: str) -> bool:
        return name.startswith((".", "__"))

    for dir_path, dirnames, filenames in src.walk():
        # Skip __pycache__ and hidden directories
        dirnames[:] = sorted(d for d in dirnames if not _skip(d))

        rel = dir_path.relative_to(src)
        out_dir = output_root / rel

        # Collect contents for this directory's self.md
        py_files = sorted(f for f in filenames if f.endswith(".py"))
        subdirs = dirnames  # already sorted above
        contents = [f"{d}/" for d in subdirs] + py_files

        # Generate self.md
        is_root = dir_path == src
        if is_root:
            content = root_self_md(src.name, contents)
        else:
            content = directory_self_md(dir_path.name, contents)
        planned.append((out_dir / "self.md", content))

        # Generate file .md stubs
        for f in py_files:
            planned.append((out_dir / f"{Path(f).stem}.md", file_md(f)))

    return planned


def build_mirror(
    src: Path, output_root: Path, step_over: bool
) -> MirrorResult:
    """Build the mirror documentation tree.

    Args:
        src: Source directory to mirror.
        output_root: Root of the output documentation tree.
        step_over: If True, skip existing files. If False, overwrite them.

    Returns:
        MirrorResult with lists of created, skipped, and existing files.
    """
    result = MirrorResult()
    planned = plan_mirror(src, output_root)

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
