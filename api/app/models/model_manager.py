from pathlib import Path
from typing import Optional

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

KNOWN_TRACEES = ["Tracee1", "Tracee2", "Tracee3", "Tracee4"]


class ModelManager:
    """Owns model lifecycle: checks which fold checkpoints are available and
    exposes the compute device. The real pipeline (conformity_pipeline.py)
    loads a fresh model per tracé call — each of the 4 tracés uses its own
    leave-one-out checkpoint, so there's no single persistent model to cache
    here, unlike a typical single-model deployment."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.device = self._detect_device()
        self._available_checkpoints: Optional[set] = None

    @staticmethod
    def _detect_device() -> str:
        # torch is only required in real mode (AI_ENABLED=true). Importing it
        # lazily keeps mock mode free of the heavy CV/DL dependency stack.
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def load(self) -> None:
        if not self.settings.AI_ENABLED:
            logger.info("AI disabled (AI_ENABLED=false) — skipping checkpoint scan.")
            self._available_checkpoints = set()
            return

        checkpoints_dir = Path(self.settings.CHECKPOINTS_DIR)
        if not checkpoints_dir.is_dir():
            logger.warning("CHECKPOINTS_DIR '%s' not found.", checkpoints_dir)
            self._available_checkpoints = set()
            return

        found = set()
        for tracee in KNOWN_TRACEES:
            if (checkpoints_dir / f"unet_fold_{tracee}_best.pt").exists():
                found.add(tracee)

        self._available_checkpoints = found
        logger.info(
            "Checkpoints found (%d/%d): %s — device=%s",
            len(found), len(KNOWN_TRACEES), sorted(found) or "none", self.device,
        )

    def has_any_checkpoint(self) -> bool:
        return bool(self._available_checkpoints)

    def has_checkpoint_for(self, tracee: str) -> bool:
        return self._available_checkpoints is not None and tracee in self._available_checkpoints

    def is_loaded(self) -> bool:
        # Kept for interface parity with the mock-phase ModelManager; "loaded"
        # here means "at least one checkpoint is ready to be loaded on demand".
        return self.has_any_checkpoint()
