# RISC-V Spec-to-Parameters Extractor with Evaluation Harness

A framework for extracting implementation-configurable parameters from the RISC-V ISA spec prose using LLMs, with automated precision/recall evaluation against a Unified Database (UDB) derived gold reference.

This project targets the **Machine-Level Performance Counters & HPM (§3.1.10–§3.1.12)** section of the RISC-V Privileged ISA Manual.

## Motivation
Architectural specifications for processors (such as the RISC-V ISA manuals) describe many parameters and configuration options that vary between implementations (e.g. counter presence, optional CSRs, and platform limits). Extracting these parameters manually to populate hardware verification databases or Unified Databases (UDB) is tedious and error-prone. This project builds a reliable LLM-based extraction pipeline paired with a deterministic evaluation harness to measure the precision and recall of automated parameter extraction against a verified gold reference.

## Repository Scope
The current scope of this repository is strictly focused on **Machine-Level Performance Counters & HPM (§3.1.10–§3.1.12)** of the RISC-V Privileged ISA Manual. This section defines performance-monitoring counter registers, event selectors, and availability control behaviors. Extraction and evaluation target the 8 canonical parameters defined within this specification range and traced to their source in the RISC-V Unified Database.

## Repository Structure
* `data/` — Target specification excerpts and UDB-aligned gold reference parameters.
* `docs/` — Schemas, methodology definitions, and engineering decisions.
* `prompts/` — System prompts and few-shot templates.
* `src/` — CLI entrypoint, LLM backends, comparison engines, and metrics.
* `tests/` — Automated test suite verifying schema constraints, diffs, and caching.

## Installation
Ensure you have Python 3.11+ and a virtual environment activated:
```bash
# Install core package with dev dependencies
pip install -e .[dev]

# Optional: Install Gemini extras
pip install -e .[gemini]

# Optional: Install OpenAI extras
pip install -e .[openai]
```

## Quickstart
Verify the repository installation by running the automated unit test suite:
```bash
python -m pytest -v
```

## Offline Reproduction
To execute the end-to-end extraction and evaluation pipeline completely offline (no API keys required), run:
```bash
python -m src.cli run --backend mock
```
This command runs parameter extraction using the offline mock backend, writes candidates to `results/example_candidates.yaml`, and generates the detailed metrics report at `results/evaluation.md`.

## Running with Gemini
Ensure the `GEMINI_API_KEY` environment variable is set:
```bash
python -m src.cli run --backend gemini --model gemini-2.5-flash
```

## Running with OpenAI
Ensure the `OPENAI_API_KEY` environment variable is set:
```bash
python -m src.cli run --backend openai --model gpt-4o-mini
```

## Running Evaluation
If you already have an extracted candidates YAML file, you can evaluate it separately:
```bash
python -m src.cli evaluate --candidates results/example_candidates.yaml --gold data/gold_reference.yaml --output results/evaluation.md
```

## Repository Layout
- `data/spec_excerpts/machine_counters.md` — Target specification excerpt (§3.1.10–§3.1.12).
- `data/gold_reference.yaml` — Curated gold reference list.
- `docs/gold-reference-schema.md` — Specifications for the gold YAML structure.
- `docs/gold-reference.md` — Methodology for curation of the gold reference.
- `docs/methodology.md` — Category definitions and worked examples.
- `docs/engineering-decisions.md` — Design decisions and architectural rationales.
- `prompts/current.md` — The active prompt template.
- `src/cli.py` — Click-based command interface.

## Current Limitations
- **Manual Scope**: Currently restricted to §3.1.10–§3.1.12 (Machine-Level Performance Counters).
- **Exact Name Normalization**: Normalization handles capitalization and symbols (spaces/underscores/dashes), but semantic synonyms (e.g. `HPM_COUNT` instead of `HPM_COUNTER_EN`) are not dynamically mapped.
- **Context Capacity**: Evaluating long specification books requires text pre-chunking.

## Future Extensions
- **API Schema Constraints**: Enforce JSON output schema constraints at the LLM API layer (via Gemini configurations).
- **Synonyms Dictionary**: Incorporate a synonym alias mapping in the evaluation diff engine.
- **Dynamic Few-Shot RAG**: Retrieve positive and negative examples dynamically based on section content similarity.

---

## License
Licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.
