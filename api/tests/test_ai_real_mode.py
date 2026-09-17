"""Tests for RealAIService wiring that don't require torch/cv2/fitz to be
installed — they exercise ModelManager checkpoint discovery, which is what's
reachable without the full CV/DL dependency stack. Uses monkeypatch so the
env changes don't leak into other test modules.

Note: CHECKPOINTS_DIR is overridden to `models/saved` here because these
tests run from within `api/` in isolation. In the real project layout
(api/ next to models/ at the repo root), the default `../models/saved`
is correct and does not need overriding."""
from app.core.config import get_settings
from app.models.model_manager import ModelManager


def test_model_manager_detects_available_checkpoint(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("CHECKPOINTS_DIR", "models/saved")
    get_settings.cache_clear()
    settings = get_settings()
    manager = ModelManager(settings)
    manager.load()
    assert manager.has_checkpoint_for("Tracee1")
    assert not manager.has_checkpoint_for("Tracee2")
    assert manager.has_any_checkpoint()
    get_settings.cache_clear()


def test_model_manager_no_checkpoints_when_ai_disabled(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    manager = ModelManager(settings)
    manager.load()
    assert not manager.has_any_checkpoint()
    get_settings.cache_clear()
