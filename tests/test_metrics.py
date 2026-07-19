"""Unit tests for the metrics engine in src.evaluation.metrics."""

import pytest
from src.evaluation.diff import DiffResult
from src.evaluation.metrics import compute_metrics


class MockDiffResult:
    """Helper to mock a DiffResult for testing."""

    def __init__(self, tp_count: int, fp_count: int, fn_count: int, pm_count: int) -> None:
        # We only need lengths of lists for compute_metrics,
        # so dummy items of the correct size are sufficient.
        self.true_positives = [None] * tp_count
        self.false_positives = [None] * fp_count
        self.false_negatives = [None] * fn_count
        self.partial_matches = [None] * pm_count


def test_standard_metrics() -> None:
    # 4 True Positives, 1 False Positive, 2 False Negatives, 1 Partial Match
    diff = MockDiffResult(tp_count=4, fp_count=1, fn_count=2, pm_count=1)
    
    report = compute_metrics(diff)  # type: ignore[arg-type]
    
    # Strict checks
    # tp_strict = 4
    # fp_strict = 1 + 1 = 2
    # fn_strict = 2 + 1 = 3
    # precision = 4 / 6 = 0.6667
    # recall = 4 / 7 = 0.5714
    # f1 = 2 * (4/6 * 4/7) / (4/6 + 4/7) = 0.6154
    assert report.strict.tp == 4
    assert report.strict.fp == 2
    assert report.strict.fn == 3
    assert report.strict.precision == 0.6667
    assert report.strict.recall == 0.5714
    assert report.strict.f1 == 0.6154

    # Relaxed checks
    # tp_relaxed = 4 + 1 = 5
    # fp_relaxed = 1
    # fn_relaxed = 2
    # precision = 5 / 6 = 0.8333
    # recall = 5 / 7 = 0.7143
    # f1 = 2 * (5/6 * 5/7) / (5/6 + 5/7) = 0.7692
    assert report.relaxed.tp == 5
    assert report.relaxed.fp == 1
    assert report.relaxed.fn == 2
    assert report.relaxed.precision == 0.8333
    assert report.relaxed.recall == 0.7143
    assert report.relaxed.f1 == 0.7692

    assert report.total_candidates == 6
    assert report.total_gold == 7
    assert report.partial_matches_count == 1


def test_perfect_matches() -> None:
    diff = MockDiffResult(tp_count=5, fp_count=0, fn_count=0, pm_count=0)
    report = compute_metrics(diff)  # type: ignore[arg-type]

    assert report.strict.precision == 1.0
    assert report.strict.recall == 1.0
    assert report.strict.f1 == 1.0
    assert report.relaxed.precision == 1.0
    assert report.relaxed.recall == 1.0
    assert report.relaxed.f1 == 1.0


def test_all_hallucinations() -> None:
    diff = MockDiffResult(tp_count=0, fp_count=5, fn_count=5, pm_count=0)
    report = compute_metrics(diff)  # type: ignore[arg-type]

    assert report.strict.precision == 0.0
    assert report.strict.recall == 0.0
    assert report.strict.f1 == 0.0
    assert report.relaxed.precision == 0.0
    assert report.relaxed.recall == 0.0
    assert report.relaxed.f1 == 0.0


def test_empty_candidates() -> None:
    diff = MockDiffResult(tp_count=0, fp_count=0, fn_count=5, pm_count=0)
    report = compute_metrics(diff)  # type: ignore[arg-type]

    assert report.strict.precision == 0.0
    assert report.strict.recall == 0.0
    assert report.strict.f1 == 0.0
    assert report.relaxed.precision == 0.0
    assert report.relaxed.recall == 0.0
    assert report.relaxed.f1 == 0.0


def test_empty_gold() -> None:
    diff = MockDiffResult(tp_count=0, fp_count=5, fn_count=0, pm_count=0)
    report = compute_metrics(diff)  # type: ignore[arg-type]

    assert report.strict.precision == 0.0
    assert report.strict.recall == 0.0
    assert report.strict.f1 == 0.0
    assert report.relaxed.precision == 0.0
    assert report.relaxed.recall == 0.0
    assert report.relaxed.f1 == 0.0


def test_zero_total() -> None:
    diff = MockDiffResult(tp_count=0, fp_count=0, fn_count=0, pm_count=0)
    report = compute_metrics(diff)  # type: ignore[arg-type]

    assert report.strict.precision == 0.0
    assert report.strict.recall == 0.0
    assert report.strict.f1 == 0.0
    assert report.relaxed.precision == 0.0
    assert report.relaxed.recall == 0.0
    assert report.relaxed.f1 == 0.0
