# app/graphql/context.py
from fastapi import Request, WebSocket
from typing import Any, Optional

from strawberry.fastapi.context import BaseContext


from app.auth.get_current_user import get_current_user_from_request
from platform_common.logging.logging import get_logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from platform_common.db.engine import get_engine

from platform_common.db.dal.dataset_dal import DatasetDAL
from platform_common.db.dal.dataset_item_dal import DatasetItemDAL
from platform_common.db.dal.project_dal import ProjectDAL
from platform_common.db.dal.file_dal import FileDAL

logger = get_logger("graphql_context")


class GraphQLContext(BaseContext):
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)

    # ✅ allow dict-style access: ctx["current_user"]
    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    # optional convenience
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


async def create_db_session() -> AsyncSession:
    engine = await get_engine()
    async_session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return async_session_factory()


async def get_context(request: Request = None, websocket: WebSocket = None):
    session = await create_db_session()
    try:
        if request is not None:
            auth_info = await get_current_user_from_request(request)
            user = auth_info["user"]
            yield GraphQLContext(
                request=request,
                current_user=user,
                session_id=auth_info["session_id"],
                db_session=session,
                dataset_dal=DatasetDAL(session),
                dataset_item_dal=DatasetItemDAL(session),
                project_dal=ProjectDAL(session),
                file_dal=FileDAL(session),
            )
            return

        if websocket is not None:
            yield GraphQLContext(
                request=websocket,
                current_user=None,
                session_id=None,
                db_session=session,
                dataset_dal=DatasetDAL(session),
                dataset_item_dal=DatasetItemDAL(session),
                project_dal=ProjectDAL(session),
                file_dal=FileDAL(session),
            )
            return

        raise RuntimeError("get_context called without request or websocket")
    finally:
        await session.close()
