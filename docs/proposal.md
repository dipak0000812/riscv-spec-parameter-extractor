# RISC-V Spec-to-Parameters Extractor with Evaluation Harness

## Project Proposal & Design Specification

### 1. Objective
Design and implement a local, offline evaluation harness that utilizes Large Language Models (LLMs) to automatically extract implementation-defined architectural parameters from RISC-V specification text. The system compares the model's candidates against a manually curated, schema-conforming gold-reference dataset to calculate precision, recall, and F1 scores.

### 2. Scope
This evaluation is scoped to **Machine-Level Performance Counters & HPM (§3.1.10–§3.1.12)** from the RISC-V Privileged ISA specification. This includes parameters governing:
- Hardware Performance Monitor counter enables (`HPM_COUNTER_EN`)
- Event selectors (`HPM_EVENTS`)
- Counter inhibition controls (`COUNTINHIBIT_EN`, `MCOUNTINHIBIT_IMPLEMENTED`)
- Next-privilege counter availability (`MCOUNTENABLE_EN`, `SCOUNTENABLE_EN`, `HCOUNTENABLE_EN`)
- Shadow mapping availability (`TIME_CSR_IMPLEMENTED`)

### 3. Key Architecture Components
- **Spec Excerpt Corpus**: Plain text Markdown extracts with addressable anchor tags representing paragraph-level segments.
- **Gold-Reference Database**: A structured database representing the definitive mappings derived from the official `riscv-unified-db` repository.
- **Extractor Engine**: A pluggable, cached LLM connector wrapper supporting Gemini and OpenAI APIs.
- **Evaluation Engine**: Pure mathematical comparison logic mapping candidates to gold entries using case-insensitive normalization and semantic prefix-overlap checks.
- **CLI Wrapper**: A unified execution tool built on Click to run extraction and evaluation.
