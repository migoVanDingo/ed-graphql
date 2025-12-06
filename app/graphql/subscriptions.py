# app/graphql/subscriptions.py

import strawberry
from typing import AsyncGenerator
from platform_common.logging.logging import get_logger

logger = get_logger("graphql_subscriptions")


@strawberry.type
class DatasetEventType:
    type: str  # "CREATED" | "UPDATED" | "DELETED"
    dataset_id: str
    dataset_name: str


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def datasetEvents(self, info) -> AsyncGenerator[DatasetEventType, None]:
        """
        Example subscription that yields dataset events for the current user/org.
        Wire this to your Redis/GCP Pub/Sub layer.
        """
        user = info.context["current_user"]
        logger.info(f"datasetEvents subscription started for user_id={user.id}")

        # This is pseudo-code. Replace with your actual pub/sub listener.
        channel = await subscribe_to_dataset_channel(user)  # you implement this

        try:
            async for msg in channel:
                # Map your internal message into DatasetEventType
                yield DatasetEventType(
                    type=msg["type"],
                    dataset_id=msg["dataset_id"],
                    dataset_name=msg.get("dataset_name", ""),
                )
        finally:
            await channel.close()
            logger.info(f"datasetEvents subscription closed for user_id={user.id}")
