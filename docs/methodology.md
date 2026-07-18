# Parameter Classification Methodology

This document explains the parameter categories used in this repository, citing terminology from the RISC-V Unified Database (UDB).

## Category Definitions

We classify each architectural parameter into one of three categories:

### 1. Named Parameters
- **Definition:** The parameter corresponds to a specific, implementation-configurable register, bitfield, or structure that has a distinct, defined name in the RISC-V specification prose or is named directly in UDB schemas.
- **Worked Example:** `HPM_COUNTER_EN`
  - *Spec Prose:* "The hardware performance monitor includes 29 additional 64-bit event counters..."
  - *UDB Parameter:* `HPM_COUNTER_EN.yaml`
  - *Rationale:* It represents a specific, named architectural structure (HPM counters) whose implementation size is defined.

### 2. Configuration-Dependent Parameters
- **Definition:** An implementation parameter whose existence, size, or valid range depends on the value of another parameter or on the presence of specific extensions.
- **Worked Example:** `MCOUNTINHIBIT_IMPLEMENTED`
  - *Spec Prose:* "If the csr:mcountinhibit[] register is not implemented, the implementation behaves as though..."
  - *UDB Parameter:* `MCOUNTINHIBIT_IMPLEMENTED.yaml`
  - *Rationale:* The parameter is a boolean reflecting whether the `mcountinhibit` CSR structure itself is implemented (which is configuration-dependent).

### 3. Unnamed Parameters
- **Definition:** The parameter represents a configuration option or behavior described in the specification prose, but lacks a canonical, capitalized name in the spec text.
- **Worked Example:**
  - *Note on this Chapter:* The Machine-Level Counters & HPM chapter contains no unnamed parameters. Every parameter in this evaluation corpus maps directly to a named register or implementation status register in the UDB.
  - *Generic Definition:* A parameter representing an implementation-defined behavior (e.g. an instruction execution timing boundary or an exception prioritization choice) that has no explicit register or register-field name associated with it in the manual text. This category is preserved for compatibility with future spec chapters.

---

## Known Limitations

1. **Chapter Scope Limitation:** This gold-reference list is currently scoped only to §3.1.10–§3.1.12. General parameters (like XLEN) are excluded to prevent evaluation drift.
2. **Text Anchor Sensitivity:** Matching logic relies on exact anchor locations. A minor change in paragraph order or anchor syntax in future specs would require updating anchor tags in the spec corpus to preserve matching scores.
