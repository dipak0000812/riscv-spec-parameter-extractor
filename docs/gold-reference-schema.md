# Gold-Reference Schema Specification

This document defines and freezes the schema used for the gold-reference dataset in `data/gold_reference.yaml`. 

Every entry in the gold-reference file must validate against this schema.

## Schema Fields

| Field | Type | Required | Allowed Values / Pattern | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `string` or `null` | Yes | `^[A-Z0-9_]+$` or `null` | The canonical parameter identifier derived from the corresponding UDB filename (without the `.yaml` suffix). If the parameter is unnamed in the spec text, this field is `null`. |
| `category` | `string` | Yes | `named`, `unnamed`, `config-dependent` | The classification category from UDB / Part I instructions. |
| `udb_file` | `string` | Yes | `spec/std/isa/param/.*\.yaml` | Relpath of the parameter file in the `riscv/riscv-unified-db` repository. |
| `section` | `string` | Yes | `^\d+(\.\d+)*$` | Section identifier from the spec excerpt where the parameter is defined (e.g., `"3.1.10"`). |
| `canonical_anchor` | `string` | Yes | `^norm:[a-z0-9_]+$` | The exact anchor ID preceding the defining statement in `machine_counters.md`. |
| `canonical_citation` | `string` | Yes | Verbatim string | One or more contiguous sentences copied verbatim from the specification, beginning at the line of the `canonical_anchor`. |
| `secondary_anchors` | `list[string]` | Yes | List of `^norm:[a-z0-9_]+$` | Other anchors in the spec excerpt where this parameter is referenced or modified. |
| `related_parameters` | `list[string]` | Yes | List of uppercase snake_case | Other parameters that have direct architectural or logical relationships with this parameter. |
| `mapping_type` | `string` | Yes | `simple`, `unnamed`, `one-to-many`, `many-to-one` | Classification of the spec-to-UDB mapping structure (resolves edge cases). |
| `classification_rationale` | `string` | Yes | Plain text statement | The evidence-based justification for assigning this specific category, citing CSR rules or description properties. |

---

## Schema Rules & Validation Logic

### 1. Name and Category Constraint
- If `name` is `null`, `category` must be `unnamed`.
- If `category` is `unnamed`, `name` must be `null`.
- If `name` is a string (e.g. `HPM_COUNTER_EN`), `category` must be `named` or `config-dependent`.

### 2. Traceability Requirements
- The `udb_file` must exist as a real path in the `riscv-unified-db` parameter file tree.
- The `canonical_anchor` and `canonical_citation` must exist in the spec excerpt file.
- `canonical_citation` must match the line(s) following `canonical_anchor` in the Markdown file exactly.

### 3. Mapping Type Definitions
- `simple`: One clear spec sentence maps directly to one named parameter in UDB.
- `unnamed`: The parameter exists architecture-wise but has no fixed name in the spec text.
- `one-to-many`: A single parameter maps to multiple separate citations or segments in the spec text.
- `many-to-one`: A single spec sentence or block (like a register description) defines multiple related parameters simultaneously.

### 4. Ordering Requirement
- All entries in `data/gold_reference.yaml` must be sorted alphabetically by `name`.
- Unnamed entries (where `name` is `null`) must appear last.
