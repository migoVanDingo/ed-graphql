from typing import Any, Dict

from platform_common.config.settings import get_settings
from platform_common.logging.logging import get_logger
from platform_common.pubsub.factory import get_subscriber
from platform_common.pubsub.event import PubSubEvent

from app.graphql.dashboard.subscription import (
    push_datastore_update_to_clients,
)

logger = get_logger("graphql.upload_session_status_subscriber")
settings = get_settings()

# Must match the pubsub_topic in ed-database-management's listen_to_upload_session_changes()
UPLOAD_SESSION_TOPIC = "upload_session:status"


async def _handle_upload_session_status_event(event: PubSubEvent) -> None:
    """
    Handle upload_session status change events coming from Redis.

    event.payload is whatever the Postgres trigger sent via pg_notify,
    then wrapped by ed-database-management's listen_to_pg_channel.
    """
    payload: Dict[str, Any] = event.payload or {}

    status = payload.get("status")
    datastore_id = payload.get("datastore_id")

    if not datastore_id:
        logger.warning(
            "upload_session status event missing datastore_id: %r",
            payload,
        )
        return

    # Only act on terminal states per our design
    if status not in ("ready", "failed"):
        logger.debug(
            "Ignoring upload_session status=%s for datastore=%s",
            status,
            datastore_id,
        )
        return

    logger.info(
        "Received upload_session status=%s for datastore=%s; pushing update to clients",
        status,
        datastore_id,
    )

    await push_datastore_update_to_clients(datastore_id)


async def start_upload_session_status_subscriber() -> None:
    """
    Entrypoint used by FastAPI lifespan: subscribe to Redis topic
    `upload_session:status` and dispatch all events to
    _handle_upload_session_status_event.
    """
    subscriber = get_subscriber()

    # topic_handlers structure:
    # {
    #   "topic_name": {
    #       "normalized_event_type": async_handler,
    #       "*": async_catch_all_handler,
    #   }
    # }
    #
    # We don't care about event_type here, we want *all* events on this topic,
    # so we use "*" as a catch-all.
    topic_handlers = {
        UPLOAD_SESSION_TOPIC: {
            "*": _handle_upload_session_status_event,
        }
    }

    logger.info(
        "Starting Redis subscription for upload_session status events on topic '%s'",
        UPLOAD_SESSION_TOPIC,
    )

    # This runs until cancelled by lifespan
    await subscriber.subscribe(topic_handlers)
