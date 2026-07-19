"""Unit tests for the parameter extraction orchestration pipeline."""

import json
from pathlib import Path
import pytest
from src.extractor.backends import ExtractionBackend
from src.extractor.run_extraction import (
    Candidate,
    clean_json_response,
    parse_and_validate_candidates,
    run_extraction,
)


class MockBackend(ExtractionBackend):
    """Mock implementation of ExtractionBackend for testing."""

    def __init__(self, name: str, version: str, response: str) -> None:
        self._name = name
        self._version = version
        self.response = response
        self.call_count = 0

    def extract(self, prompt: str, spec_text: str) -> str:
        self.call_count += 1
        return self.response

    @property
    def name(self) -> str:
        return self._name

    @property
    def model_version(self) -> str:
        return self._version


def test_clean_json_response() -> None:
    # Test stripping markdown ticks
    raw = "```json\n[\n  {\"candidate_name\": \"TEST\"}\n]\n```"
    assert clean_json_response(raw) == "[\n  {\"candidate_name\": \"TEST\"}\n]"

    # Test stripping raw ticks without json label
    raw_no_label = "```\n[\n  1, 2\n]\n```"
    assert clean_json_response(raw_no_label) == "[\n  1, 2\n]"

    # Test leaving clean text alone
    clean = "[\n  1, 2\n]"
    assert clean_json_response(clean) == clean


def test_parse_and_validate_candidates() -> None:
    raw_json = json.dumps([
        {
            "candidate_name": "HPM_COUNTER_EN",
            "category": "named",
            "chapter": "Counters",
            "section": "3.1.10",
            "paragraph": "norm:mhpmcounter_num",
            "exact_quotation": "The hardware performance monitor includes 29 additional...",
            "reason_extracted": "Explicit named HPM count parameter."
        }
    ])
    candidates = parse_and_validate_candidates(raw_json, "mock-model-1")
    assert len(candidates) == 1
    assert candidates[0].candidate_name == "HPM_COUNTER_EN"
    assert candidates[0].category == "named"
    assert candidates[0].model == "mock-model-1"

    # Test with wrapped key dictionary (model wraps response in a dict)
    wrapped_json = json.dumps({
        "candidates": [
            {
                "candidate_name": "HPM_EVENTS",
                "category": "named",
                "chapter": "Counters",
                "section": "3.1.10",
                "paragraph": "norm:mhpmevent",
                "exact_quotation": "The event selector CSRs...",
                "reason_extracted": "Explicit parameter."
            }
        ]
    })
    wrapped_candidates = parse_and_validate_candidates(wrapped_json, "mock-model-1")
    assert len(wrapped_candidates) == 1
    assert wrapped_candidates[0].candidate_name == "HPM_EVENTS"


def test_parse_and_validate_failures() -> None:
    # Failure case: Invalid category
    bad_cat = json.dumps([{
        "candidate_name": "HPM_EVENTS",
        "category": "invalid-cat",
        "chapter": "Counters",
        "section": "3.1.10",
        "paragraph": "norm:mhpmevent",
        "exact_quotation": "...",
        "reason_extracted": "..."
    }])
    with pytest.raises(ValueError, match="category 'invalid-cat' is invalid"):
        parse_and_validate_candidates(bad_cat, "mock")

    # Failure case: Empty quotation
    bad_quote = json.dumps([{
        "candidate_name": "HPM_EVENTS",
        "category": "named",
        "chapter": "Counters",
        "section": "3.1.10",
        "paragraph": "norm:mhpmevent",
        "exact_quotation": "",
        "reason_extracted": "..."
    }])
    with pytest.raises(ValueError, match="exact_quotation must not be empty"):
        parse_and_validate_candidates(bad_quote, "mock")


def test_run_extraction_pipeline(tmp_path: Path) -> None:
    spec_file = tmp_path / "spec.md"
    prompt_file = tmp_path / "prompt.md"
    output_file = tmp_path / "output.yaml"
    cache_dir = tmp_path / "cache"

    spec_file.write_text("Spec text content", encoding="utf-8")
    prompt_file.write_text("Prompt template contents", encoding="utf-8")

    response_data = [
        {
            "candidate_name": "COUNTINHIBIT_EN",
            "category": "named",
            "chapter": "Counters",
            "section": "3.1.12",
            "paragraph": "norm:mcountinhibit",
            "exact_quotation": "The counter-inhibit register...",
            "reason_extracted": "Explicit parameter."
        }
    ]
    
    mock_backend = MockBackend("mock-api", "v1", json.dumps(response_data))

    # Run extraction 1: Cache Miss
    candidates = run_extraction(
        backend=mock_backend,
        spec_path=spec_file,
        prompt_path=prompt_file,
        output_path=output_file,
        cache_dir=cache_dir,
    )

    assert len(candidates) == 1
    assert candidates[0].candidate_name == "COUNTINHIBIT_EN"
    assert mock_backend.call_count == 1
    assert output_file.is_file()

    # Run extraction 2: Cache Hit (Backend shouldn't be called again)
    candidates_2 = run_extraction(
        backend=mock_backend,
        spec_path=spec_file,
        prompt_path=prompt_file,
        output_path=output_file,
        cache_dir=cache_dir,
    )

    assert len(candidates_2) == 1
    assert candidates_2[0].candidate_name == "COUNTINHIBIT_EN"
    assert mock_backend.call_count == 1  # Still 1, read from cache!
