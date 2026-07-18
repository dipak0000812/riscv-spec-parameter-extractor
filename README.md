# RISC-V Spec-to-Parameters Extractor with Evaluation Harness

A framework for extracting implementation-configurable parameters from the RISC-V ISA spec prose using LLMs, with automated precision/recall evaluation against a Unified Database (UDB) derived gold reference.

## Repository Layout
- `data/`: Specification excerpts and structured gold references.
- `docs/`: Design documents, schemas, and classification methodology.
- `src/`: Package code (extractors, caches, metrics, diff algorithms).
- `tests/`: Automated validation and pipeline unit tests.

## Scoping
This project targets the **Machine-Level Performance Counters & HPM (§3.1.10–§3.1.12)** section of the RISC-V Privileged ISA Manual.

## License
Licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.
