"""Pluggable LLM backend interface and concrete implementations.

Defines the abstract ExtractionBackend interface. Concrete backends
(Gemini, OpenAI) import their respective SDKs only within their own
modules/methods — no SDK types leak into the rest of the codebase.
"""

from abc import ABC, abstractmethod
import os


class ExtractionBackend(ABC):
    """Abstract base class representing an LLM backend for extraction."""

    @abstractmethod
    def extract(self, prompt: str, spec_text: str) -> str:
        """Execute extraction prompt against spec text.

        Returns the raw response string from the model.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name for this backend."""
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """The specific model name/version being executed."""
        pass


class GeminiBackend(ExtractionBackend):
    """Concrete backend utilizing Google's Gemini API."""

    def __init__(self, model_version: str = "gemini-2.5-flash", api_key: str | None = None) -> None:
        self._model_version = model_version
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please configure it before executing Gemini extractions."
            )

    def extract(self, prompt: str, spec_text: str) -> str:
        # Dynamically import SDK only when needed to isolate dependencies
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ImportError(
                "google-genai SDK is not installed. "
                "Please install it using 'pip install riscv-param-extractor[gemini]'"
            ) from e

        # Initialize client
        client = genai.Client(api_key=self._api_key)
        
        # Merge prompt and spec text as user contents
        contents = [
            prompt,
            "--- START OF SPECIFICATION TEXT ---",
            spec_text,
            "--- END OF SPECIFICATION TEXT ---"
        ]

        # Use system instructions or configurations if needed.
        # We configure temperature = 0.0 for maximum determinism.
        config = types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        )

        try:
            response = client.models.generate_content(
                model=self._model_version,
                contents=contents,
                config=config,
            )
            return response.text or ""
        except Exception as err:
            raise RuntimeError(f"Gemini API request failed: {err}") from err

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_version(self) -> str:
        return self._model_version


class OpenAIBackend(ExtractionBackend):
    """Concrete backend utilizing OpenAI's API."""

    def __init__(self, model_version: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        self._model_version = model_version
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please configure it before executing OpenAI extractions."
            )

    def extract(self, prompt: str, spec_text: str) -> str:
        # Dynamically import SDK only when needed to isolate dependencies
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "openai SDK is not installed. "
                "Please install it using 'pip install riscv-param-extractor[openai]'"
            ) from e

        client = OpenAI(api_key=self._api_key)

        messages = [
            {"role": "system", "content": "You are a static analysis tool that outputs raw JSON array maps."},
            {"role": "user", "content": f"{prompt}\n\n--- SPECIFICATION TEXT ---\n{spec_text}"}
        ]

        try:
            # We configure temperature = 0.0 for maximum determinism
            response = client.chat.completions.create(
                model=self._model_version,
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            choice = response.choices[0]
            return choice.message.content or ""
        except Exception as err:
            raise RuntimeError(f"OpenAI API request failed: {err}") from err

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_version(self) -> str:
        return self._model_version


class MockBackend(ExtractionBackend):
    """Mock backend for offline testing and evaluation runs."""

    def __init__(self, model_version: str = "mock-model-v1", api_key: str | None = None) -> None:
        self._model_version = model_version

    def extract(self, prompt: str, spec_text: str) -> str:
        # Predefined mock response reflecting typical extraction result.
        # It contains 7 correct parameters (one with a category mismatch),
        # 1 hallucination, and misses 1 parameter from the gold list (HCOUNTENABLE_EN).
        # This allows demonstrating the evaluation report's capabilities.
        import json
        mock_candidates = [
            {
                "candidate_name": "COUNTINHIBIT_EN",
                "category": "named",
                "chapter": "Machine-Level CSRs",
                "section": "3.1.12",
                "paragraph": "norm:mcountinhibit_sz_warl_op1",
                "exact_quotation": "The counter-inhibit register csr:mcountinhibit[] is a 32-bit *WARL* register that controls which of the hardware performance-monitoring counters increment.",
                "reason_extracted": "Configures which counters are inhibited."
            },
            {
                "candidate_name": "HPM_COUNTER_EN",
                "category": "named",
                "chapter": "Machine-Level CSRs",
                "section": "3.1.10",
                "paragraph": "norm:mhpmcounter_num",
                "exact_quotation": "The hardware performance monitor includes 29 additional 64-bit event counters, csr:mhpmcounter3[]–csr:mhpmcounter31[].",
                "reason_extracted": "Controls HPM counter enablement."
            },
            {
                "candidate_name": "HPM_EVENTS",
                "category": "named",
                "chapter": "Machine-Level CSRs",
                "section": "3.1.10",
                "paragraph": "norm:mhpmevent_sz_warl_op",
                "exact_quotation": "The event selector CSRs, csr:mhpmevent3[]–csr:mhpmevent31[], are 64-bit *WARL* registers that control which event causes the corresponding counter to increment.",
                "reason_extracted": "Configures events for counters."
            },
            {
                "candidate_name": "MCOUNTENABLE_EN",
                "category": "named",
                "chapter": "Machine-Level CSRs",
                "section": "3.1.11",
                "paragraph": "norm:mcounteren_sz",
                "exact_quotation": "The counter-enable csr:mcounteren[] register is a 32-bit register that controls the availability of the hardware performance-monitoring counters to the next-lowest privileged mode.",
                "reason_extracted": "Enables counters for lower privilege modes."
            },
            {
                "candidate_name": "MCOUNTINHIBIT_IMPLEMENTED",
                "category": "config-dependent",
                "chapter": "Machine-Level CSRs",
                "section": "3.1.12",
                "paragraph": "norm:mcountinhibit_not_impl",
                "exact_quotation": "If the csr:mcountinhibit[] register is not implemented, the implementation behaves as though the register were set to zero.",
                "reason_extracted": "Whether counter inhibit register is implemented."
            },
            {
                "candidate_name": "SCOUNTENABLE_EN",
                "category": "named",
                "chapter": "Machine-Level CSRs",
                "section": "3.1.11",
                "paragraph": "norm:mcounteren_set_nxt_priv",
                "exact_quotation": "When one of these bits is set, access to the corresponding register is permitted in the next implemented privilege mode (S-mode if implemented, otherwise U-mode).",
                "reason_extracted": "Enables counter access for supervisor/user mode."
            },
            {
                "candidate_name": "TIME_CSR_IMPLEMENTED",
                "category": "named",  # Category mismatch (Gold category is config-dependent)
                "chapter": "Machine-Level CSRs",
                "section": "3.1.11",
                "paragraph": "norm:time_op_rdonly",
                "exact_quotation": "The csr:time[] CSR is a read-only shadow of the memory-mapped csr:mtime[] register.",
                "reason_extracted": "Configuration of shadow time register."
            },
            {
                "candidate_name": "MSTATUS_FS_LEGAL_VALUES",
                "category": "named",
                "chapter": "Machine-Level CSRs",
                "section": "3.1.10",
                "paragraph": "norm:mhpmcounter_num",
                "exact_quotation": "The hardware performance monitor includes 29 additional 64-bit event counters...",
                "reason_extracted": "Out-of-scope parameter injected to simulate a cross-chapter association error."
            }
        ]
        return json.dumps(mock_candidates)

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model_version(self) -> str:
        return self._model_version
