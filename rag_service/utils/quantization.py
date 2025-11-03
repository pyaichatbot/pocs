"""
Binary quantization utilities for vector compression.

Binary quantization reduces vector storage requirements by converting
float embeddings to binary representations while maintaining reasonable
search quality.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from ..config import Settings
from ..utils.logging import get_logger

try:
    import numpy as np  # type: ignore
except ImportError:
    np = None  # type: ignore


class Quantizer:
    """Binary quantizer for vector compression."""

    def __init__(self, settings: Settings, enabled: bool = False):
        """Initialize quantizer.

        Args:
            settings: Configuration settings.
            enabled: Whether quantization is enabled. Defaults to False.
        """
        self.logger = get_logger(__name__)
        self.settings = settings
        self.enabled = enabled and self._is_available()

        if self.enabled and np is None:
            self.logger.warning(
                "NumPy not available. Quantization disabled."
            )
            self.enabled = False

    def _is_available(self) -> bool:
        """Check if quantization is available."""
        return np is not None

    def quantize(self, vectors: List[List[float]]) -> Optional[List[List[int]]]:
        """Quantize float vectors to binary representations.

        Args:
            vectors: List of float vectors to quantize.

        Returns:
            List of binary vectors (0s and 1s), or None if disabled/unavailable.
        """
        if not self.enabled or not np:
            return None

        try:
            vectors_array = np.array(vectors, dtype=np.float32)
            # Binary quantization: > 0 becomes 1, <= 0 becomes 0
            binary_vectors = (vectors_array > 0).astype(np.int8)
            return binary_vectors.tolist()
        except Exception as exc:
            self.logger.error("Quantization failed: %s", exc)
            return None

    def dequantize(self, binary_vectors: List[List[int]]) -> Optional[List[List[float]]]:
        """Dequantize binary vectors back to float approximations.

        Args:
            binary_vectors: List of binary vectors.

        Returns:
            List of float vectors, or None if disabled/unavailable.
        """
        if not self.enabled or not np:
            return None

        try:
            binary_array = np.array(binary_vectors, dtype=np.int8)
            # Convert binary back to float: 1 -> 1.0, 0 -> -1.0
            float_vectors = (binary_array * 2.0 - 1.0).astype(np.float32)
            return float_vectors.tolist()
        except Exception as exc:
            self.logger.error("Dequantization failed: %s", exc)
            return None

