# app/graphql/user_schema.py
import strawberry
from typing import AsyncGenerator, Optional
from app.internal.event_bus import bus
from app.graphql.types import UserChange
from platform_common.logging.logging import get_logger

logger = get_logger("graphql_subscriptions")


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def user_created(self) -> AsyncGenerator[UserChange, None]:
        try:
            async for msg in bus.subscribe("user_created"):
                yield UserChange(operation=msg.get("operation", ""), payload=msg)
        except Exception as e:
            logger.error("user_created generator crashed: %r", e, exc_info=True)
            raise

    @strawberry.subscription
    async def user_updated(self) -> AsyncGenerator[UserChange, None]:
        try:
            async for msg in bus.subscribe("user_updated"):
                yield UserChange(operation=msg.get("operation", ""), payload=msg)
        except Exception as e:
            logger.error("user_updated generator crashed: %r", e, exc_info=True)
            raise

    @strawberry.subscription
    async def user_deleted(self) -> AsyncGenerator[UserChange, None]:
        try:
            async for msg in bus.subscribe("user_deleted"):
                yield UserChange(operation=msg.get("operation", ""), payload=msg)
        except Exception as e:
            logger.error("user_deleted generator crashed: %r", e, exc_info=True)
            raise

    @strawberry.subscription
    async def user_changes(
        self, op: Optional[str] = None
    ) -> AsyncGenerator[UserChange, None]:
        # NOTE: this is a bit hand-wavy as written; you might later refactor
        # it to fan-in properly. For now, we leave your logic.
        keys = (
            (op.lower(),)
            if op
            else (
                "user_created",
                "user_updated",
                "user_deleted",
            )
        )
        while True:
            for k in keys:
                msg = await anext(bus.subscribe(k))
                yield UserChange(operation=msg.get("operation", ""), payload=msg)
