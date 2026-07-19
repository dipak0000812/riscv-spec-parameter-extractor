"""Candidate vs. gold-reference comparison logic.

Pure comparison — no I/O, no API calls. Classifies each candidate
as a match, hallucination, or partial match, and identifies missed
gold-reference entries.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from src.extractor.run_extraction import Candidate


@dataclass(frozen=True)
class GoldEntry:
    """Represents an entry in the gold-reference dataset."""

    name: Optional[str]
    category: str
    udb_file: str
    section: str
    canonical_anchor: str
    canonical_citation: str
    secondary_anchors: List[str]
    related_parameters: List[str]
    mapping_type: str
    classification_rationale: str


@dataclass
class DiffResult:
    """Contains results of comparing extracted candidates against gold reference."""

    # True Positives: (candidate, gold_entry)
    true_positives: List[Tuple[Candidate, GoldEntry]]

    # Partial Matches: (candidate, gold_entry, mismatch_reason)
    # Typically name matches but category differs.
    partial_matches: List[Tuple[Candidate, GoldEntry, str]]

    # False Positives (Hallucinations): candidates that did not match any gold entry
    false_positives: List[Candidate]

    # False Negatives (Missed): gold entries that were not matched by any candidate
    false_negatives: List[GoldEntry]


def normalize_name(name: Optional[str]) -> str:
    """Normalize parameter names for case-insensitive, symbol-agnostic matching."""
    if name is None:
        return ""
    return name.lower().replace("_", "").replace("-", "").replace(" ", "")


def diff_candidates_against_gold(
    candidates: List[Candidate], gold_entries: List[GoldEntry]
) -> DiffResult:
    """Compare a list of extracted Candidates against GoldEntries.

    Deterministic classification:
    - Named parameters are matched by normalized name.
    - Unnamed parameters are matched by anchor or citation overlap.
    - Duplicates/re-extractions are handled (only first match counts, others are FP).
    """
    true_positives: List[Tuple[Candidate, GoldEntry]] = []
    partial_matches: List[Tuple[Candidate, GoldEntry, str]] = []
    false_positives: List[Candidate] = []
    false_negatives: List[GoldEntry] = []

    # Keep track of which gold entries have been matched
    matched_gold_indices = set()

    for c_idx, candidate in enumerate(candidates):
        best_match_idx = None
        mismatch_reason = None

        c_name_norm = normalize_name(candidate.candidate_name)
        is_named_candidate = c_name_norm != ""

        for g_idx, gold in enumerate(gold_entries):
            # Skip if this gold entry was already matched
            if g_idx in matched_gold_indices:
                continue

            g_name_norm = normalize_name(gold.name)
            is_named_gold = g_name_norm != ""

            if is_named_candidate and is_named_gold:
                # Named match check
                if c_name_norm == g_name_norm:
                    best_match_idx = g_idx
                    if candidate.category != gold.category:
                        mismatch_reason = (
                            f"Category mismatch: candidate='{candidate.category}', gold='{gold.category}'"
                        )
                    break
            elif not is_named_candidate and not is_named_gold:
                # Unnamed match check: match by anchor or citation overlap
                c_anchor = candidate.paragraph.strip()
                g_anchors = [gold.canonical_anchor] + gold.secondary_anchors
                anchor_match = c_anchor in g_anchors or any(c_anchor == a.strip() for a in g_anchors)

                c_quote_norm = " ".join(candidate.exact_quotation.split()).lower()
                g_quote_norm = " ".join(gold.canonical_citation.split()).lower()
                quote_match = c_quote_norm in g_quote_norm or g_quote_norm in c_quote_norm

                if anchor_match or quote_match:
                    best_match_idx = g_idx
                    if candidate.category != gold.category:
                        mismatch_reason = (
                            f"Category mismatch for unnamed parameter: candidate='{candidate.category}', gold='{gold.category}'"
                        )
                    break

        if best_match_idx is not None:
            gold_entry = gold_entries[best_match_idx]
            matched_gold_indices.add(best_match_idx)
            if mismatch_reason is None:
                true_positives.append((candidate, gold_entry))
            else:
                partial_matches.append((candidate, gold_entry, mismatch_reason))
        else:
            false_positives.append(candidate)

    # Identify false negatives (unmatched gold entries)
    for g_idx, gold in enumerate(gold_entries):
        if g_idx not in matched_gold_indices:
            false_negatives.append(gold)

    return DiffResult(
        true_positives=true_positives,
        partial_matches=partial_matches,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )
