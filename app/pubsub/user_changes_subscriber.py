import json
import asyncio
from platform_common.config.settings import get_settings
from platform_common.logging.logging import get_logger
from platform_common.pubsub.factory import get_subscriber
from platform_common.errors.base import ServiceUnavailableError
from app.internal.event_bus import bus

logger = get_logger("user_changes_subscriber")
settings = get_settings()

CHANNEL = "user:changes"


async def _forward_to_bus(event):
    # event.event_type is Enum-like; platform-common normalization gives "user_created" etc.
    event_key = getattr(event.event_type, "value", str(event.event_type)).lower()
    payload = event.payload  # already a dict from your trigger
    await bus.publish(event_key, payload)
    logger.info("[graphql-bridge] forwarded event=%s", event_key)


async def start_user_changes_subscriber():
    sub = get_subscriber()
    try:
        await sub.subscribe(
            {
                "user:changes": {
                    "user_created": _forward_to_bus,
                    "user_updated": _forward_to_bus,
                    "user_deleted": _forward_to_bus,
                    "*": _forward_to_bus,
                }
            }
        )
    except ConnectionError as e:
        # Could not connect to Redis
        raise ServiceUnavailableError(
            message=f"Redis subscriber connection failed: {e}", code="PUBSUB_ERROR"
        )
    except asyncio.CancelledError:
        close = getattr(sub, "close", None)
        if callable(close):
            await close()
        raise
    except Exception as e:
        # Catch any other unexpected pubsub crash
        raise ServiceUnavailableError(
            message=f"Unexpected subscriber failure: {e}", code="PUBSUB_ERROR"
        )
