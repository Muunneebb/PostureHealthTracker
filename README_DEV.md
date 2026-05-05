# Development setup

Quick steps to set up a local development environment and run tests.

1. Create a Python virtual environment (from project root):

```bash
python3 -m venv .venv
```

2. Activate the virtual environment:

```bash
source .venv/bin/activate
```

3. Install runtime and development dependencies:

```bash
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

4. Run tests:

```bash
pytest -q
```

Notes:
- The project includes many optional system-specific packages; consider installing only what's needed for your environment.
- `.venv` is included in `.gitignore` to avoid committing virtual environments.
