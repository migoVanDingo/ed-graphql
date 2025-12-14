# app/graphql/context.py
from fastapi import Request, WebSocket
from app.auth.get_current_user import get_current_user_from_request
from platform_common.logging.logging import get_logger

logger = get_logger("graphql_context")


async def get_context(
    request: Request = None,
    websocket: WebSocket = None,
):
    """
    Build the Strawberry GraphQL context for both HTTP and WebSocket.

    - For HTTP queries/mutations, FastAPI injects `request`.
    - For WebSocket subscriptions, FastAPI injects `websocket`.
    """
    # HTTP path: normal auth
    if request is not None:
        auth_info = await get_current_user_from_request(request)
        user = auth_info["user"]

        logger.debug(f"GraphQL HTTP context built for user_id={user.id}")

        return {
            "request": request,
            "current_user": user,
            "session_id": auth_info["session_id"],
        }

    # WebSocket path: for now, no auth helper — just minimal context
    if websocket is not None:
        logger.debug("GraphQL WS context built without user auth (TODO)")

        return {
            "request": websocket,
            "current_user": None,
            "session_id": None,
        }

    # Should never happen
    raise RuntimeError("get_context called without request or websocket")
