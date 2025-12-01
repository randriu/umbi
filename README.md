# umbi

Library for input/output of transition systems in a *unified Markov binary (UMB)* format.

## Installation:

(optional) create and activate a python environment:

```
$ python -m venv venv
$ source venv/bin/activate
```

Install `umbi` via
```
(venv) $ pip install umbi
```

## Running umbi

Examples:
```
(venv) $ umbi --import-umb /path/to/input.umb
(venv) $ umbi --import-umb /path/to/input.umb --export-umb /path/to/output.umb
(venv) $ umbi --import-umb /path/to/input.umb --export-umb /path/to/output.umb --log-level=DEBUG
```

## Development

### Installing Development Tools
Run the following command to install all development dependencies:

```bash
pip install .[dev]
```

This will install tools for testing, linting, and other development tasks.


### Setting Up Pre-Commit Hooks
To ensure code quality and consistency, this repository uses `pre-commit` hooks. Developers should set up the hooks by running the following command:

```bash
pre-commit install
```

This will configure `pre-commit` to automatically run checks (e.g., linting, formatting) before each commit. To manually run the hooks on all files, use:

```bash
pre-commit run --all-files
```

