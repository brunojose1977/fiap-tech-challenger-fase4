"""Lógica de detecção de violência (placeholder, como no notebook)."""

from __future__ import annotations

import numpy as np


def _numel(data) -> int:
    if hasattr(data, "numel"):
        return int(data.numel())
    return int(np.asarray(data).size)


def _row_slice(data, index: int):
    """Retorna linhas (n, 3) compatível com tensor ou ndarray."""
    if hasattr(data, "__getitem__"):
        return data[index]
    raise TypeError("keypoints.data não suporta indexação")


def _to_numpy_2d(row_slice) -> np.ndarray:
    if hasattr(row_slice, "detach"):
        return row_slice.detach().cpu().numpy()
    return np.asarray(row_slice, dtype=np.float64)


def is_violence_detected(person_keypoints, confidence_threshold: float = 0.5) -> bool:
    """
    Placeholder: no notebook, dispara se houver mais de 10 keypoints visíveis acima do limiar.

    Args:
        person_keypoints: objeto keypoints do Ultralytics (com `.data`).
        confidence_threshold: confiança mínima por keypoint.

    Returns:
        True se a heurística placeholder considerar "violência".
    """
    if person_keypoints is None:
        return False

    data = getattr(person_keypoints, "data", None)
    if data is None or _numel(data) == 0:
        return False

    kpts = _to_numpy_2d(_row_slice(data, 0))
    visible_kpts = kpts[kpts[:, 2] > confidence_threshold]
    return len(visible_kpts) > 10
