from datetime import date


def _today() -> str:
    return date.today().isoformat()


DEFAULT_INSTRUCTIONS = """\
## Conventions

### self.md Pattern

Every directory has a `self.md` that describes the directory's purpose and contents. The structure mirrors the source tree — if a directory exists in source, it should have a corresponding directory here with a `self.md`.

### Frontmatter Standard

**Directory index files (`self.md`):**

```yaml
---
type: directory-index
path: <path-to-this-dir>
mirrors: <source-path>           # the source directory this mirrors
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
last_updated_by: <author>
---
```

**File documentation (`<filename>.md`):**

```yaml
---
type: file-doc
mirrors: <source-file-path>
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
last_updated_by: <author>
---
```

### File Naming

- Each source file `example.py` gets a corresponding `example.md`
- Each directory gets a `self.md` describing its contents
- Keep documentation in sync with code changes

### File Size Guidance

- Keep individual files under **100 lines**
- If a document grows past 100 lines, split it into sub-documents in a subdirectory
- `self.md` files should be concise — typically 20-50 lines"""


def root_self_md(
    dir_name: str,
    contents: list[str],
    custom_instructions: str | None = None,
) -> str:
    """Generate the root self.md with usage instructions and conventions."""
    today = _today()
    contents_listing = "\n".join(f"- `{c}`" for c in sorted(contents))
    instructions = custom_instructions if custom_instructions is not None else DEFAULT_INSTRUCTIONS
    return f"""---
type: directory-index
path: {dir_name}
created: {today}
last_updated: {today}
---

# {dir_name}/

Documentation mirror of `{dir_name}/`. This directory maintains a parallel structure to the source code for long-term knowledge, architecture notes, and per-file documentation.

## Directory Structure

{contents_listing}

{instructions}
"""


def directory_self_md(dir_name: str, contents: list[str]) -> str:
    """Generate a self.md for a subdirectory."""
    today = _today()
    contents_listing = "\n".join(f"- `{c}`" for c in sorted(contents))
    return f"""---
type: directory-index
path: {dir_name}
created: {today}
last_updated: {today}
---

# {dir_name}/

## Contents

{contents_listing}
"""


def file_md(file_name: str) -> str:
    """Generate a documentation stub for a source file."""
    today = _today()
    return f"""---
type: file-doc
mirrors: {file_name}
created: {today}
last_updated: {today}
---

# {file_name}

## Overview

_Document the purpose of this file._

## Key Components

_Document the key classes, functions, and variables._
"""
