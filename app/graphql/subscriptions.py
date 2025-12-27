# app/graphql/subscriptions.py
import asyncio
import strawberry
from typing import AsyncGenerator, Optional

from platform_common.logging.logging import get_logger
from platform_common.pubsub.factory import get_subscriber
from platform_common.pubsub.event import PubSubEvent

logger = get_logger("graphql_subscriptions")


@strawberry.type
class DatasetUpdatedEvent:
    dataset_id: str
    reason: str
    operation: str
    file_id: Optional[str] = None
    role: Optional[str] = None


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def datasetUpdated(
        self,
        info,
        datasetId: strawberry.ID,
    ) -> AsyncGenerator[DatasetUpdatedEvent, None]:
        user = info.context["current_user"]
        dsid = str(datasetId)

        logger.info("datasetUpdated started user_id=%s dataset_id=%s", user.id, dsid)

        subscriber = get_subscriber()
        q: asyncio.Queue[DatasetUpdatedEvent] = asyncio.Queue()

        async def on_any(event: PubSubEvent):
            p = event.payload or {}
            if p.get("dataset_id") != dsid:
                return

            await q.put(
                DatasetUpdatedEvent(
                    dataset_id=dsid,
                    reason=str(p.get("event_name") or "DATASET_FILES_CHANGED").lower(),
                    operation=str(p.get("operation") or ""),
                    file_id=p.get("file_id"),
                    role=p.get("role"),
                )
            )

        # Run Redis subscription in background
        sub_task = asyncio.create_task(
            subscriber.subscribe({"dataset:updated": {"*": on_any}})
        )

        try:
            while True:
                yield await q.get()
        finally:
            sub_task.cancel()
            try:
                await sub_task
            except asyncio.CancelledError:
                pass
            logger.info("datasetUpdated closed user_id=%s dataset_id=%s", user.id, dsid)
