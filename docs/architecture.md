# Architecture Documentation

This document describes the software architecture and module layout of the RISC-V parameter extraction and evaluation harness.

## Package Layout

```
.
├── data/                       # Evaluation datasets and spec corpora
│   ├── gold_reference.yaml     # Alphabetical manually-verified gold mappings
│   └── spec_excerpts/          # plain-text target specification excerpts
│       └── machine_counters.md
├── docs/                       # Project specifications and methodology docs
├── prompts/                    # Versioned parameter-extraction LLM prompts
│   ├── current.md              # Active prompt used by the pipeline
│   └── v1.md
├── results/                    # Committed evaluation reports and raw outputs
├── src/                        # Core Python package code
│   ├── cli.py                  # CLI orchestration commands (validate-gold, etc)
│   ├── evaluation/             # Metrics calculation and matching algorithms
│   │   ├── diff.py
│   │   └── metrics.py
│   └── extractor/              # LLM backend client wrapper and cache managers
│       ├── backends.py
│       └── run_extraction.py
└── tests/                      # Automated pytest unit test suite
```

## Architectural Design Principles

1. **Separation of Concerns**: Business logic (matching, metric computation, API wrappers) is strictly partitioned from I/O orchestration (CLI command execution, file system management).
2. **Provider Isolation**: SDK imports for model providers (Google GenAI, OpenAI) are dynamically deferred inside the concrete backend execution hooks, protecting core application entry points from external SDK type leak.
3. **Immutability of Gold Mappings**: The evaluation benchmark dataset is locked behind a strict schema enforcer and does not contain mutable evaluation configuration parameters.
