# app/graphql/root_schema.py
import strawberry

from app.graphql.dashboard.query import DashboardQuery
from app.graphql.dashboard.subscription import Subscription as DashboardSubscription
from app.graphql.dashboard.mutation import DashboardMutation
from app.graphql.dashboard.types.project_type import ProjectType
from app.graphql.schema.dataset_schema import DatasetType
from app.graphql.dashboard.types.user_type import UserType


@strawberry.type
class Query(DashboardQuery):
    """Root Query type."""

    pass


@strawberry.type
class Subscription(DashboardSubscription):
    """Root Subscription type."""

    pass


@strawberry.type
class Mutation(DashboardMutation):
    """Root Mutation type."""

    pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,  # ⬅️ this is the important new line
    subscription=Subscription,
)
