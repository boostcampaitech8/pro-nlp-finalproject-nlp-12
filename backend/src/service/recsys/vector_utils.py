import json
import numpy as np
from typing import Optional


def parse_vector_json(user_vector_json: Optional[str]) -> np.ndarray:
    if not user_vector_json:
        return np.array([], dtype=float)
    try:
        arr = json.loads(user_vector_json)
        if not isinstance(arr, list) or len(arr) == 0:
            return np.array([], dtype=float)
        return np.array(arr, dtype=float)
    except Exception:
        return np.array([], dtype=float)


def safe_l2_normalize(v: np.ndarray) -> np.ndarray:
    try:
        norm = float(np.linalg.norm(v))
        if norm > 0:
            return v / norm
    except Exception:
        pass
    return v
