import asyncio
from collections import defaultdict
from typing import Any, Dict, AsyncIterator


class EventBus:
    """
    Simple in-memory async pub/sub keyed by event name.
    Not durable (process memory only) but perfect for bridging Redis to GQL.
    """

    def __init__(self, maxsize: int = 256):
        self._queues: Dict[str, asyncio.Queue] = defaultdict(
            lambda: asyncio.Queue(maxsize=maxsize)
        )
        self._lock = asyncio.Lock()

    async def publish(self, key: str, message: Any) -> None:
        # Never block the subscriber; if full, drop the oldest then enqueue.
        q = self._queues[key]
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            try:
                q.get_nowait()  # drop oldest
                q.task_done()
            except Exception:
                pass
            q.put_nowait(message)

    async def subscribe(self, key: str) -> AsyncIterator[Any]:
        """
        Async iterator that yields messages for `key`.
        IMPORTANT: each iterator has its own view of the queue's stream.
        """
        q = self._queues[key]
        while True:
            item = await q.get()
            try:
                yield item
            finally:
                q.task_done()


# Global singleton
bus = EventBus(maxsize=512)
