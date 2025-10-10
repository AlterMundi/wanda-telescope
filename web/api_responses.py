"""Helper functions for standardized API responses."""
from typing import Any, Dict, Optional

from flask import jsonify


def success_response(data: Any, message: Optional[str] = None, http_status: int = 200):
    """Return a standardized success JSON response."""
    payload: Dict[str, Any] = {
        "success": True,
        "data": data,
        "message": message or "Operation completed successfully",
    }
    return jsonify(payload), http_status


def error_response(*, code: str, message: str, http_status: int = 400, data: Any = None):
    """Return a standardized error JSON response."""
    payload: Dict[str, Any] = {
        "success": False,
        "code": code,
        "error": message,
    }
    if data is not None:
        payload["data"] = data
    return jsonify(payload), http_status
