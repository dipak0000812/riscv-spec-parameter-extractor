"""Precision, recall, and F1 computation.

Pure math — no I/O. Takes a DiffResult and produces a MetricsReport.
Handles all division-by-zero edge cases safely.
"""

from dataclasses import dataclass
from src.evaluation.diff import DiffResult


@dataclass(frozen=True)
class MetricsSummary:
    """Detailed precision, recall, and F1 metrics for a specific evaluation mode."""

    precision: float
    recall: float
    f1: float
    tp: float
    fp: float
    fn: float


@dataclass(frozen=True)
class MetricsReport:
    """Unified report containing both strict and relaxed evaluation metrics."""

    strict: MetricsSummary
    relaxed: MetricsSummary
    total_candidates: int
    total_gold: int
    partial_matches_count: int


def _compute_summary(tp: float, fp: float, fn: float) -> MetricsSummary:
    """Helper to safely calculate precision, recall, and F1 scores."""
    precision = 0.0
    recall = 0.0
    f1 = 0.0

    if (tp + fp) > 0:
        precision = tp / (tp + fp)

    if (tp + fn) > 0:
        recall = tp / (tp + fn)

    if (precision + recall) > 0:
        f1 = (2 * precision * recall) / (precision + recall)

    return MetricsSummary(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        tp=tp,
        fp=fp,
        fn=fn,
    )


def compute_metrics(diff: DiffResult) -> MetricsReport:
    """Compute strict and relaxed metrics from a DiffResult.

    Strict Mode:
    - True Positives must match both name and category.
    - Partial matches (category mismatch) count as both FP and FN.

    Relaxed Mode (Name-Only):
    - Name-only matches count as True Positives, ignoring category correctness.
    - Partial matches count as True Positives.
    """
    tp_strict = len(diff.true_positives)
    fp_strict = len(diff.false_positives) + len(diff.partial_matches)
    fn_strict = len(diff.false_negatives) + len(diff.partial_matches)

    tp_relaxed = len(diff.true_positives) + len(diff.partial_matches)
    fp_relaxed = len(diff.false_positives)
    fn_relaxed = len(diff.false_negatives)

    strict_summary = _compute_summary(tp_strict, fp_strict, fn_strict)
    relaxed_summary = _compute_summary(tp_relaxed, fp_relaxed, fn_relaxed)

    total_candidates = len(diff.true_positives) + len(diff.partial_matches) + len(diff.false_positives)
    total_gold = len(diff.true_positives) + len(diff.partial_matches) + len(diff.false_negatives)

    return MetricsReport(
        strict=strict_summary,
        relaxed=relaxed_summary,
        total_candidates=total_candidates,
        total_gold=total_gold,
        partial_matches_count=len(diff.partial_matches),
    )
