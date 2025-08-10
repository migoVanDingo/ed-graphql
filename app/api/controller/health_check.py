# app/api/controller/health_check.py
from fastapi import APIRouter, Request
from platform_common.logging.logging import get_logger, set_request_context
from platform_common.config.settings import get_settings
from platform_common.pubsub.factory import get_subscriber
from redis.asyncio import Redis

router = APIRouter()
logger = get_logger("health")


@router.get("/")
async def health_check(request: Request):
    # Optional: bind request-specific info
    set_request_context(
        request_id=str(request.headers.get("x-request-id", "unknown")),
        user_id="test-user",
        session_id="abc123",
    )

    logger.info("Health check successful!", path=request.url.path)

    s = get_settings()
    url = getattr(s, "redis_url_effective", s.redis_url)
    ok = None
    try:
        r = Redis.from_url(url, encoding="utf-8", decode_responses=True)
        ok = await r.ping()  # -> True if reachable
        await r.close()
    except Exception as e:
        ok = f"error: {e!r}"
    return {
        "service": "ed-graphql",
        "redis_url": url,
        "redis_ping": ok,
        "channel": "user:changes",
    }
