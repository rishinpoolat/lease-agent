"""The ModelProvider boundary — see docs/context/04-agent-boundaries.md.

Hard rules (enforced by convention + code review, not the type system):
1. Only apps/worker calls a ModelProvider. apps/api only enqueues jobs.
2. Every ExtractedField must carry a source_excerpt, or have
   confidence == "not_found" and source_excerpt == None. Never a value with
   no source.
3. The stub implementation (stub.py) is a first-class ModelProvider, not a
   shortcut — it does real heuristic extraction over the actual input, not
   canned output.
"""

from typing import Protocol

from agents.schemas import LeaseExtractionResult, PhotoAssessmentResult


class ImageRef(Protocol):
    """Enough to identify an uploaded photo without depending on the storage layer."""

    filename: str
    path: str


class ModelProvider(Protocol):
    def extract_lease(self, document_text: str) -> LeaseExtractionResult: ...

    def analyze_photos(self, images: list[ImageRef]) -> PhotoAssessmentResult: ...
