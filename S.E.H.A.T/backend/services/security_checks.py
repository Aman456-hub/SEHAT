import os
import logging
from fastapi import Request, HTTPException

logger = logging.getLogger("security_checks")

async def verify_webhook_token(request: Request):
    """
    Optional security check to verify that incoming webhook requests
    match the configured security token if WEBHOOK_VERIFY_TOKEN is set.
    Bypassed if no verification token is configured in environment.
    """
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN")
    if not verify_token:
        return

    token_in_query = request.query_params.get("token")
    auth_header = request.headers.get("Authorization", "")

    if token_in_query != verify_token and auth_header != f"Bearer {verify_token}":
        logger.warning("Unauthorized webhook request: invalid verification token.")
        raise HTTPException(status_code=403, detail="Unauthorized webhook request.")
