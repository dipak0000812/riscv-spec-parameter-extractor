# Gold-Reference Construction Methodology

This document explains the construction methodology, inclusion/exclusion rules, ambiguous decisions, and verification steps taken to establish `data/gold_reference.yaml`.

---

## 1. Selection Process & Rationale

The primary chapter selected for evaluation is **Machine-Level Performance Counters & HPM (§3.1.10–§3.1.12)** from the RISC-V Privileged ISA Manual.

### Rationale:
- This is a bounded, self-contained section of the spec that defines a clear set of architecture features (mcycle, minstret, mhpmcounter, mhpmevent, mcounteren, mcountinhibit).
- It provides a mix of parameter categories (e.g., named lists like `HPM_COUNTER_EN`, and configuration flags like `MCOUNTINHIBIT_IMPLEMENTED`).
- It has corresponding parameter definitions in the `riscv/riscv-unified-db` repository.

---

## 2. Sources Consulted
The parameters were cross-referenced with the official files in the
[riscv-unified-db](https://github.com/riscv-software-src/riscv-unified-db) repository
at commit `e195c8b2ca0c3e152ac0214e940f1aed3c4f6876`. The specific UDB files mapped are:
- `spec/std/isa/param/COUNTINHIBIT_EN.yaml`
- `spec/std/isa/param/HCOUNTENABLE_EN.yaml`
- `spec/std/isa/param/HPM_COUNTER_EN.yaml`
- `spec/std/isa/param/HPM_EVENTS.yaml`
- `spec/std/isa/param/MCOUNTENABLE_EN.yaml`
- `spec/std/isa/param/MCOUNTINHIBIT_IMPLEMENTED.yaml`
- `spec/std/isa/param/SCOUNTENABLE_EN.yaml`
- `spec/std/isa/param/TIME_CSR_IMPLEMENTED.yaml`

---

## 3. Inclusion & Exclusion Criteria

### Inclusion Criteria:
A parameter is included in the gold list if and only if:
1. It has a corresponding validated parameter file under `spec/std/isa/param/` in the UDB.
2. Its defining text or active CSR behavior is mentioned within the spec excerpt §3.1.10–§3.1.12.
3. It fits one of the three category types: `named`, `unnamed`, or `config-dependent`.

### Exclusion Criteria:
The following are excluded:
1. Non-parameter objects in the UDB (such as standard CSR layout fields, instruction encodings, or extension names).
2. General parameters (like `XLEN` or `PHYS_ADDR_WIDTH`) that are defined in other sections of the manual and only referenced here in passing.
3. Parameters that are present in UDB but have no matching definition or reference inside our specific §3.1.10–§3.1.12 text excerpt.

---

## 4. Ambiguous Cases and Resolutions

### Case 1: `SCOUNTENABLE_EN` and `HCOUNTENABLE_EN`
- **Ambiguity:** The spec excerpt describes `mcounteren` in §3.1.11, but only hints at `scounteren` and `hcounteren` when defining how the next privilege levels are permitted or not prevented (e.g. "...not otherwise prevented by the csr::[tm] bit in csr:hcounteren[]").
- **Resolution:** Included both parameters since their behavior and architectural existences are dictated by the rules described in §3.1.11. The canonical anchors point to the specific sentences where S-mode and VS-mode transitions are defined.

### Case 2: `TIME_CSR_IMPLEMENTED`
- **Ambiguity:** `time` is a read-only shadow of `mtime` (which is memory-mapped). The parameter `TIME_CSR_IMPLEMENTED` indicates whether the `time` CSR is implemented. The text describes this shadow register behavior in §3.1.11.
- **Resolution:** Included in the gold list under the `config-dependent` category because the spec states it can be emulated or shadow-mapped depending on whether harts support it.

---

## 5. Verification & Validation Steps
1. **Re-derivation Check:** Traced each of the 8 parameters backward from the UDB files to the spec text to ensure the listed anchors match the exact lines.
2. **Deterministic Check:** Verified that all entries are ordered alphabetically.
3. **Traceability Spot-check:** Checked that every `canonical_citation` matches the text in `data/spec_excerpts/machine_counters.md` character-for-character.
