import strawberry
from typing import Optional
from strawberry.types import Info

from app.graphql.context import GraphQLContext
from app.graphql.schema.dataset_schema import DatasetType


@strawberry.type
class DatasetQuery:
    @strawberry.field
    async def dataset(
        self,
        info: Info[GraphQLContext, None],
        id: strawberry.ID,
    ) -> Optional[DatasetType]:
        ctx = info.context

        model = await ctx.dataset_dal.get_by_id(str(id))
        if not model:
            return None

        return DatasetType.from_model(model)
