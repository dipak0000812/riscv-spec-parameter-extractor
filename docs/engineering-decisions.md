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

---

## Decision 3: Strict vs. Relaxed Evaluation Modes in Metrics

### Problem
Evaluating model performance strictly (demanding correct classification category) and relaxed (evaluating name correctness only) both represent critical engineering views. Hardcoding a single interpretation hides the model's true characteristics. For example, a model that finds all 8 correct parameter names but gets 3 categories wrong will receive a lower F1 under strict evaluation, even though its identification capability was perfect.

### Decision
Calculate and report both **Strict** and **Relaxed (Name-Only)** metrics in the final summary report. 
- In **Strict Mode**, partial matches are counted as both False Positives and False Negatives, reflecting classification failures. Strict mode's double-counting of partial matches (both FP and FN) means strict F1 penalizes category errors more heavily than either a pure miss or a pure hallucination alone would.
- In **Relaxed Mode**, partial matches are counted as True Positives, reflecting correct identification.

### Alternatives Considered
1. **Single Strict Metric**: Report only strict accuracy.
   * *Why rejected:* Hides the model's parameter discovery performance. A developer fine-tuning a model might want to know if the model is good at finding parameters but just needs classification alignment.
2. **Weighted Score (e.g., F1.5 or 0.5 weight for partial)**:
   * *Why rejected:* Arbitrary weights (like 0.5) lack clear mathematical or architectural justification, making comparisons less intuitive than separate strict/relaxed bounds.

### Trade-offs
* **Pros**: Provides a transparent upper and lower bound on model capability, clearly showing where the model succeeds (naming) vs where it struggles (categorization).
* **Cons**: Increases the amount of data in the evaluation report, requiring clear visual separation in tables.

---

## Decision 4: Mock Backend Integration for Offline Verification

### Problem
Executing LLM extraction requires API keys (e.g. GEMINI_API_KEY) and network access. In testing, CI/CD pipelines, or local developer review settings, these credentials might not be present or network requests might be disabled. Without an offline extraction mode, testing the end-to-end pipeline (extraction -> candidates -> diff -> metrics -> evaluation report) becomes impossible or heavily mock-dependent inside testing frameworks, making the CLI commands hard to verify.

### Decision
Implement a pluggable `MockBackend` in `src/extractor/backends.py` and expose it as a choice in the CLI (`--backend mock`). The `MockBackend` simulates a realistic extraction run on the target hardware performance monitor excerpt. It returns a deterministic JSON response representing a high-performing model that extracts 7 of the 8 gold parameters correctly, introduces one category mismatch, misses one parameter, and introduces one hallucination.

### Alternatives Considered
1. **Require API Keys**: Force developers to configure API keys for any CLI run.
   * *Why rejected:* Severely harms onboarding, local development, and reproducible review when API keys are not available or are restricted.
2. **Mock only at unit test level**: Use pytest mocks for testing, but let the CLI fail if no keys are present.
   * *Why rejected:* Prevents executing the actual CLI commands (`extract`, `run`) in a real shell environment.

### Trade-offs
* **Pros**: Enables zero-dependency, zero-cost, fully offline end-to-end execution of the CLI pipeline. Facilitates immediate visual validation of evaluation report generation.
* **Cons**: The returned candidates list is static and does not reflect real-time spec modifications. However, for verification of the harness code itself, this is a positive trait.

---

## Decision 5: Gold Reference Derived from the RISC-V Unified Database (UDB)

### Problem
The evaluation harness needs a ground-truth dataset to compare LLM output against. The two natural sources are: (a) manually-written entries from specification reading alone, or (b) entries anchored to a machine-readable authoritative source.

