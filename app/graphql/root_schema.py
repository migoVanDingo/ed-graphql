import strawberry

from app.graphql.dashboard.query import DashboardQuery
from app.graphql.dashboard.subscription import Subscription as DashboardSubscription


@strawberry.type
class Query(DashboardQuery):
    """Root Query type."""

    pass


@strawberry.type
class Subscription(DashboardSubscription):
    """Root Subscription type."""

    pass


schema = strawberry.Schema(
    query=Query,
    subscription=Subscription,
    # mutation=None is implied if you omit it
)
