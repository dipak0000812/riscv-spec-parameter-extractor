"""Validation suite for the gold-reference parameters database.

Ensures that data/gold_reference.yaml strictly conforms to the rules
defined in docs/gold-reference-schema.md.
"""

from pathlib import Path
from src.cli import validate_gold_file


def test_gold_reference_schema() -> None:
    """Validate data/gold_reference.yaml against the schema using the core validator."""
    project_root = Path(__file__).parent.parent
    gold_path = project_root / "data" / "gold_reference.yaml"
    spec_path = project_root / "data" / "spec_excerpts" / "machine_counters.md"

    # Execute the core validation suite
    errors = validate_gold_file(gold_path, spec_path)
    assert not errors, f"Gold reference validation failed:\n" + "\n".join(f" - {err}" for err in errors)
