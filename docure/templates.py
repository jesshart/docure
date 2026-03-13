def root_self_md(dir_name: str, contents: list[str]) -> str:
    """Generate the root self.md with usage instructions."""
    contents_listing = "\n".join(f"- `{c}`" for c in sorted(contents))
    return f"""# {dir_name}/ — Documentation Root

This directory mirrors the structure of `{dir_name}/` for documentation purposes.

## How to Use This Documentation

- **self.md** files describe the purpose and contents of their directory
- **<filename>.md** files document the corresponding source file
- Keep documentation in sync with code changes

## Contents

{contents_listing}
"""


def directory_self_md(dir_name: str, contents: list[str]) -> str:
    """Generate a self.md for a subdirectory."""
    contents_listing = "\n".join(f"- `{c}`" for c in sorted(contents))
    return f"""# {dir_name}/

## Contents

{contents_listing}
"""


def file_md(file_name: str) -> str:
    """Generate a documentation stub for a Python file."""
    return f"""# {file_name}

## Overview

_Document the purpose of this file._

## Key Components

_Document the key classes, functions, and variables._
"""
