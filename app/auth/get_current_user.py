# app/auth/dependencies.py

from fastapi import Request
from platform_common.auth.jwt_utils import decode_jwt
from platform_common.db.dal.user_dal import UserDAL
from platform_common.db.session import get_session
from platform_common.errors.base import AuthError, NotFoundError
from platform_common.logging.logging import get_logger

logger = get_logger("graphql_auth")


async def get_current_user_from_request(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        logger.info("No access_token cookie present on GraphQL request")
        raise AuthError("Not authenticated")

    try:
        payload = decode_jwt(access_token)
    except Exception as e:
        logger.warning(f"Failed to decode access token in GraphQL: {e}")
        raise AuthError("Invalid or expired token")

    user_id = payload.get("sub")
    session_id = payload.get("session_id")

    if not user_id:
        logger.error("JWT payload missing 'sub' (user_id)")
        raise AuthError("Invalid token payload")

    # 🔑 Use get_session as an async generator
    async for session in get_session():
        user_dal = UserDAL(session)
        user = await user_dal.get_by_id(user_id)
        # get_session will close the session when we break out
        break

    if not user:
        logger.error(f"User not found in GraphQL for user_id={user_id}")
        raise NotFoundError("User not found")

    return {
        "user": user,
        "session_id": session_id,
        "token_payload": payload,
    }
