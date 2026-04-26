# Jan Workspace Manager

Workspace manager for the Jan chat application.

## Features
- Manages workspaces used by Jan
- GUI app built with wxPython
- GitHub sync with auto-commit and push for workspace updates
- Pull workspaces from a configured Git repository on demand or startup
- Clone or replace repositories: Working with multiple workspace repos

## Requirements
- Python 3.10+

## Installation
From PyPI:

```bash
pip install janwsmanager
```

From source:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install .
```

## Usage
After installation:

```bash
./janws
```

## Dependencies
- appdirs
- GitPython
- wxPython
