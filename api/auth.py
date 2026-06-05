import os
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str = Depends(api_key_header)) -> str:
    """
    Verify API key from X-API-Key header.

    Args:
        key: API key from header

    Returns:
        str: The API key if valid

    Raises:
        HTTPException: 403 if key is missing or invalid
    """
    expected_key = os.getenv("API_KEY", "dev-secret-key")

    if not key or key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key"
        )

    return key
