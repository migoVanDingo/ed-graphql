# app/graphql/root_schema.py
import strawberry
from app.graphql.user_schema import Subscription as UserSub
from app.graphql.debug_schema import Subscription as DebugSub


# Combine subscriptions by multiple inheritance
@strawberry.type
class Subscription(UserSub, DebugSub):
    pass


@strawberry.type
class Query:
    hello: str = "ok"


schema = strawberry.Schema(query=Query, subscription=Subscription)
