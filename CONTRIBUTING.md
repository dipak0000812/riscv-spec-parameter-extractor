# Contributing

Thank you for taking the time to look at this project.

## Running the Project

```bash
# Install with dev dependencies
pip install -e .[dev]

# Run the full pipeline offline (no API key needed)
python -m src.cli run --backend mock

# Run the test suite
python -m pytest -v
```

## Code Style

- Python 3.11+
- Follow the existing module structure: keep I/O in `cli.py`, keep logic in `evaluation/` and `extractor/` pure where possible.
- No new dependencies without updating `pyproject.toml`.

## Making Changes

- Open an issue before starting significant work so we can discuss the approach.
- Keep pull requests focused — one logical change per PR.
- Add or update tests for any changes to `diff.py`, `metrics.py`, or `run_extraction.py`.
- Do not modify `data/gold_reference.yaml` without updating the construction methodology in `docs/gold-reference.md`.
