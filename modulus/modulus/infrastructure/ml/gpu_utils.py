"""Lightweight GPU detection and array helpers for optional cuML/CuPy backends."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional, Tuple
import importlib


def _import_optional(module_name: str):
    """Import a module if available; return None on ImportError."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


@lru_cache(maxsize=1)
def detect_gpu_stack(device_id: Optional[int] = None) -> dict:
    """
    Detect whether the GPU stack (CuPy/cuML/cuDF) is available.

    Returns a dictionary with:
        available: bool
        cupy: module or None
        cuml: module or None
        cudf: module or None
        error: optional error string when detection failed
        device: optional device name/info when available
    """
    cp = _import_optional("cupy")

    # Shim sklearn for cuML compatibility (some builds expect _get_default_requests)
    try:
        from sklearn.base import BaseEstimator  # type: ignore

        if not hasattr(BaseEstimator, "_get_default_requests") and hasattr(
            BaseEstimator, "_get_metadata_request"
        ):
            def _get_default_requests(self):  # type: ignore
                return self._get_metadata_request()

            # Bind as classmethod to match sklearn internal expectations
            BaseEstimator._get_default_requests = _get_default_requests  # type: ignore[attr-defined]
    except Exception:
        pass

    cuml = _import_optional("cuml")
    cudf = _import_optional("cudf")

    available = cp is not None and cuml is not None and cudf is not None
    error = None

    if not available:
        return {
            "available": False,
            "cupy": cp,
            "cuml": cuml,
            "cudf": cudf,
            "error": "Missing cupy/cuml/cudf",
        }

    try:
        device_count = cp.cuda.runtime.getDeviceCount()
        if device_count == 0:
            return {
                "available": False,
                "cupy": cp,
                "cuml": cuml,
                "cudf": cudf,
                "error": "No CUDA devices visible",
            }

        # Activate requested device (or default 0)
        dev = cp.cuda.Device(0 if device_id is None else device_id)
        dev.use()
        device_name = cp.cuda.runtime.getDeviceProperties(dev.id)["name"].decode()
    except Exception as exc:  # noqa: BLE001
        available = False
        error = str(exc)
        device_name = None

    return {
        "available": available,
        "cupy": cp,
        "cuml": cuml,
        "cudf": cudf,
        "error": error,
        "device": device_name if available else None,
    }


def to_gpu_array(array: Any) -> Tuple[Any, bool]:
    """
    Move numpy array to GPU as CuPy if available.

    Returns tuple: (possibly converted array, used_gpu flag)
    """
    state = detect_gpu_stack()
    cp = state.get("cupy")
    if not state.get("available") or cp is None:
        return array, False

    if isinstance(array, cp.ndarray):
        return array, True
    return cp.asarray(array), True


def to_cpu_array(array: Any) -> Any:
    """Ensure output is a numpy array."""
    state = detect_gpu_stack()
    cp = state.get("cupy")
    if cp is not None and isinstance(array, cp.ndarray):
        return cp.asnumpy(array)
    return array


def ensure_numpy(*arrays: Any) -> Tuple[Any, ...]:
    """Convert any CuPy arrays to numpy for downstream sklearn metrics."""
    return tuple(to_cpu_array(arr) for arr in arrays)


def gpu_available() -> bool:
    """Convenience boolean flag."""
    return bool(detect_gpu_stack().get("available"))


def format_gpu_state(state: dict) -> str:
    """Human-readable summary for logging."""
    if not state.get("available"):
        return f"GPU unavailable ({state.get('error', 'unknown reason')})"
    dev = state.get("device") or "CUDA device"
    cp = state.get("cupy")
    cuml = state.get("cuml")
    return f"GPU available: {dev} | CuPy: {getattr(cp, '__version__', 'unknown')} | cuML: {getattr(cuml, '__version__', 'unknown')}"



