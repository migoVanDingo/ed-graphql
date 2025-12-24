# app/graphql/schema/dataset_schema.py

import strawberry
from typing import Optional, List
from datetime import datetime
from strawberry.types import Info

from platform_common.db.dal.dataset_item_dal import DatasetItemDAL
from platform_common.models.dataset import Dataset
from platform_common.models.project_dataset_link import ProjectDatasetLink
from platform_common.utils.time_helpers import to_datetime_utc
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
    datastore_id: strawberry.ID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    # -----------------------------------
    # Resolver: dataset → items
    # -----------------------------------
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

    # -----------------------------------
    # (Optional) Resolver: dataset → projects
    # -----------------------------------
    @strawberry.field
    async def projects(
        self,
        info: Info[GraphQLContext, None],
    ) -> List[
        strawberry.LazyType["ProjectType", "app.graphql.dashboard.types.project_type"]
    ]:
        dataset_model: Dataset = await info.context.dataset_dal.get(self.id)
        return [
            ProjectType.from_model(link.project) for link in dataset_model.project_links
        ]

    # -----------------------------------
    # Factory method
    # -----------------------------------
    @staticmethod
    def from_model(model: Dataset) -> "DatasetType":
        return DatasetType(
            id=model.id,
            datastore_id=model.datastore_id,
            name=model.name,
            description=model.description,
            created_at=to_datetime_utc(model.created_at),
            updated_at=to_datetime_utc(model.updated_at),
        )


@strawberry.input
class CreateDatasetInput:
    """
    NOTE:
    You CAN keep project_id as an input if you want convenience creation.
    That does NOT mean Dataset has a project_id column — it simply means:
    - create dataset
    - auto-create a ProjectDatasetLink row
    """

    project_id: Optional[strawberry.ID] = None
    datastore_id: strawberry.ID
    name: str
    description: Optional[str] = None
