# app/graphql/root_schema.py

import strawberry

from app.graphql.user_schema import Subscription as UserSub
from app.graphql.debug_schema import Subscription as DebugSub
from app.graphql.dashboard_schema import DashboardQuery
from platform_common.errors.graphql import PlatformErrorExtension


# Combine subscriptions by multiple inheritance
@strawberry.type
class Subscription(UserSub, DebugSub):
    pass


# Combine queries
@strawberry.type
class Query(DashboardQuery):
    hello: str = "ok"


schema = strawberry.Schema(
    query=Query,
    subscription=Subscription,
    # Use our error extension to format PlatformError subclasses
    extensions=[PlatformErrorExtension()],
)
