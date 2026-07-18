"""CLI entrypoint for the RISC-V parameter extractor.

Orchestration only. Business logic lives in extractor/ and evaluation/.
"""

import sys
from pathlib import Path
import re
import click
import yaml

# List of 228 verified parameters from riscv-unified-db repo.
# Used for programmatic validation of UDB path and related parameter existence.
VERIFIED_UDB_PARAMS = {
    "ARCH_ID_VALUE", "ASID_WIDTH", "CACHE_BLOCK_SIZE", "CONFIG_PTR_ADDRESS", "COUNTINHIBIT_EN",
    "DBG_HCONTEXT_WIDTH", "DBG_SCONTEXT_WIDTH", "DCSR_MPRVEN_TYPE", "DCSR_STEPIE_TYPE",
    "DCSR_STOPCOUNT_TYPE", "DCSR_STOPTIME_TYPE", "ELEN", "FOLLOW_VTYPE_RESET_RECOMMENDATION",
    "FORCE_UPGRADE_CBO_INVAL_TO_FLUSH", "GSTAGE_MODE_BARE", "HCONTEXT_AVAILABLE",
    "HCOUNTENABLE_EN", "HPM_COUNTER_EN", "HPM_EVENTS", "HSTATEEN_AIA_TYPE",
    "HSTATEEN_CONTEXT_TYPE", "HSTATEEN_CSRIND_TYPE", "HSTATEEN_ENVCFG_TYPE",
    "HSTATEEN_IMSIC_TYPE", "HSTATEEN_JVT_TYPE", "HW_MSTATUS_FS_DIRTY_UPDATE",
    "HW_MSTATUS_VS_DIRTY_UPDATE", "IGNORE_INVALID_VSATP_MODE_WRITES_WHEN_V_EQ_ZERO",
    "IMPRECISE_VECTOR_TRAP_SETTABLE", "IMP_ID_VALUE", "JVT_BASE_MASK", "JVT_BASE_TYPE",
    "JVT_READ_ONLY", "LEGAL_VSTART", "LRSC_FAIL_ON_NON_EXACT_LRSC", "LRSC_FAIL_ON_VA_SYNONYM",
    "LRSC_MISALIGNED_BEHAVIOR", "LRSC_RESERVATION_STRATEGY", "MARCHID_IMPLEMENTED",
    "MCID_WIDTH", "MCONTEXT_AVAILABLE", "MCOUNTENABLE_EN", "MCOUNTINHIBIT_IMPLEMENTED",
    "MCTRCTL_CORSWAPINH_IMPLEMENTED", "MCTRCTL_CUSTOM_IMPLEMENTED", "MCTRCTL_DIRCALLINH_IMPLEMENTED",
    "MCTRCTL_DIRJMPINH_IMPLEMENTED", "MCTRCTL_DIRLJMPINH_IMPLEMENTED", "MCTRCTL_EXCINH_IMPLEMENTED",
    "MCTRCTL_INDCALLINH_IMPLEMENTED", "MCTRCTL_INDJMPINH_IMPLEMENTED", "MCTRCTL_INDLJMPINH_IMPLEMENTED",
    "MCTRCTL_INTRINH_IMPLEMENTED", "MCTRCTL_MTE_IMPLEMENTED", "MCTRCTL_NTBREN_IMPLEMENTED",
    "MCTRCTL_RASEMU_IMPLEMENTED", "MCTRCTL_RETINH_IMPLEMENTED", "MCTRCTL_STE_IMPLEMENTED",
    "MCTRCTL_TKBRINH_IMPLEMENTED", "MCTRCTL_TRETINH_IMPLEMENTED", "MIMPID_IMPLEMENTED",
    "MISALIGNED_AMO", "MISALIGNED_LDST", "MISALIGNED_LDST_EXCEPTION_PRIORITY",
    "MISALIGNED_MAX_ATOMICITY_GRANULE_SIZE", "MISALIGNED_SPLIT_STRATEGY", "MISA_CSR_IMPLEMENTED",
    "MSTATEEN_AIA_TYPE", "MSTATEEN_CONTEXT_TYPE", "MSTATEEN_CSRIND_TYPE",
    "MSTATEEN_ENVCFG_TYPE", "MSTATEEN_IMSIC_TYPE", "MSTATEEN_JVT_TYPE", "MSTATUS_FS_LEGAL_VALUES",
    "MSTATUS_VS_LEGAL_VALUES", "MTVAL_WIDTH", "MTVEC_ACCESS", "MTVEC_BASE_ALIGNMENT_DIRECT",
    "MTVEC_BASE_ALIGNMENT_VECTORED", "MTVEC_ILLEGAL_WRITE_BEHAVIOR", "MTVEC_MODES",
    "MUTABLE_MISA_A", "MUTABLE_MISA_B", "MUTABLE_MISA_C", "MUTABLE_MISA_D", "MUTABLE_MISA_F",
    "MUTABLE_MISA_H", "MUTABLE_MISA_M", "MUTABLE_MISA_Q", "MUTABLE_MISA_S", "MUTABLE_MISA_U",
    "MUTABLE_MISA_V", "MXLEN", "M_MODE_ENDIANNESS", "NUM_EXTERNAL_GUEST_INTERRUPTS",
    "NUM_PMP_ENTRIES", "NUM_USABLE_PMP_ENTRIES", "PHYS_ADDR_WIDTH", "PMA_GRANULARITY",
    "PMLEN", "PMP_GRANULARITY", "PMP_NA4_SUPPORTED", "PMP_NAPOT_SUPPORTED", "PMP_TOR_SUPPORTED",
    "PRECISE_SYNCHRONOUS_EXCEPTIONS", "RCID_WIDTH", "REPORT_CAUSE_IN_MTVAL_ON_LANDING_PAD_SOFTWARE_CHECK",
    "REPORT_CAUSE_IN_MTVAL_ON_SHADOW_STACK_SOFTWARE_CHECK", "REPORT_CAUSE_IN_STVAL_ON_LANDING_PAD_SOFTWARE_CHECK",
    "REPORT_CAUSE_IN_STVAL_ON_SHADOW_STACK_SOFTWARE_CHECK", "REPORT_CAUSE_IN_VSTVAL_ON_LANDING_PAD_SOFTWARE_CHECK",
    "REPORT_CAUSE_IN_VSTVAL_ON_SHADOW_STACK_SOFTWARE_CHECK", "REPORT_ENCODING_IN_MTVAL_ON_ILLEGAL_INSTRUCTION",
    "REPORT_ENCODING_IN_STVAL_ON_ILLEGAL_INSTRUCTION", "REPORT_ENCODING_IN_VSTVAL_ON_ILLEGAL_INSTRUCTION",
    "REPORT_ENCODING_IN_VSTVAL_ON_VIRTUAL_INSTRUCTION", "REPORT_GPA_IN_HTVAL_ON_GUEST_PAGE_FAULT",
    "REPORT_GPA_IN_TVAL_ON_INSTRUCTION_GUEST_PAGE_FAULT", "REPORT_GPA_IN_TVAL_ON_INTERMEDIATE_GUEST_PAGE_FAULT",
    "REPORT_GPA_IN_TVAL_ON_LOAD_GUEST_PAGE_FAULT", "REPORT_GPA_IN_TVAL_ON_STORE_AMO_GUEST_PAGE_FAULT",
    "REPORT_VA_IN_MTVAL_ON_BREAKPOINT", "REPORT_VA_IN_MTVAL_ON_INSTRUCTION_ACCESS_FAULT",
    "REPORT_VA_IN_MTVAL_ON_INSTRUCTION_MISALIGNED", "REPORT_VA_IN_MTVAL_ON_INSTRUCTION_PAGE_FAULT",
    "REPORT_VA_IN_MTVAL_ON_LOAD_ACCESS_FAULT", "REPORT_VA_IN_MTVAL_ON_LOAD_MISALIGNED",
    "REPORT_VA_IN_MTVAL_ON_LOAD_PAGE_FAULT", "REPORT_VA_IN_MTVAL_ON_STORE_AMO_ACCESS_FAULT",
    "REPORT_VA_IN_MTVAL_ON_STORE_AMO_MISALIGNED", "REPORT_VA_IN_MTVAL_ON_STORE_AMO_PAGE_FAULT",
    "REPORT_VA_IN_STVAL_ON_BREAKPOINT", "REPORT_VA_IN_STVAL_ON_INSTRUCTION_ACCESS_FAULT",
    "REPORT_VA_IN_STVAL_ON_INSTRUCTION_MISALIGNED", "REPORT_VA_IN_STVAL_ON_INSTRUCTION_PAGE_FAULT",
    "REPORT_VA_IN_STVAL_ON_LOAD_ACCESS_FAULT", "REPORT_VA_IN_STVAL_ON_LOAD_MISALIGNED",
    "REPORT_VA_IN_STVAL_ON_LOAD_PAGE_FAULT", "REPORT_VA_IN_STVAL_ON_STORE_AMO_ACCESS_FAULT",
    "REPORT_VA_IN_STVAL_ON_STORE_AMO_MISALIGNED", "REPORT_VA_IN_STVAL_ON_STORE_AMO_PAGE_FAULT",
    "REPORT_VA_IN_VSTVAL_ON_BREAKPOINT", "REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_ACCESS_FAULT",
    "REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_MISALIGNED", "REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_PAGE_FAULT",
    "REPORT_VA_IN_VSTVAL_ON_LOAD_ACCESS_FAULT", "REPORT_VA_IN_VSTVAL_ON_LOAD_MISALIGNED",
    "REPORT_VA_IN_VSTVAL_ON_LOAD_PAGE_FAULT", "REPORT_VA_IN_VSTVAL_ON_STORE_AMO_ACCESS_FAULT",
    "REPORT_VA_IN_VSTVAL_ON_STORE_AMO_MISALIGNED", "REPORT_VA_IN_VSTVAL_ON_STORE_AMO_PAGE_FAULT",
    "RESERVED_VSET_X0X0_VILL_SET", "RESERVED_VSET_X0X0_VLMAX_CHANGE", "RVV_VL_WHEN_AVL_LT_DOUBLE_VLMAX",
    "SATP_MODE_BARE", "SCOUNTENABLE_EN", "SEW_MIN", "SSTATEEN_JVT_TYPE", "STVAL_WIDTH",
    "STVEC_MODE_DIRECT", "STVEC_MODE_VECTORED", "SUPPORT_FRACTIONAL_LMUL_BEYOND_REQUIRED",
    "SV32X4_TRANSLATION", "SV32_VSMODE_TRANSLATION", "SV39X4_TRANSLATION", "SV39_VSMODE_TRANSLATION",
    "SV48X4_TRANSLATION", "SV48_VSMODE_TRANSLATION", "SV57X4_TRANSLATION", "SV57_VSMODE_TRANSLATION",
    "SXLEN", "S_MODE_ENDIANNESS", "TIME_CSR_IMPLEMENTED", "TINST_VALUE_ON_BREAKPOINT",
    "TINST_VALUE_ON_FINAL_INSTRUCTION_GUEST_PAGE_FAULT", "TINST_VALUE_ON_FINAL_LOAD_GUEST_PAGE_FAULT",
    "TINST_VALUE_ON_FINAL_STORE_AMO_GUEST_PAGE_FAULT", "TINST_VALUE_ON_INSTRUCTION_ADDRESS_MISALIGNED",
    "TINST_VALUE_ON_LOAD_ACCESS_FAULT", "TINST_VALUE_ON_LOAD_ADDRESS_MISALIGNED",
    "TINST_VALUE_ON_LOAD_PAGE_FAULT", "TINST_VALUE_ON_MCALL", "TINST_VALUE_ON_SCALL",
    "TINST_VALUE_ON_STORE_AMO_ACCESS_FAULT", "TINST_VALUE_ON_STORE_AMO_ADDRESS_MISALIGNED",
    "TINST_VALUE_ON_STORE_AMO_PAGE_FAULT", "TINST_VALUE_ON_UCALL", "TINST_VALUE_ON_VIRTUAL_INSTRUCTION",
    "TINST_VALUE_ON_VSCALL", "TRAP_ON_EBREAK", "TRAP_ON_ECALL_FROM_M", "TRAP_ON_ECALL_FROM_S",
    "TRAP_ON_ECALL_FROM_U", "TRAP_ON_ECALL_FROM_VS", "TRAP_ON_ILLEGAL_WLRL", "TRAP_ON_RESERVED_INSTRUCTION",
    "TRAP_ON_SFENCE_VMA_WHEN_SATP_MODE_IS_READ_ONLY", "TRAP_ON_UNIMPLEMENTED_CSR",
    "TRAP_ON_UNIMPLEMENTED_INSTRUCTION", "UXLEN", "U_MODE_ENDIANNESS", "VECTOR_FF_NO_EXCEPTION_TRIM",
    "VECTOR_FF_SEG_EXCEPTION_PARTIAL_LOAD", "VECTOR_FF_UPDATE_PAST_TRIM", "VECTOR_LOAD_PAST_TRAP",
    "VECTOR_LOAD_SEG_FF_OVERWRITE_ELEMENTS_AFTER_FAULT", "VECTOR_LS_INDEX_MAX_EEW",
    "VECTOR_LS_MISALIGNED_LEGAL", "VECTOR_LS_SEG_PARTIAL_ACCESS", "VECTOR_LS_WHOLEREG_MISALIGNED_LEGAL",
    "VENDOR_ID_BANK", "VENDOR_ID_OFFSET", "VFREDUSUM_FINAL_NODE_ELEMENT_BEHAVIOR",
    "VFREDUSUM_INACTIVE_NODE_ELEMENT_BEHAVIOR", "VFREDUSUM_NAN", "VFREDUSUM_NODE_ROUNDING_BEHAVIOR",
    "VILL_SET_ON_RESERVED_VTYPE", "VLEN", "VMID_WIDTH", "VSSTAGE_MODE_BARE", "VSSTATUS_VS_EXISTS",
    "VSTVEC_MODE_DIRECT", "VSTVEC_MODE_VECTORED", "VSXLEN", "VS_MODE_ENDIANNESS", "VUXLEN",
    "VU_MODE_ENDIANNESS", "ZAWRS_NTO_IS_NOP"
}


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML safe loader that strictly forbids duplicate keys in mappings."""

    def construct_mapping(self, node, deep=False):
        mapping = []
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    f"Duplicate key '{key}' found in YAML mapping"
                )
            mapping.append(key)
        return super().construct_mapping(node, deep=deep)


def validate_gold_file(gold_path: Path, spec_path: Path) -> list[str]:
    """Validate the gold reference file structure and contents.

    Returns a list of error strings. If empty, validation passed.
    """
    errors = []
    if not gold_path.is_file():
        return [f"Gold file not found at: {gold_path}"]
    if not spec_path.is_file():
        return [f"Spec excerpt file not found at: {spec_path}"]

    try:
        # Load using custom UniqueKeyLoader to reject duplicate keys
        with open(gold_path, "r", encoding="utf-8") as f:
            entries = yaml.load(f, Loader=UniqueKeyLoader)
    except Exception as e:
        return [f"Failed to parse YAML (checking for duplicate keys): {e}"]

    if not isinstance(entries, list):
        return ["Gold reference must be a YAML list of entries."]

    name_pattern = re.compile(r"^[A-Z0-9_]+$")
    anchor_pattern = re.compile(r"^norm:[a-z0-9_]+$")
    section_pattern = re.compile(r"^\d+(\.\d+)*$")

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_text = f.read()
    except Exception as e:
        return [f"Failed to read spec excerpt: {e}"]

    seen_names = []
    seen_anchors = {}
    seen_citations = {}

    # Gather all defined parameter names in this database for cross-referencing
    defined_names = {entry.get("name") for entry in entries if isinstance(entry, dict) and entry.get("name") is not None}

    for idx, entry in enumerate(entries):
        required_keys = {
            "name",
            "category",
            "udb_file",
            "section",
            "canonical_anchor",
            "canonical_citation",
            "secondary_anchors",
            "related_parameters",
            "mapping_type",
            "classification_rationale",
        }
        if not isinstance(entry, dict):
            errors.append(f"Entry {idx} is not a dictionary.")
            continue

        actual_keys = set(entry.keys())
        missing = required_keys - actual_keys
        extra = actual_keys - required_keys
        if missing:
            errors.append(f"Entry {idx} is missing keys: {missing}")
        if extra:
            errors.append(f"Entry {idx} contains unknown keys: {extra}")

        name = entry.get("name")
        category = entry.get("category")
        udb_file = entry.get("udb_file")
        section = entry.get("section")
        canonical_anchor = entry.get("canonical_anchor")
        canonical_citation = entry.get("canonical_citation")
        secondary_anchors = entry.get("secondary_anchors", [])
        related_parameters = entry.get("related_parameters", [])
        mapping_type = entry.get("mapping_type")
        rationale = entry.get("classification_rationale")

        if name is not None:
            if not isinstance(name, str) or not name_pattern.match(name):
                errors.append(f"Entry {idx}: invalid name format '{name}'")
            elif name not in VERIFIED_UDB_PARAMS:
                errors.append(f"Entry {idx}: name '{name}' is not one of the 228 verified parameters in riscv-unified-db")
            else:
                seen_names.append(name)
        else:
            seen_names.append("")

        if category not in {"named", "unnamed", "config-dependent"}:
            errors.append(f"Entry {idx}: invalid category '{category}'")

        if name is None and category != "unnamed":
            errors.append(f"Entry {idx}: null name requires category 'unnamed'")
        if name is not None and category == "unnamed":
            errors.append(f"Entry {idx}: named parameter cannot have category 'unnamed'")

        # Validate udb_file targets a real parameter in UDB
        if not isinstance(udb_file, str) or not udb_file.startswith("spec/std/isa/param/") or not udb_file.endswith(".yaml"):
            errors.append(f"Entry {idx}: invalid udb_file path format '{udb_file}'")
        elif name is not None:
            expected_udb_file = f"spec/std/isa/param/{name}.yaml"
            if udb_file != expected_udb_file:
                errors.append(f"Entry {idx}: udb_file '{udb_file}' mismatch for parameter name '{name}' (expected '{expected_udb_file}')")

        if not isinstance(section, str) or not section_pattern.match(section):
            errors.append(f"Entry {idx}: invalid section format '{section}'")

        # Validate canonical anchor format and uniqueness
        if not isinstance(canonical_anchor, str) or not anchor_pattern.match(canonical_anchor):
            errors.append(f"Entry {idx}: invalid canonical_anchor format '{canonical_anchor}'")
        else:
            anchor_tag = f"<!-- anchor: {canonical_anchor} -->"
            occurrences = spec_text.count(anchor_tag)
            if occurrences != 1:
                errors.append(f"Entry {idx}: anchor '{canonical_anchor}' must appear exactly once in spec text, found {occurrences}")
            if canonical_anchor in seen_anchors:
                errors.append(f"Entry {idx}: duplicate canonical_anchor '{canonical_anchor}' reused from entry {seen_anchors[canonical_anchor]}")
            else:
                seen_anchors[canonical_anchor] = idx

        if isinstance(secondary_anchors, list):
            for sa in secondary_anchors:
                if not isinstance(sa, str) or not anchor_pattern.match(sa):
                    errors.append(f"Entry {idx}: invalid secondary anchor format '{sa}'")
                elif spec_text.count(f"<!-- anchor: {sa} -->") == 0:
                    errors.append(f"Entry {idx}: secondary anchor '{sa}' not found in spec text")
        else:
            errors.append(f"Entry {idx}: secondary_anchors must be a list")

        # Validate related parameters point to other parameters that exist in the database
        if isinstance(related_parameters, list):
            for rp in related_parameters:
                if not isinstance(rp, str) or not name_pattern.match(rp):
                    errors.append(f"Entry {idx}: invalid related parameter name '{rp}'")
                elif rp not in defined_names:
                    errors.append(f"Entry {idx}: related parameter '{rp}' does not exist in the gold reference database")
        else:
            errors.append(f"Entry {idx}: related_parameters must be a list")

        if mapping_type not in {"simple", "unnamed", "one-to-many", "many-to-one"}:
            errors.append(f"Entry {idx}: invalid mapping_type '{mapping_type}'")

        if not isinstance(rationale, str) or len(rationale.strip()) <= 15:
            errors.append(f"Entry {idx}: classification_rationale must be a string and is too short")

        # Validate canonical citation existence, match, and uniqueness
        if isinstance(canonical_citation, str):
            citation = canonical_citation.strip()
            anchor_tag = f"<!-- anchor: {canonical_anchor} -->"
            if anchor_tag in spec_text:
                anchor_pos = spec_text.find(anchor_tag)
                following_text = spec_text[anchor_pos + len(anchor_tag):].strip()
                clean_following = re.sub(r"<!--.*?-->", "", following_text)
                
                norm_citation = " ".join(citation.split())
                norm_following = " ".join(clean_following.split())
                if not norm_following.startswith(norm_citation):
                    errors.append(f"Entry {idx} ({name}): citation mismatch following anchor.")
                
                # Check for duplicate citations
                if norm_citation in seen_citations:
                    errors.append(f"Entry {idx}: duplicate citation reused from entry {seen_citations[norm_citation]}")
                else:
                    seen_citations[norm_citation] = idx
        else:
            errors.append(f"Entry {idx}: canonical_citation must be a string")

    non_empty_names = [n for n in seen_names if n != ""]
    if len(non_empty_names) != len(set(non_empty_names)):
        errors.append("Duplicate parameter names are present in gold reference.")

    def sort_key(name_val: str) -> tuple[int, str]:
        if name_val == "":
            return (1, "")
        return (0, name_val)

    sorted_names = sorted(seen_names, key=sort_key)
    if seen_names != sorted_names:
        errors.append(f"Sorting violation. Expected alphabetical order: {sorted_names}")

    return errors


@click.group()
def main() -> None:
    """RISC-V Spec-to-Parameters Extractor with Evaluation Harness."""


@main.command(name="validate-gold")
@click.option(
    "--gold",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=Path("data/gold_reference.yaml"),
    help="Path to the gold reference file.",
)
@click.option(
    "--spec",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=Path("data/spec_excerpts/machine_counters.md"),
    help="Path to the spec excerpt file.",
)
def validate_gold_cmd(gold: Path, spec: Path) -> None:
    """Validate data/gold_reference.yaml against formatting rules."""
    click.echo(f"Validating {gold} against {spec}...")
    errors = validate_gold_file(gold, spec)
    if errors:
        click.echo(click.style(f"Validation FAILED with {len(errors)} errors:", fg="red"))
        for err in errors:
            click.echo(f"  - {err}")
        sys.exit(1)
    else:
        click.echo(click.style("Validation PASSED successfully.", fg="green"))
