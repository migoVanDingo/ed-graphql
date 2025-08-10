# app/debug/raw_tap.py
import json
import asyncio
from redis.asyncio import Redis
from platform_common.config.settings import get_settings
from platform_common.logging.logging import get_logger

logger = get_logger("raw_tap")
settings = get_settings()

CHANNEL = "user:changes"


async def start_raw_tap():
    r = Redis.from_url(
        getattr(settings, "redis_url_effective", settings.redis_url),
        encoding="utf-8",
        decode_responses=True,
    )
    ps = r.pubsub()
    await ps.subscribe(CHANNEL)
    logger.info("[raw-tap] Subscribed to %s", CHANNEL)
    try:
        async for msg in ps.listen():
            if msg.get("type") != "message":
                continue
            logger.info(
                "[raw-tap] channel=%s raw=%s", msg.get("channel"), msg.get("data")
            )
    finally:
        await ps.unsubscribe(CHANNEL)
        await ps.close()
        await r.close()
