# RISC-V Spec-to-Parameters Extractor with Evaluation Harness

A tool for extracting implementation-configurable architectural parameters from RISC-V ISA specification prose using LLMs, with automated precision/recall evaluation against a Unified Database (UDB) derived gold reference.

## Motivation

RISC-V processor specifications describe many configuration options that vary between implementations — counter presence, optional CSRs, platform limits. Extracting these parameters manually to populate hardware verification databases or Unified Databases (UDB) is tedious and error-prone. This project builds an LLM-based extraction pipeline paired with a deterministic evaluation harness to measure extraction quality against a verified gold reference.

## Repository Scope

The current scope is strictly **Machine-Level Performance Counters & HPM (§3.1.10–§3.1.12)** of the RISC-V Privileged ISA Manual. This section defines performance-monitoring counter registers, event selectors, and availability control behaviors. Extraction and evaluation target the 8 canonical parameters in this range, each traced to a source file in the RISC-V Unified Database.

## Installation

Requires Python 3.11+. Create and activate a virtual environment, then install:

```bash
# Core package with dev dependencies
pip install -e .[dev]

# Optional: add Gemini support
pip install -e .[gemini]

# Optional: add OpenAI support
pip install -e .[openai]
```

## Quickstart

Run the complete pipeline offline — no API key required:

```bash
python -m src.cli run --backend mock
```

This runs extraction using the deterministic mock backend, writes candidates to
`results/raw/candidates.yaml`, and generates a metrics report at `results/evaluation.md`.

A pre-generated example report is committed at [`results/evaluation.md`](results/evaluation.md)
and can be read without running anything.

To verify the test suite:

```bash
python -m pytest -v
```

## Running with Gemini

Set `GEMINI_API_KEY` as an environment variable (recommended over passing it on the command line):

```bash
export GEMINI_API_KEY=your_key_here
python -m src.cli run --backend gemini --model gemini-2.5-flash
```

## Running with OpenAI

Set `OPENAI_API_KEY` as an environment variable:

```bash
export OPENAI_API_KEY=your_key_here
python -m src.cli run --backend openai --model gpt-4o-mini
```

## Running Evaluation Separately

If you already have a candidates YAML file from a previous extraction run:

```bash
python -m src.cli evaluate \
  --candidates results/example_candidates.yaml \
  --gold data/gold_reference.yaml \
  --output results/evaluation.md
```

## Project Layout

```
data/
  gold_reference.yaml             # Curated gold reference (8 parameters, UDB-traced)
  spec_excerpts/machine_counters.md  # Target specification excerpt (§3.1.10–§3.1.12)
docs/
  gold-reference-schema.md        # Schema definition for gold_reference.yaml
  gold-reference.md               # Construction methodology and inclusion criteria
  methodology.md                  # Category definitions and worked examples
  engineering-decisions.md        # Design decisions and rationale
  architecture.md                 # Package layout and design principles
prompts/
  current.md                      # Active prompt template (v1)
  v1.md                           # Versioned prompt archive
results/
  evaluation.md                   # Committed example evaluation report
  example_candidates.yaml         # Committed example extraction output
src/
  cli.py                          # CLI entrypoint (validate-gold, extract, evaluate, run)
  evaluation/diff.py              # Candidate-to-gold comparison engine
  evaluation/metrics.py           # Precision / recall / F1 calculation
  extractor/backends.py           # LLM backend interface (Gemini, OpenAI, Mock)
  extractor/run_extraction.py     # Extraction orchestration and response caching
tests/                            # Pytest unit tests (18 tests)
```

## Current Limitations

- **Scope**: Restricted to §3.1.10–§3.1.12. Covering the full ISA manual would require text pre-chunking.
- **Name normalization**: Handles capitalization and symbols (e.g. `HPM_COUNTER_EN` vs `hpm_counter_en`), but semantic synonyms (e.g. `HPM_COUNT`) are not mapped and score as misses.
- **Context capacity**: Single-context prompting works at this excerpt size. Longer chapters would exceed practical context limits.

## Future Extensions

- **JSON schema constraints**: Enforce output structure at the LLM API layer (via Gemini `response_schema`) to eliminate category enum violations.
- **Synonyms dictionary**: Derive a synonym alias map from UDB parameter description files and integrate it into the matching engine.
- **Dynamic few-shot retrieval**: Retrieve positive/negative examples from other spec chapters based on section content similarity.

---

## Acknowledgements

- Specification text sourced from the [RISC-V ISA Manual](https://github.com/riscv/riscv-isa-manual) (Privileged ISA, §3.1.10–§3.1.12).
- Gold reference parameters traced to [riscv-unified-db](https://github.com/riscv-software-src/riscv-unified-db) at commit `e195c8b2ca0c3e152ac0214e940f1aed3c4f6876`.

## License

Licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.
