# app/graphql/context.py
from fastapi import Request
from app.auth.get_current_user import get_current_user_from_request
from platform_common.db.session import (
    get_session,
)  # adjust path if needed
from platform_common.logging.logging import get_logger

logger = get_logger("graphql_context")


async def get_context(request: Request):
    """
    Build the Strawberry GraphQL context.

    - Validates the access token and loads the current user.
    - Attaches a DB session if you want to use DALs directly in resolvers.
    """
    # This will raise HTTPException(401) if not authenticated.
    auth_info = await get_current_user_from_request(request)
    user = auth_info["user"]

    # Get async DB session via your platform_common helper
    # Depending on how get_session is defined, you might call it with `request`.
    db_session = await get_session(request)

    logger.debug(f"GraphQL context built for user_id={user.id}")

    return {
        "request": request,
        "current_user": user,
        "session_id": auth_info["session_id"],
        "db_session": db_session,
    }
