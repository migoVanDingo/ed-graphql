# app/graphql/context.py
from fastapi import Request, WebSocket
from typing import TypedDict, Any, Optional

from app.auth.get_current_user import get_current_user_from_request
from platform_common.logging.logging import get_logger

# 🔽 NEW: imports for DB + DALs
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from platform_common.db.engine import get_engine
from platform_common.db.dal.dataset_dal import DatasetDAL
from platform_common.db.dal.dataset_item_dal import DatasetItemDAL
from platform_common.db.dal.project_dal import ProjectDAL
from platform_common.db.dal.file_dal import FileDAL

logger = get_logger("graphql_context")


class GraphQLContext(TypedDict):
    request: Any  # Request or WebSocket
    current_user: Any
    session_id: Optional[str]
    db_session: AsyncSession
    dataset_dal: DatasetDAL
    dataset_item_dal: DatasetItemDAL
    project_dal: ProjectDAL
    file_dal: FileDAL


# 🔽 NEW: helper to create an AsyncSession (using your engine pattern)
async def create_db_session() -> AsyncSession:
    engine = await get_engine()
    async_session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return async_session_factory()


async def get_context(
    request: Request = None,
    websocket: WebSocket = None,
) -> GraphQLContext:
    """
    Build the Strawberry GraphQL context for both HTTP and WebSocket.
    """
    if request is not None:
        auth_info = await get_current_user_from_request(request)
        user = auth_info["user"]

        # 🔽 NEW: create a DB session and DALs
        session = await create_db_session()

        logger.debug(f"GraphQL HTTP context built for user_id={user.id}")

        return {
            "request": request,
            "current_user": user,
            "session_id": auth_info["session_id"],
            "db_session": session,
            "dataset_dal": DatasetDAL(session),
            "dataset_item_dal": DatasetItemDAL(session),
            "project_dal": ProjectDAL(session),
            "file_dal": FileDAL(session),
        }

    if websocket is not None:
        # You can decide later how you want auth here
        session = await create_db_session()

        logger.debug("GraphQL WS context built without user auth (TODO)")

        return {
            "request": websocket,
            "current_user": None,
            "session_id": None,
            "db_session": session,
            "dataset_dal": DatasetDAL(session),
            "dataset_item_dal": DatasetItemDAL(session),
            "project_dal": ProjectDAL(session),
            "file_dal": FileDAL(session),
        }

    raise RuntimeError("get_context called without request or websocket")
