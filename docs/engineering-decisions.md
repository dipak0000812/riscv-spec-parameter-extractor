# Engineering Decisions Log

This document records the key architectural and design decisions made during the implementation of the RISC-V Spec-to-Parameters Extractor.

---

## Decision 1: Diff Mapping and Duplicate Extraction Policy

### Problem
When the extraction engine runs, an LLM might output multiple duplicate candidate entries for a single parameter, or multiple candidates might match the same gold-reference parameter. If all of these duplicate matches are counted as True Positives (TP), the precision metric will be artificially inflated, and recall could exceed 100%.

### Decision
Implement a strict, stateful mapping policy in `src/evaluation/diff.py` where a gold-reference entry can be matched at most once. Once a gold entry index is matched to a candidate, that gold entry is marked as matched and is unavailable for subsequent candidate matches. Any subsequent candidate extracting the same parameter name is treated as a duplicate and classified under `false_positives` (a hallucination/redundancy).

### Alternatives Considered
1. **Permissive Matching**: Allow multiple candidates to match the same gold entry, counting each as a True Positive.
   * *Why rejected:* Fails to penalize LLM redundancy and violates mathematical correctness of precision/recall metrics.
2. **Pre-deduplication**: De-duplicate the candidate list by parameter name prior to running the diff engine.
   * *Why rejected:* If a candidate matches a name but has an incorrect category, and another candidate has the correct name and category, pre-deduplication might discard the correct one depending on ordering. Deferring the duplication check to the diff matching loop ensures the best match is selected.

### Trade-offs
* **Pros**: Guarantees metrics are mathematically bounded (precision and recall between 0.0 and 1.0) and accurately penalizes redundant LLM extractions.
* **Cons**: The ordering of the candidate list determines which candidate claims the gold entry first. However, since the candidates are processed sequentially, this is deterministic and reflects the extraction order.

---

## Decision 2: Treatment of Category Mismatch (Partial Matches)

### Problem
If an LLM extracts the correct parameter name (e.g. `HPM_COUNTER_EN`) but classifies its category incorrectly (e.g. classifying it as `config-dependent` instead of `named`), it is not a complete hallucination, nor is it a fully correct extraction. 

### Decision
Classify these cases explicitly as `partial_matches` in `src/evaluation/diff.py`. They are segregated from both `true_positives` (perfect name and category matches) and absolute `false_positives` (complete hallucinations). 

### Alternatives Considered
1. **Strict Mismatch**: Treat any category mismatch as a pure False Positive and False Negative.
   * *Why rejected:* Too punitive. In practice, finding the correct parameter name in the spec is a significant portion of the task's difficulty. Ignoring name correctness because of a category error obscures model capabilities.
2. **Soft True Positive**: Treat any name match as a True Positive, ignoring the category correctness.
   * *Why rejected:* Fails to evaluate the model's classification performance, which is a key requirement of the specification.

### Trade-offs
* **Pros**: Provides a granular view of model performance, separating parsing errors (finding the wrong text) from classification errors (getting the category wrong).
* **Cons**: Requires the metrics engine to explicitly define how partial matches are accounted for in F1 calculations (e.g. treating them as partial successes or strict failures).
