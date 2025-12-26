# app/graphql/root_schema.py
import strawberry

from app.graphql.dashboard.query import DashboardQuery
from app.graphql.dashboard.subscription import Subscription as DashboardSubscription
from app.graphql.dashboard.mutation import DashboardMutation

from app.graphql.schema.query.dataset_query import DatasetQuery


@strawberry.type
class Query(DashboardQuery, DatasetQuery):
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
    mutation=Mutation,
    subscription=Subscription,
)
