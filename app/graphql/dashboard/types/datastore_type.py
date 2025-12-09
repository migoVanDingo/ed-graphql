# app/graphql/dashboard/types/datastore_type.py

from datetime import datetime
from typing import Optional

import strawberry


@strawberry.type
class DatastoreFileType:
    id: str
    filename: str
    content_type: str
    size: int
    created_at: datetime


@strawberry.type
class DatastoreFileTypeBreakdownType:
    content_type: str
    file_count: int
    total_bytes: int


@strawberry.type
class DatastoreFileCategoryBreakdownType:
    # e.g. "csv", "json", "mp4", "wav", "audio", "video", "other"
    category: str

    # if you want to show the underlying MIME types in a tooltip, etc.
    content_types: List[str]

    file_count: int
    total_bytes: int


@strawberry.type
class DatastoreMetricsType:
    capacity_bytes: Optional[BigInt]
    used_bytes: BigInt
    free_bytes: Optional[BigInt]
    used_percent: Optional[float]

    file_count: int
    last_upload_at: Optional[datetime]

    # ← changed to category-based breakdown:
    by_category: List[DatastoreFileCategoryBreakdownType]


@strawberry.type
class DatastoreFilesPageType:
    items: List[DatastoreFileType]
    total_count: int
    # simple offset-based pagination for now
    limit: int
    offset: int


@strawberry.type
class DatastoreType:
    id: str
    name: str
    description: Optional[str]
    created_at: datetime

    @strawberry.field
    async def metrics(self, info) -> DatastoreMetricsType:
        from app.resolvers.datastore_resolvers import get_datastore_metrics

        return await get_datastore_metrics(info, datastore_id=self.id)

    @strawberry.field
    async def files(
        self,
        info,
        limit: int = 25,
        offset: int = 0,
    ) -> DatastoreFilesPageType:
        from app.resolvers.datastore_resolvers import get_datastore_files_page

        return await get_datastore_files_page(
            info,
            datastore_id=self.id,
            limit=limit,
            offset=offset,
        )
