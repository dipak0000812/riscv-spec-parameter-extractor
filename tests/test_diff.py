"""Unit tests for the diff engine in src.evaluation.diff."""

import pytest
from src.extractor.run_extraction import Candidate
from src.evaluation.diff import (
    GoldEntry,
    diff_candidates_against_gold,
    normalize_name,
)


def create_gold_entry(
    name: str | None,
    category: str = "named",
    section: str = "3.1.10",
    canonical_anchor: str = "norm:anchor",
    canonical_citation: str = "Standard specification text.",
) -> GoldEntry:
    """Helper to create dummy GoldEntry with defaults."""
    return GoldEntry(
        name=name,
        category=category,
        udb_file=f"spec/std/isa/param/{name}.yaml" if name else "spec/std/isa/param/unnamed.yaml",
        section=section,
        canonical_anchor=canonical_anchor,
        canonical_citation=canonical_citation,
        secondary_anchors=[],
        related_parameters=[],
        mapping_type="simple" if name else "unnamed",
        classification_rationale="Test rationale.",
    )


def create_candidate(
    name: str | None,
    category: str = "named",
    section: str = "3.1.10",
    paragraph: str = "norm:anchor",
    exact_quotation: str = "Standard specification text.",
) -> Candidate:
    """Helper to create dummy Candidate with defaults."""
    return Candidate(
        candidate_name=name,
        category=category,
        chapter="Test Chapter",
        section=section,
        paragraph=paragraph,
        exact_quotation=exact_quotation,
        reason_extracted="Test reason.",
        model="test-model",
    )


def test_normalize_name() -> None:
    assert normalize_name("HPM_COUNTER_EN") == "hpmcounteren"
    assert normalize_name("hpm_counter_en") == "hpmcounteren"
    assert normalize_name("Hpm Counter En") == "hpmcounteren"
    assert normalize_name("hpm-counter-en") == "hpmcounteren"
    assert normalize_name(None) == ""


def test_perfect_matches() -> None:
    gold = [
        create_gold_entry("HPM_COUNTER_EN", "named"),
        create_gold_entry("COUNTINHIBIT_EN", "named"),
    ]
    candidates = [
        create_candidate("HPM_COUNTER_EN", "named"),
        create_candidate("COUNTINHIBIT_EN", "named"),
    ]

    result = diff_candidates_against_gold(candidates, gold)
    assert len(result.true_positives) == 2
    assert len(result.partial_matches) == 0
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0

    assert result.true_positives[0][0].candidate_name == "HPM_COUNTER_EN"
    assert result.true_positives[1][0].candidate_name == "COUNTINHIBIT_EN"


def test_case_insensitive_and_symbol_insensitivity() -> None:
    gold = [create_gold_entry("HPM_COUNTER_EN", "named")]
    candidates = [create_candidate("hpm_counter_en", "named")]

    result = diff_candidates_against_gold(candidates, gold)
    assert len(result.true_positives) == 1
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0


def test_category_mismatch_is_partial_match() -> None:
    gold = [create_gold_entry("HPM_COUNTER_EN", "named")]
    candidates = [create_candidate("HPM_COUNTER_EN", "config-dependent")]

    result = diff_candidates_against_gold(candidates, gold)
    assert len(result.true_positives) == 0
    assert len(result.partial_matches) == 1
    assert len(result.false_positives) == 0
    assert len(result.false_negatives) == 0

    cand, gentry, reason = result.partial_matches[0]
    assert cand.candidate_name == "HPM_COUNTER_EN"
    assert gentry.name == "HPM_COUNTER_EN"
    assert "Category mismatch" in reason


def test_hallucinations_and_missed() -> None:
    gold = [create_gold_entry("HPM_COUNTER_EN", "named")]
    candidates = [create_candidate("EXTRA_PARAM_NAME", "named")]

    result = diff_candidates_against_gold(candidates, gold)
    assert len(result.true_positives) == 0
    assert len(result.partial_matches) == 0
    assert len(result.false_positives) == 1
    assert len(result.false_negatives) == 1

    assert result.false_positives[0].candidate_name == "EXTRA_PARAM_NAME"
    assert result.false_negatives[0].name == "HPM_COUNTER_EN"


def test_duplicate_extractions() -> None:
    gold = [create_gold_entry("HPM_COUNTER_EN", "named")]
    candidates = [
        create_candidate("HPM_COUNTER_EN", "named"),
        create_candidate("HPM_COUNTER_EN", "named"),  # Duplicate
    ]

    result = diff_candidates_against_gold(candidates, gold)
    assert len(result.true_positives) == 1
    assert len(result.partial_matches) == 0
    assert len(result.false_positives) == 1  # Second one is classified as FP (hallucination/redundancy)
    assert len(result.false_negatives) == 0


def test_unnamed_parameter_matching() -> None:
    gold = [
        create_gold_entry(
            name=None,
            category="unnamed",
            canonical_anchor="norm:unnamed_ref",
            canonical_citation="This is an unnamed parameter definition.",
        )
    ]

    # Test match by anchor
    cand_anchor_match = [
        create_candidate(
            name=None,
            category="unnamed",
            paragraph="norm:unnamed_ref",
            exact_quotation="Different citation text.",
        )
    ]
    res_anchor = diff_candidates_against_gold(cand_anchor_match, gold)
    assert len(res_anchor.true_positives) == 1
    assert len(res_anchor.false_positives) == 0

    # Test match by citation overlap
    cand_quote_match = [
        create_candidate(
            name=None,
            category="unnamed",
            paragraph="norm:wrong_anchor",
            exact_quotation="unnamed parameter definition",
        )
    ]
    res_quote = diff_candidates_against_gold(cand_quote_match, gold)
    assert len(res_quote.true_positives) == 1
    assert len(res_quote.false_positives) == 0

    # Test unnamed category mismatch
    cand_mismatch = [
        create_candidate(
            name=None,
            category="config-dependent",
            paragraph="norm:unnamed_ref",
            exact_quotation="This is an unnamed parameter definition.",
        )
    ]
    res_mismatch = diff_candidates_against_gold(cand_mismatch, gold)
    assert len(res_mismatch.true_positives) == 0
    assert len(res_mismatch.partial_matches) == 1
