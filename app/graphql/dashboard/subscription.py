from typing import AsyncGenerator, Dict, List
import asyncio

import strawberry

from platform_common.db.dal.datastore_dal import DatastoreDAL
from platform_common.logging.logging import get_logger

from app.graphql.dashboard.types import DatastoreType

logger = get_logger("graphql_dashboard_subscription")


# key: datastore_id, value: list[asyncio.Queue[None]]
_DATASTORE_SUBSCRIBERS: Dict[str, List[asyncio.Queue]] = {}


async def publish_datastore_update(datastore_id: str) -> None:
    """
    Call this whenever datastore content changes (e.g. after file upload).

    We don't send the metrics themselves; metrics are always recomputed
    via DatastoreDAL.get_datastore_with_metrics inside the subscription,
    so this stays consistent with your existing dashboard query.
    """
    queues = _DATASTORE_SUBSCRIBERS.get(datastore_id, [])
    if not queues:
        return

    logger.debug(
        "Notifying %d subscribers for datastore_id=%s",
        len(queues),
        datastore_id,
    )

    for q in queues:
        await q.put(None)  # just a wake-up signal


def _register_datastore_subscriber(datastore_id: str, queue: asyncio.Queue) -> None:
    _DATASTORE_SUBSCRIBERS.setdefault(datastore_id, []).append(queue)


def _unregister_datastore_subscriber(datastore_id: str, queue: asyncio.Queue) -> None:
    queues = _DATASTORE_SUBSCRIBERS.get(datastore_id)
    if not queues:
        return
    try:
        queues.remove(queue)
    except ValueError:
        pass
    if not queues:
        _DATASTORE_SUBSCRIBERS.pop(datastore_id, None)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def datastore_updated(
        self,
        datastore_id: strawberry.ID,
        info: strawberry.types.Info,
    ) -> AsyncGenerator[DatastoreType, None]:
        """
        Stream updates for a specific datastore.

        - First payload: the current snapshot (computed from DAL).
        - Subsequent payloads: new snapshots whenever publish_datastore_update()
          is called for this datastore_id.
        """
        datastore_dal: DatastoreDAL = info.context["datastore_dal"]
        ds = await datastore_dal.get_datastore_with_metrics(str(datastore_id))

        # 1) initial snapshot
        yield DatastoreType(
            id=ds.id,
            name=ds.name,
            description=ds.description,
            created_at=ds.created_at,
            # TODO: add your metrics fields here, e.g.:
            # used_bytes=ds.used_bytes,
            # capacity_bytes=ds.capacity_bytes,
            # free_bytes=ds.free_bytes,
            # file_count=ds.file_count,
        )

        # 2) subscribe to further updates
        queue: asyncio.Queue = asyncio.Queue()
        _register_datastore_subscriber(str(datastore_id), queue)

        try:
            while True:
                # wait for a signal
                await queue.get()

                # recompute metrics fresh each time
                ds = await datastore_dal.get_datastore_with_metrics(str(datastore_id))

                yield DatastoreType(
                    id=ds.id,
                    name=ds.name,
                    description=ds.description,
                    created_at=ds.created_at,
                    # same metrics fields here as above
                )
        finally:
            _unregister_datastore_subscriber(str(datastore_id), queue)
