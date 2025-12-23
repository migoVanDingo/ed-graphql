# app/graphql/schema/dataset_schema.py
import strawberry
from typing import Optional, List
from datetime import datetime
from strawberry.types import Info

from platform_common.db.dal.dataset_item_dal import DatasetItemDAL
from app.graphql.context import GraphQLContext


@strawberry.type
class DatasetItemType:
    id: strawberry.ID
    dataset_id: strawberry.ID
    file_id: strawberry.ID
    created_at: datetime
    status: Optional[str] = None


@strawberry.type
class DatasetType:
    id: strawberry.ID
    org_id: strawberry.ID
    datastore_id: strawberry.ID
    project_id: Optional[strawberry.ID]
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    async def items(
        self,
        info: Info[GraphQLContext, None],
    ) -> List[DatasetItemType]:
        ctx = info.context
        dataset_item_dal: DatasetItemDAL = ctx.dataset_item_dal
        items = await dataset_item_dal.list_by_dataset_id(str(self.id))
        return [
            DatasetItemType(
                id=item.id,
                dataset_id=item.dataset_id,
                file_id=item.file_id,
                created_at=item.created_at,
                status=getattr(item, "status", None),
            )
            for item in items
        ]


@strawberry.input
class CreateDatasetInput:
    project_id: Optional[strawberry.ID] = None
    datastore_id: strawberry.ID
    name: str
    description: Optional[str] = None
