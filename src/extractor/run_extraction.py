"""Extraction orchestration pipeline.

Loads spec excerpt and prompt, calls the configured backend,
parses and validates raw LLM output, writes structured candidate list.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import yaml
from src.extractor.backends import ExtractionBackend


@dataclass
class Candidate:
    """Represents a candidate parameter extracted from specification text."""

    candidate_name: str | None
    category: str
    chapter: str
    section: str
    paragraph: str
    exact_quotation: str
    reason_extracted: str
    model: str


def clean_json_response(raw_text: str) -> str:
    """Clean markdown formatting blocks from LLM raw response text if present."""
    text = raw_text.strip()
    # Strip markdown block ticks if present (e.g. ```json ... ```)
    if text.startswith("```"):
        # Match ```json ... ``` or similar block formatting
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1).strip()
    return text


def parse_and_validate_candidates(raw_text: str, model_version: str) -> list[Candidate]:
    """Parse raw JSON response from model and validate against Candidate schema."""
    cleaned = clean_json_response(raw_text)
    
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        # If response is a JSON object with a single key wrapping the list
        raise ValueError(f"Model response is not valid JSON: {err}\nRaw text:\n{cleaned}") from err

    # Normalize single object to list if model output a single item
    if isinstance(data, dict):
        # Some models wrap the list inside a key, e.g. {"candidates": [...]}
        for key in ["candidates", "parameters", "entries", "list"]:
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            data = [data]

    if not isinstance(data, list):
        raise ValueError("Model JSON response must be a list of candidate parameters.")

    candidates = []
    allowed_categories = {"named", "unnamed", "config-dependent"}

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Candidate entry {idx} is not a valid map structure.")

        # Extract values with clean defaults
        candidate_name = item.get("candidate_name")
        category = item.get("category", "").lower().strip()
        chapter = item.get("chapter", "").strip()
        section = str(item.get("section", "")).strip()
        paragraph = item.get("paragraph", "").strip()
        exact_quotation = item.get("exact_quotation", "").strip()
        reason_extracted = item.get("reason_extracted", "").strip()

        # Enforce name formats
        if candidate_name is not None:
            candidate_name = str(candidate_name).strip()
            if candidate_name == "null" or candidate_name == "":
                candidate_name = None

        if category not in allowed_categories:
            # Fallback mapper or raise error
            raise ValueError(
                f"Candidate {idx} ({candidate_name}): category '{category}' is invalid. "
                f"Must be one of: {allowed_categories}"
            )

        # Basic validation checks
        if not exact_quotation:
            raise ValueError(f"Candidate {idx} ({candidate_name}): exact_quotation must not be empty.")

        candidates.append(
            Candidate(
                candidate_name=candidate_name,
                category=category,
                chapter=chapter,
                section=section,
                paragraph=paragraph,
                exact_quotation=exact_quotation,
                reason_extracted=reason_extracted,
                model=model_version,
            )
        )

    return candidates


def run_extraction(
    backend: ExtractionBackend,
    spec_path: Path,
    prompt_path: Path,
    output_path: Path | None = None,
    cache_dir: Path | None = None,
) -> list[Candidate]:
    """Execute the extraction pipeline.

    Loads spec and prompt, fetches response using backend (with caching),
    parses, validates, and dumps candidates to output_path.
    """
    if not spec_path.is_file():
        raise FileNotFoundError(f"Spec file not found at: {spec_path}")
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt file not found at: {prompt_path}")

    # Read spec text and prompt text
    with open(spec_path, "r", encoding="utf-8") as f:
        spec_text = f.read()
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    # Determine caching key
    cache_key_data = (
        f"prompt={prompt_text}\n"
        f"spec={spec_text}\n"
        f"backend={backend.name}\n"
        f"model={backend.model_version}\n"
        f"temp=0.0"
    )
    cache_hash = hashlib.sha256(cache_key_data.encode("utf-8")).hexdigest()

    # Retrieve from cache if available
    raw_response = None
    cache_file = None
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{cache_hash}.json"
        if cache_file.is_file():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    raw_response = cache_data.get("response")
            except Exception:
                # If cache read fails, ignore and re-extract
                raw_response = None

    # Fetch from API if cache miss
    if raw_response is None:
        raw_response = backend.extract(prompt_text, spec_text)
        # Store in cache if directory provided
        if cache_file is not None:
            try:
                cache_payload = {
                    "metadata": {
                        "backend": backend.name,
                        "model_version": backend.model_version,
                        "prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
                        "spec_sha256": hashlib.sha256(spec_text.encode("utf-8")).hexdigest(),
                    },
                    "response": raw_response,
                }
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_payload, f, indent=2, ensure_ascii=False)
            except Exception:
                # Pass silently if cache write fails
                pass

    # Parse and validate Candidates
    candidates = parse_and_validate_candidates(raw_response, backend.model_version)

    # Save candidates list to output path if provided
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Convert dataclasses to dict list for serialization
        dump_data = [asdict(c) for c in candidates]
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(dump_data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    return candidates
