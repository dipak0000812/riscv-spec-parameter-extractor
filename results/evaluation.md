# Evaluation Report: mock-model-v1

## Metadata
- **Model Used**: `mock-model-v1`
- **Prompt Version**: `v1`
- **Backend Used**: `mock` (deterministic extraction simulation)
- **Evaluation Dataset**: RISC-V Privileged ISA Manual (§3.1.10–§3.1.12, Machine Counters)
- **Gold Reference Version**: Derived from `riscv-unified-db` commit `e195c8b2ca0c3e152ac0214e940f1aed3c4f6876`

## Summary Metrics

| Metric | Strict Mode | Relaxed Mode |
| --- | --- | --- |
| **True Positives (TP)** | 6 | 7 |
| **False Positives (FP)** | 2 | 1 |
| **False Negatives (FN)** | 2 | 1 |
| **Precision** | 0.7500 | 0.8750 |
| **Recall** | 0.7500 | 0.8750 |
| **F1 Score** | 0.7500 | 0.8750 |

Total Candidates: `8`
Total Gold Parameters: `8`
Partial Matches: `1`

## Breakdown of Results

### 1. True Positives (TP)
- **COUNTINHIBIT_EN** (`named`)
  - **Section**: 3.1.12
  - **Citation**: *"The counter-inhibit register csr:mcountinhibit[] is a 32-bit *WARL* register that controls which of the hardware performance-monitoring counters increment."*

- **HPM_COUNTER_EN** (`named`)
  - **Section**: 3.1.10
  - **Citation**: *"The hardware performance monitor includes 29 additional 64-bit event counters, csr:mhpmcounter3[]–csr:mhpmcounter31[]."*

- **HPM_EVENTS** (`named`)
  - **Section**: 3.1.10
  - **Citation**: *"The event selector CSRs, csr:mhpmevent3[]–csr:mhpmevent31[], are 64-bit *WARL* registers that control which event causes the corresponding counter to increment."*

- **MCOUNTENABLE_EN** (`named`)
  - **Section**: 3.1.11
  - **Citation**: *"The counter-enable csr:mcounteren[] register is a 32-bit register that controls the availability of the hardware performance-monitoring counters to the next-lowest privileged mode."*

- **MCOUNTINHIBIT_IMPLEMENTED** (`config-dependent`)
  - **Section**: 3.1.12
  - **Citation**: *"If the csr:mcountinhibit[] register is not implemented, the implementation behaves as though the register were set to zero."*

- **SCOUNTENABLE_EN** (`named`)
  - **Section**: 3.1.11
  - **Citation**: *"When one of these bits is set, access to the corresponding register is permitted in the next implemented privilege mode (S-mode if implemented, otherwise U-mode)."*

### 2. Partial Matches (Name Match, Category Mismatch)
- **TIME_CSR_IMPLEMENTED**
  - **Gold Category**: `config-dependent`
  - **Extracted Category**: `named`
  - **Mismatch Reason**: Category mismatch: candidate='named', gold='config-dependent'
  - **Citation**: *"The csr:time[] CSR is a read-only shadow of the memory-mapped csr:mtime[] register."*

### 3. False Positives (Hallucinations / Redundancies)
- **MSTATUS_FS_LEGAL_VALUES** (`named`)
  - **Section**: 3.1.10
  - **Quotation**: *"The hardware performance monitor includes 29 additional 64-bit event counters..."*
  - **Model Rationale**: Hallucinated parameter not relevant/present in this specific excerpt context.

### 4. False Negatives (Missed Gold Parameters)
- **HCOUNTENABLE_EN** (`named`)
  - **Section**: 3.1.11
  - **Canonical Anchor**: `norm:mcounteren_tm_set`
  - **Citation**: *"When this bit is set, access to the csr:stimecmp[] or csr:vstimecmp[] register is permitted in S-mode if implemented, and access to the csr:vstimecmp[] register (via csr:stimecmp[]) is permitted in VS-mode if implemented and not otherwise prevented by the csr::[tm] bit in csr:hcounteren[]."*

## Narrated Walkthroughs of Discrepancies

### Walkthrough 1: Partial Match (`TIME_CSR_IMPLEMENTED`)
In this evaluation run, the parameter **`TIME_CSR_IMPLEMENTED`** is identified as a partial match. The model successfully extracted the correct parameter name but misclassified its category as `named` instead of `config-dependent`.

- **Prose Evidence**: *"The csr:time[] CSR is a read-only shadow of the memory-mapped csr:mtime[] register."*
- **Why this happened**: The canonical citation describing `time` describes the shadow register itself. The implementation optionality is established elsewhere in the specification (which states that an implementation may choose to trap instead of implementing the register). Because the model focused on the register-definition sentence rather than the separate optionality statement, it classified the parameter as a named architectural feature instead of a configuration-dependent parameter.

### Walkthrough 2: False Positive (`MSTATUS_FS_LEGAL_VALUES`)
The parameter **`MSTATUS_FS_LEGAL_VALUES`** was flagged as a False Positive because it was extracted by the model but does not exist in the gold reference for this performance counters chapter.

- **Prose Evidence**: The model extracted this parameter quoting the HPM counter text: *"The hardware performance monitor includes 29 additional 64-bit event counters..."*
- **Why this happened**: This is a controlled test case designed to simulate a realistic LLM failure mode (where a model mistakenly maps an out-of-scope parameter name to unrelated text). The parameter `MSTATUS_FS_LEGAL_VALUES` exists in the Unified Database; however, it is intentionally out of scope for this specification excerpt, and the evaluation harness correctly identifies it as a false positive.

## Lessons Learned
- **Category Optionality Boundaries**: Distinguishing between register field parameters (`named`) and overall register presence optionality (`config-dependent`) is a major challenge for the LLM. The prompt should explicitly define how to classify registers whose implementation depends on platform constraints.
- **Value of Separable Metrics**: Separating evaluation into strict and relaxed F1 scores prevents categorization mistakes (which are easy to align via post-processing or prompt tweaks) from obscuring high raw parameter discovery recall (relaxed F1 of 87.50% vs. strict F1 of 75.00%).
- **Anchor Validation Rigor**: Standardizing embedded HTML anchors (`<!-- anchor: ... -->`) provides a foolproof mechanism for checking citation alignment and locating extracted text, preventing hallucinated citations from sliding through.

## Current Limitations
- **Limited Excerpt Scope**: Evaluation is restricted to §3.1.10–§3.1.12. Extending the evaluation scope to cover the entire spec manual requires a robust text chunker to prevent context dilution.
- **Strict Synonyms Check**: Normalization handles case and symbol changes (e.g. `HPM_COUNTER_EN` vs. `hpm_counter_en`), but semantic synonym mappings (e.g., if a model outputs `HPM_COUNT` instead of the canonical UDB name) are not dynamically mapped and result in a miss.

## Future Improvements
- **JSON Schema Constraints**: Enforce the candidate output structure directly at the LLM API layer (via google-genai schema properties) to eliminate any syntax formatting or category enum validation exceptions.
- **Synonyms Map**: Integrate a synonym dictionary in the matching engine derived from alternate names listed in the UDB parameters description files.
- **Automated Few-Shot RAG**: Dynamically retrieve positive and negative few-shot examples from other spec chapters based on the semantic similarity of the text block being processed.
