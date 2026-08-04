# AHRS

Attitude and Heading Reference System tools in Python.

## Development

Create a virtual environment and install the project with its development tools:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the tests and linter:

```bash
pytest
ruff check .
```

## Project layout

```text
.
├── pyproject.toml
├── src/
│   └── ahrs/
│       └── __init__.py
└── tests/
    └── test_package.py
```
