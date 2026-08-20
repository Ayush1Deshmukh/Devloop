"""Deprecated module.

The request/response models used to be duplicated here (without validation) and
in ``app.models.schemas`` (with validation). ``schemas`` is now the single source
of truth; this module re-exports it so existing imports keep working.
"""

from app.models.schemas import GenerationRequest, GenerationResponse

__all__ = ["GenerationRequest", "GenerationResponse"]
