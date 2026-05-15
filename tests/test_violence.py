"""Testes da heurística placeholder de violência."""

from __future__ import annotations

import numpy as np

from yolo_violence_pipeline.violence import is_violence_detected


class _FakeKpts:
    def __init__(self, data: np.ndarray) -> None:
        self.data = data


def test_no_violence_when_empty() -> None:
    k = _FakeKpts(np.zeros((1, 0, 3), dtype=np.float64))
    assert is_violence_detected(k, confidence_threshold=0.5) is False


def test_violence_when_many_visible_keypoints() -> None:
    n = 17
    conf = np.zeros((1, n, 3), dtype=np.float64)
    conf[0, :, 0] = np.linspace(0, 1, n)
    conf[0, :, 1] = np.linspace(0, 1, n)
    conf[0, :, 2] = 0.9
    k = _FakeKpts(conf)
    assert is_violence_detected(k, confidence_threshold=0.5) is True


def test_no_violence_when_low_confidence() -> None:
    n = 17
    conf = np.zeros((1, n, 3), dtype=np.float64)
    conf[0, :, 2] = 0.1
    k = _FakeKpts(conf)
    assert is_violence_detected(k, confidence_threshold=0.9) is False
