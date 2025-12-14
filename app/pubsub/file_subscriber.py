# app/pubsub/file_status_subscriber.py

from typing import Any, Dict

from platform_common.config.settings import get_settings
from platform_common.logging.logging import get_logger
from platform_common.pubsub.factory import get_subscriber
from platform_common.pubsub.event import PubSubEvent
from platform_common.utils.time_helpers import parse_occurred_at_string

from app.graphql.dashboard.subscription import (
    FileStatusEvent,
    push_file_status_event_to_clients,
)

logger = get_logger("graphql.file_status_subscriber")
settings = get_settings()

# Must match the pubsub_topic in ed-database-management's listen_to_file_status_changes()
FILE_STATUS_TOPIC = "file:status"


async def _handle_file_status_event(event: PubSubEvent) -> None:
    payload: Dict[str, Any] = event.payload or {}

    file_id = payload.get("file_id")
    datastore_id = payload.get("datastore_id")
    upload_session_id = payload.get("upload_session_id")
    old_status = payload.get("old_status")
    new_status = payload.get("new_status")
    raw_occurred_at = payload.get("occurred_at")

    if not file_id or not datastore_id:
        logger.warning(
            "file status event missing file_id or datastore_id: %r",
            payload,
        )
        return

    occurred_at = parse_occurred_at_string(raw_occurred_at)

    logger.info(
        "Received file status change %s -> %s for file=%s datastore=%s",
        old_status,
        new_status,
        file_id,
        datastore_id,
    )

    event_obj = FileStatusEvent(
        file_id=file_id,
        datastore_id=datastore_id,
        upload_session_id=upload_session_id,
        old_status=old_status,
        new_status=new_status,
        occurred_at=occurred_at,  # 👈 now a real datetime
    )

    await push_file_status_event_to_clients(event_obj)


async def start_file_status_subscriber() -> None:
    """
    Entrypoint used by FastAPI lifespan: subscribe to Redis topic
    `file:status` and dispatch all events to _handle_file_status_event.
    """
    subscriber = get_subscriber()

    topic_handlers = {
        FILE_STATUS_TOPIC: {
            "*": _handle_file_status_event,
        }
    }

    logger.info(
        "Starting Redis subscription for file status events on topic '%s'",
        FILE_STATUS_TOPIC,
    )

    # This runs until cancelled by lifespan
    await subscriber.subscribe(topic_handlers)
