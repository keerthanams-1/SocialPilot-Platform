import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import Request
from fastapi.responses import JSONResponse

def standard_response(
    success: bool = True,
    message: str = "Operation completed successfully",
    data: Optional[Any] = None,
    errors: Optional[List[Any]] = None,
    status_code: int = 200,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Format standardized enterprise API JSON response."""
    payload = {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
        "errors": errors if errors is not None else [],
        "request_id": request_id or str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    return JSONResponse(content=payload, status_code=status_code)
