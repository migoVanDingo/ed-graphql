# app/graphql/root_schema.py
import strawberry
from strawberry.schema.config import StrawberryConfig

from app.graphql.user_schema import Subscription as UserSub
from app.graphql.debug_schema import Subscription as DebugSub
from app.graphql.dashboard_schema import DashboardQuery
from platform_common.errors.graphql import (
    custom_format_error,
)  # adjust path


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
    config=StrawberryConfig(
        error_formatter=custom_format_error,
        # you can keep defaults for other options
        # auto_camel_case=True, etc., if you want
    ),
)
