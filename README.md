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

Launch the desktop dashboard:

```bash
ahrs-ui
```

The **Connect** button currently starts a simulated telemetry stream so the UI can
be evaluated without hardware. Real serial data can be fed into the dashboard by
constructing `Telemetry` samples and passing them to `AHRSApp.update_telemetry()`.

## Project layout

```text
.
├── pyproject.toml
├── src/
│   └── ahrs/
│       ├── __init__.py
│       └── app.py
└── tests/
    └── test_package.py
```
