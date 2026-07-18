# Spec-to-Parameters Extractor with Evaluation Harness — Implementation Plan v2

## Goal

Build a CLI tool that extracts RISC-V architectural parameters from spec prose using LLM prompting, evaluates extraction quality against a manually-verified gold-reference list sourced from the real [riscv-unified-db](https://github.com/riscv/riscv-unified-db), and reports precision/recall/F1 with full traceability.

---

## Proposed Changes

### Component 1: Repository Scaffolding

#### pyproject.toml

Python project config. Dependencies:
- `pyyaml` — YAML I/O
- `click` — CLI framework
- `pytest` — testing

LLM SDK dependencies (`google-genai`, `openai`) declared as optional extras, not hard requirements. The generic backend interface is defined first; SDK details never leak beyond the concrete backend class that wraps them.

#### LICENSE

BSD-3-Clause.

#### .gitignore

Standard Python gitignore + `results/raw/` exclusion except committed example files.

---

### Component 2: Spec Excerpt Preparation

This must happen before the gold reference. You cannot build a gold list before deciding exactly what text constitutes the evaluation corpus.

#### data/spec_excerpts/machine_counters.md

Scope: **§3.1.10–3.1.12 only** (Hardware Performance Monitor, mcounteren, mcountinhibit). Start with the smallest meaningful corpus.

Sourced from AsciiDoc at `riscv-isa-manual/src/machine.adoc`. Conversion rules:
- Preserve original section numbers exactly (§3.1.10, §3.1.11, §3.1.12)
- Record the source commit hash and file path at the top of the file
- Preserve table structure as-is
- No manual edits to prose content — only formatting conversion

---

### Component 3: Gold-Reference Dataset

#### data/gold_reference.yaml

Manually-verified gold list. Each entry:

```yaml
- name: HPM_COUNTER_EN
  category: named  # named | unnamed | config-dependent
  udb_file: spec/std/isa/param/HPM_COUNTER_EN.yaml
  section: "3.1.10"
  canonical_citation: >
    The hardware performance monitor includes 29 additional 64-bit event
    counters, mhpmcounter3–mhpmcounter31.
  secondary_citations: []
  related_parameters: [COUNTINHIBIT_EN, MCOUNTENABLE_EN]
  category_basis: "Direct UDB description: 'List of HPM counters that are enabled'"
  mapping_type: simple
```

No `aliases` field. Name matching uses case-insensitive normalization with underscore/space equivalence only.

#### docs/gold-reference.md

Documents: chapter selection rationale, construction procedure followed, inclusion/exclusion criteria, ambiguous cases log, validation steps performed, known limitations, UDB commit hash used.

---

### Component 4: Prompt Engineering

#### prompts/v1.md

First prompt iteration. Structure:
1. System context: "You are analyzing RISC-V specification text to identify architectural parameters..."
2. Category definitions: Named, unnamed, config-dependent
3. **One** few-shot example from a *different* chapter (not the evaluation chapter).
4. Output format specification: JSON array matching the candidate schema
5. Negative examples: things that look like parameters but aren't

#### prompts/current.md

Copy of the active prompt version. `run_extraction.py` loads this file.

---

### Component 5: Extraction Engine

#### src/extractor/backends.py

Generic backend interface defined first. No SDK imports at the interface level.

#### src/extractor/run_extraction.py

Orchestrates extraction:
1. Loads spec excerpt from `data/spec_excerpts/`
2. Loads prompt from `prompts/current.md`
3. Calls configured backend
4. Parses and validates raw LLM output against the candidate schema
5. Writes structured candidate list to `results/raw/`

---

### Component 6: Evaluation Engine

#### src/evaluation/diff.py

Pure comparison logic. No I/O, no API calls.

#### src/evaluation/metrics.py

Pure math. No I/O.

---

### Component 7: CLI

#### src/cli.py

Single entrypoint using Click.

---

### Component 8: Testing

#### tests/test_diff.py

Unit tests for `diff.py`.

#### tests/test_metrics.py

Unit tests for `metrics.py`.

---

### Component 9: Results & Documentation

#### results/example_candidates.yaml

Committed raw extractor output from the example run.

#### results/evaluation.md

Primary reviewer-facing artifact containing precision/recall tables and FP/FN logs.

#### README.md

Structure per PDS v3 §13.

---

## Verification Plan

### Automated Tests
```bash
pytest tests/ -v
```

### Manual Verification
- Gold-reference validation procedure
- One committed example run (spec → candidates → diff → metrics)
