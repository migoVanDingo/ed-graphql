# app/graphql/dashboard/subscription.py
from typing import AsyncGenerator, Dict, List, Optional
import asyncio
from datetime import datetime

import strawberry
from strawberry.types import Info
from graphql import GraphQLError

from platform_common.logging.logging import get_logger
from app.utils.db_helpers import get_datastore_dal
from app.graphql.dashboard.types import DatastoreType

logger = get_logger("graphql_dashboard_subscription")

# ─────────────────────────────────────────
# Existing datastore subscription state
# ─────────────────────────────────────────

_DATASTORE_SUBSCRIBERS: Dict[str, List[asyncio.Queue[None]]] = {}


async def push_datastore_update_to_clients(datastore_id: str) -> None:
    queues = _DATASTORE_SUBSCRIBERS.get(datastore_id, [])
    if not queues:
        return

    logger.debug(
        "Notifying %d subscribers for datastore_id=%s",
        len(queues),
        datastore_id,
    )

    for q in list(queues):
        await q.put(None)


def _register_datastore_subscriber(
    datastore_id: str, queue: asyncio.Queue[None]
) -> None:
    _DATASTORE_SUBSCRIBERS.setdefault(datastore_id, []).append(queue)


def _unregister_datastore_subscriber(
    datastore_id: str, queue: asyncio.Queue[None]
) -> None:
    queues = _DATASTORE_SUBSCRIBERS.get(datastore_id)
    if not queues:
        return
    try:
        queues.remove(queue)
    except ValueError:
        pass
    if not queues:
        _DATASTORE_SUBSCRIBERS.pop(datastore_id, None)


async def _fetch_datastore_snapshot(datastore_id: str):
    """
    Open a new DAL/session and fetch the latest *active* datastore.
    Metrics will be resolved by DatastoreType field resolvers.
    """
    async with get_datastore_dal() as datastore_dal:
        ds = await datastore_dal.get_active(datastore_id)
        if ds is None:
            raise GraphQLError(f"Datastore {datastore_id} not found or inactive")
        return ds


# ─────────────────────────────────────────
# NEW: file status subscription state
# ─────────────────────────────────────────


@strawberry.type
class FileStatusEvent:
    file_id: strawberry.ID
    datastore_id: strawberry.ID
    upload_session_id: Optional[strawberry.ID]
    old_status: str
    new_status: str
    occurred_at: datetime


# per-datastore list of queues that carry FileStatusEvent
_FILE_STATUS_SUBSCRIBERS: Dict[str, List[asyncio.Queue[FileStatusEvent]]] = {}


async def push_file_status_event_to_clients(event: FileStatusEvent) -> None:
    """
    Called by the Redis subscriber when a file:status message arrives.
    It fans out the event to all subscribers for this datastore.
    """
    datastore_id = str(event.datastore_id)
    queues = _FILE_STATUS_SUBSCRIBERS.get(datastore_id, [])
    if not queues:
        return

    logger.debug(
        "Pushing file event to %d subscribers for datastore_id=%s",
        len(queues),
        datastore_id,
    )

    for q in list(queues):
        await q.put(event)


def _register_file_status_subscriber(
    datastore_id: str, queue: asyncio.Queue[FileStatusEvent]
) -> None:
    _FILE_STATUS_SUBSCRIBERS.setdefault(datastore_id, []).append(queue)


def _unregister_file_status_subscriber(
    datastore_id: str, queue: asyncio.Queue[FileStatusEvent]
) -> None:
    queues = _FILE_STATUS_SUBSCRIBERS.get(datastore_id)
    if not queues:
        return
    try:
        queues.remove(queue)
    except ValueError:
        pass
    if not queues:
        _FILE_STATUS_SUBSCRIBERS.pop(datastore_id, None)


@strawberry.type
class Subscription:

    # Datastore
    @strawberry.subscription
    async def datastore_updated(
        self,
        datastore_id: strawberry.ID,
        info: Info,
    ) -> AsyncGenerator[DatastoreType, None]:
        datastore_id_str = str(datastore_id)

        # 1 Initial snapshot
        ds = await _fetch_datastore_snapshot(datastore_id_str)

        initial_payload = DatastoreType(
            id=ds.id,
            name=ds.name,
            description=ds.description,
            created_at=ds.created_at,
        )

        yield initial_payload

        # 2 Subscribe to further updates
        queue: asyncio.Queue[None] = asyncio.Queue()
        _register_datastore_subscriber(datastore_id_str, queue)

        try:
            while True:
                await queue.get()  # wait for push_datastore_update_to_clients()

                ds = await _fetch_datastore_snapshot(datastore_id_str)

                next_payload = DatastoreType(
                    id=ds.id,
                    name=ds.name,
                    description=ds.description,
                    created_at=ds.created_at,
                )

                yield next_payload
        finally:
            _unregister_datastore_subscriber(datastore_id_str, queue)

    # NEW: File status subscription
    @strawberry.subscription
    async def file_status_updated(
        self,
        datastore_id: strawberry.ID,
        upload_session_id: Optional[strawberry.ID],
        info: Info,
    ) -> AsyncGenerator[FileStatusEvent, None]:
        """
        Stream per-file status changes for a given datastore.
        Optionally filter by upload_session_id.
        """
        datastore_id_str = str(datastore_id)
        upload_session_id_str = str(upload_session_id) if upload_session_id else None

        # No initial snapshot; we only stream changes
        queue: asyncio.Queue[FileStatusEvent] = asyncio.Queue()
        _register_file_status_subscriber(datastore_id_str, queue)

        try:
            while True:
                event = await queue.get()

                if (
                    upload_session_id_str
                    and str(event.upload_session_id) != upload_session_id_str
                ):
                    continue

                yield event
        finally:
            _unregister_file_status_subscriber(datastore_id_str, queue)
