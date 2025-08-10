import strawberry
from typing import AsyncGenerator, Optional
from app.internal.event_bus import bus
from app.graphql.types import UserChange
from platform_common.logging.logging import get_logger

logger = get_logger("graphql_subscriptions")


@strawberry.type
class Query:
    hello: str = "ok"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def user_created(self) -> AsyncGenerator[UserChange, None]:
        try:
            async for msg in bus.subscribe("user_created"):
                yield UserChange(operation=msg.get("operation", ""), payload=msg)
        except Exception as e:
            logger.error("user_created generator crashed: %r", e, exc_info=True)
            raise  # let Strawberry surface it

    @strawberry.subscription
    async def user_updated(self) -> AsyncGenerator[UserChange, None]:
        try:
            async for msg in bus.subscribe("user_updated"):
                yield UserChange(operation=msg.get("operation", ""), payload=msg)
        except Exception as e:
            logger.error("user_updated generator crashed: %r", e, exc_info=True)
            raise  # let Strawberry surface it

    @strawberry.subscription
    async def user_deleted(self) -> AsyncGenerator[UserChange, None]:
        try:
            async for msg in bus.subscribe("user_deleted"):
                yield UserChange(operation=msg.get("operation", ""), payload=msg)
        except Exception as e:
            logger.error("user_deleted generator crashed: %r", e, exc_info=True)
            raise  # let Strawberry surface it

    # Optional: a single stream for *all* user events with a filter arg
    @strawberry.subscription
    async def user_changes(
        self, op: Optional[str] = None
    ) -> AsyncGenerator[UserChange, None]:
        # Fan-in by listening to all 3 queues. Simple way: loop over one combined stream.
        # Minimal approach: pick a default stream and rely on the catch-all in the bridge.
        # For a true combined stream you’d run multiple tasks; keeping it simple for v1:
        keys = (op.lower(),) if op else ("user_created", "user_updated", "user_deleted")
        # round-robin: await on each queue in order (okay for low volume)
        while True:
            for k in keys:
                msg = await anext(
                    bus.subscribe(k)
                )  # Python 3.10+: helper to get next item
                yield UserChange(operation=msg.get("operation", ""), payload=msg)


schema = strawberry.Schema(query=Query, subscription=Subscription)
