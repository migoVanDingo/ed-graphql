# app/resolvers/datastore_resolvers.py

from typing import Dict, List
from strawberry.types import Info

from platform_common.db.session import get_session
from platform_common.db.dal.file_dal import FileDAL
from platform_common.db.dal.datastore_dal import DatastoreDAL
from platform_common.utils.time_helpers import to_datetime_utc

from app.graphql.dashboard_schema import (
    DatastoreMetricsType,
    DatastoreFileCategoryBreakdownType,
    DatastoreFilesPageType,
    DatastoreFileType,
)


def classify_category_from_content_type(content_type: str) -> str:
    """
    Map MIME types into dashboard categories that match your FE:
    csv, json, mp4, wav, audio, video, other, etc.
    """
    ct = (content_type or "").lower()

    # csv
    if "csv" in ct:
        return "csv"

    # json
    if "json" in ct:
        return "json"

    # mp4
    if ct == "video/mp4":
        return "mp4"

    # wav
    if ct in ("audio/wav", "audio/x-wav", "audio/wave"):
        return "wav"

    # more generic buckets
    if ct.startswith("video/"):
        return "video"

    if ct.startswith("audio/"):
        return "audio"

    if ct == "application/pdf":
        return "pdf"

    if ct.startswith("image/"):
        return "image"

    return "other"


async def get_datastore_metrics(info: Info, datastore_id: str) -> DatastoreMetricsType:
    """
    Compute metrics for a datastore.
    """
    async for session in get_session():
        file_dal = FileDAL(session)
        datastore_dal = DatastoreDAL(session)

        aggregates = await file_dal.get_datastore_aggregate_metrics(datastore_id)
        content_type_rows = await file_dal.get_datastore_content_type_breakdown(
            datastore_id
        )
        capacity_bytes = await datastore_dal.get_datastore_capacity_bytes(datastore_id)

        break

    used_bytes = aggregates["used_bytes"]
    file_count = aggregates["file_count"]

    # aggregates["last_upload_at"] is currently an int (epoch seconds)
    raw_last_upload_at = aggregates["last_upload_at"]
    if raw_last_upload_at is not None:
        last_upload_at = to_datetime_utc(raw_last_upload_at)
    else:
        last_upload_at = None

    free_bytes = None
    used_percent = None
    if capacity_bytes is not None:
        free_bytes = max(capacity_bytes - used_bytes, 0)
        used_percent = (
            float(used_bytes) / float(capacity_bytes) * 100.0
            if capacity_bytes > 0
            else 0.0
        )

    buckets: Dict[str, Dict[str, object]] = {}

    for row in content_type_rows:
        ct = row["content_type"]
        category = classify_category_from_content_type(ct)

        if category not in buckets:
            buckets[category] = {
                "category": category,
                "content_types": set(),
                "file_count": 0,
                "total_bytes": 0,
            }

        bucket = buckets[category]
        bucket["content_types"].add(ct)
        bucket["file_count"] += row["file_count"]
        bucket["total_bytes"] += row["total_bytes"]

    by_category = [
        DatastoreFileCategoryBreakdownType(
            category=cat,
            content_types=sorted(list(data["content_types"])),
            file_count=data["file_count"],
            total_bytes=data["total_bytes"],
        )
        for cat, data in buckets.items()
    ]

    return DatastoreMetricsType(
        capacity_bytes=capacity_bytes,
        used_bytes=used_bytes,
        free_bytes=free_bytes,
        used_percent=used_percent,
        file_count=file_count,
        last_upload_at=last_upload_at,  # ← now a datetime or None
        by_category=by_category,
    )


async def get_datastore_files_page(
    info: Info,
    datastore_id: str,
    limit: int,
    offset: int,
) -> DatastoreFilesPageType:
    async for session in get_session():
        file_dal = FileDAL(session)
        page = await file_dal.get_datastore_files_page(
            datastore_id=datastore_id,
            limit=limit,
            offset=offset,
        )
        break

    items = page["items"]
    total_count = page["total_count"]

    gql_items: List[DatastoreFileType] = [
        DatastoreFileType(
            id=f.id,
            filename=f.filename,
            content_type=f.content_type,
            size=f.size,
            created_at=to_datetime_utc(f.created_at),  # ← convert here
        )
        for f in items
    ]

    return DatastoreFilesPageType(
        items=gql_items,
        total_count=total_count,
        limit=limit,
        offset=offset,
    )