### Decision
The gold reference (`data/gold_reference.yaml`) is built by tracing each parameter back to a named `.yaml` file inside the [riscv-unified-db](https://github.com/riscv/riscv-unified-db) repository, recording the exact UDB commit hash used (`e195c8b2ca0c3e152ac0214e940f1aed3c4f6876`). Every entry requires a `udb_file` field pointing to the canonical parameter definition file. Manual curation decisions are limited to mapping spec prose to UDB entries and classifying the category.

### Alternatives Considered
1. **Manual-only gold list**: Write gold entries based solely on reading the specification, without cross-referencing UDB files.
   * *Why rejected:* Produces a gold reference with no external traceability. A reviewer cannot verify whether a parameter is genuinely architectural or was invented by the annotator. The entire credibility of the evaluation collapses without an authoritative ground truth.
2. **Parse UDB YAML files directly**: Auto-generate the gold list by parsing all UDB `.yaml` parameter files and matching them to spec sections.
   * *Why rejected:* UDB files do not contain canonical spec citations or anchors. Auto-generation would skip the manual verification step needed to confirm each parameter genuinely appears in the chosen spec excerpt.

### Trade-offs
* **Pros**: Every entry is verifiable against the real UDB repository at a fixed commit. Precision/recall numbers are meaningfully tied to an authoritative external source, not the annotator's private judgment.
* **Cons**: Requires manual cross-referencing at construction time. Any UDB schema changes require re-verification of field mappings.

---

## Decision 6: Deterministic Name-Based Matching in the Diff Engine

### Problem
When comparing extracted candidates against the gold reference, there are multiple possible matching strategies: exact string match, fuzzy string match, embedding-based semantic similarity, or the chosen normalized name match. Each choice changes which extractions count as true positives.

### Decision
Match named parameters using case-insensitive, symbol-agnostic normalization only (`normalize_name` strips underscores, dashes, and spaces before comparing lowercased strings). No fuzzy matching, no edit distance, no embedding similarity. Unnamed parameters are matched by anchor string equality or citation substring inclusion.

### Alternatives Considered
1. **Fuzzy String Matching (e.g., Levenshtein distance)**: Allow near-matches like `HPM_COUNT` to match `HPM_COUNTER_EN` within a threshold.
   * *Why rejected:* Introduces a tunable threshold with no principled basis. An edit distance of 3 might correctly match abbreviations but also incorrectly match unrelated parameter names that happen to share a short prefix. Produces non-reproducible results if the threshold is ever adjusted.
2. **Embedding-Based Semantic Matching**: Embed both candidate names and gold names, then match by cosine similarity above a threshold.
   * *Why rejected:* Requires an embedding model, adds a heavyweight dependency, and introduces another unverifiable threshold. More importantly: UDB parameter names are intentional identifiers, not natural language descriptions. Semantic similarity between names is not a meaningful signal — `HPM_EVENTS` and `HPM_COUNTER_EN` are semantically similar but refer to distinct parameters.

### Trade-offs
* **Pros**: Fully deterministic — the same candidate list always produces the same diff result regardless of model or runtime environment. Easy to audit: a miss is a miss, not a "close enough" judgment call.
* **Cons**: A model that outputs `HPM_COUNT` instead of `HPM_COUNTER_EN` is scored as a false positive even though it identified the right concept. This is acceptable — the extraction prompt specifies UDB canonical names must be used, and a miss here signals a real prompt engineering gap.

---

## Decision 7: No Retrieval-Augmented Generation (RAG)

### Problem
Many LLM-based extraction systems use retrieval-augmented generation (RAG) to inject relevant context dynamically: embedding spec chunks into a vector database, then retrieving the most relevant chunks at query time before prompting the model. This was considered as an architectural option for this project.

### Decision
No RAG, no vector database. The entire spec excerpt is provided directly in the prompt as a single context block. The scope is deliberately small (§3.1.10–§3.1.12, under 1,500 words), so the full excerpt fits within the model's context window without truncation.

### Alternatives Considered
1. **Dense retrieval with a vector database (e.g., FAISS, Chroma)**: Embed spec paragraphs, retrieve top-k most relevant at extraction time, inject them into the prompt.
   * *Why rejected:* Adds significant infrastructure (embedding model, vector store, retrieval logic) for a scope where it provides no benefit. The excerpt is small enough to include in full. RAG would also make the extraction non-deterministic (retrieval ranking can vary between runs) and harder to reproduce.
2. **BM25 keyword retrieval**: Use sparse TF-IDF or BM25 to retrieve relevant paragraphs before prompting.
   * *Why rejected:* Same reasoning. For this project scope, full-context is both feasible and preferable. Retrieval adds a pre-processing step that could silently drop relevant paragraphs, making errors harder to diagnose.

### Trade-offs
* **Pros**: Simpler architecture, fully reproducible, no infrastructure dependencies beyond the LLM API itself. Every run on the same input produces the same output.
* **Cons**: Does not scale beyond the context window limit. If the project scope is extended to the full ISA manual (hundreds of pages), a chunking and retrieval strategy will be required.

---

## Decision 8: LLM Response Caching by Content Hash

### Problem
Running LLM extraction against a live API is expensive (time and API cost) and non-reproducible — the same prompt can return different results across calls if temperature > 0 or model versions drift. Repeatedly calling the API during development iteration is wasteful.

### Decision
Cache raw API responses by a SHA-256 hash of the concatenated prompt text, spec text, backend name, model version string, and temperature value. Cache files are stored in `results/raw/.cache/` (gitignored). Temperature is hardcoded to 0.0 in all backends to maximize within-session determinism. The cache is never reused silently when any input changes — a changed prompt or spec always produces a new hash and a new API call.

### Alternatives Considered
1. **No caching, always call API**: Simplest approach, no cache management needed.
   * *Why rejected:* Makes iterative development expensive and slow. A single development session involving multiple evaluation runs would call the API dozens of times for functionally identical inputs.
2. **Cache by prompt hash only (ignore spec text)**: Simpler cache key that only hashes the prompt template.
   * *Why rejected:* If the spec excerpt changes (e.g., a correction to `machine_counters.md`) while the prompt stays the same, the old cached response would be silently reused against the new spec content, producing incorrect results with no warning.

### Trade-offs
* **Pros**: Eliminates redundant API calls during development. Cache invalidation is automatic and correct — any meaningful input change produces a new cache entry.
* **Cons**: Cache files accumulate silently. If the cache directory is not periodically cleaned, stale entries from old experiments can consume disk space, though they will never be incorrectly reused.
