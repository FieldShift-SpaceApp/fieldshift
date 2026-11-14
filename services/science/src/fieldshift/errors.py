# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Expected pipeline failures (architecture, Error Handling Strategy)."""

from __future__ import annotations

from fieldshift.contracts.manifest import LayerReasonCode


class PipelineError(Exception):
    """Unexpected failure: stops the pipeline."""


class LayerError(Exception):
    """Expected failure of one layer. `message` is English: it may reach the UI (manifest)."""

    def __init__(self, code: LayerReasonCode, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
