# app/graphql/context.py

from fastapi import Request
from app.auth.get_current_user import get_current_user_from_request
from platform_common.logging.logging import get_logger

logger = get_logger("graphql_context")


async def get_context(request: Request):
    auth_info = await get_current_user_from_request(request)
    user = auth_info["user"]

    logger.debug(f"GraphQL context built for user_id={user.id}")

    return {
        "request": request,
        "current_user": user,
        "session_id": auth_info["session_id"],
        # No db_session here; resolvers will open their own as needed
    }
