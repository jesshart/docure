# docure

Mirror your code structure into a documentation tree.

docure walks a source directory and creates a parallel structure of markdown files — one `.md` per source file, plus a `self.md` for each directory. It respects `.gitignore` automatically.

## Quickstart

Given a project like this:

```
.
├── app/
│   └── src/
│       ├── app.py
│       └── modules/
│           ├── module_a.py
│           └── module_b.py
└── pyproject.toml
```

Run:

```bash
uvx --from "git+https://github.com/jesshart/docure" docure init app
```

And docure produces a parallel documentation tree:

```
.
├── app/
│   └── src/
│       ├── app.py
│       └── modules/
│           ├── module_a.py
│           └── module_b.py
├── thoughts/
│   └── app/
│       ├── self.md
│       └── src/
│           ├── self.md
│           ├── app.md
│           └── modules/
│               ├── self.md
│               ├── module_a.md
│               └── module_b.md
└── pyproject.toml
```

## Install

```bash
# Run directly (no install needed)
uvx --from "git+https://github.com/jesshart/docure" docure init <path>

# Or install into a project
uv add "docure @ git+https://github.com/jesshart/docure"
```

## Usage

```bash
# Basic — mirrors src/ into thoughts/src/ at your git root
docure init src

# Custom output directory
docure init src -o docs/api

# Custom root directory name (default: thoughts)
docure init src --name wiki

# Include specific file types (default: .py only)
docure init src --file-types .py .js .ts

# Include all file types (respects .gitignore)
docure init src --file-types all

# Overwrite existing documentation files
docure init src --force

# Skip all confirmation prompts
docure init src -y
```

## Behavior

- **Safe by default** — existing files are skipped, not overwritten. Use `--force` to overwrite.
- **Prompts before acting** — all default actions (output path, file types) require confirmation. Use `-y` to auto-confirm.
- **Respects .gitignore** — when inside a git repo, only tracked and untracked-but-not-ignored files are mirrored.
- **Skips noise** — `__pycache__/`, hidden directories (`.`-prefixed), and other non-essential directories are always excluded.

## Generated files

- **`self.md`** — created in each directory. The root `self.md` includes usage instructions; subdirectory `self.md` files list their contents.
- **`<filename>.md`** — a documentation stub for each source file, with sections for overview and key components.
