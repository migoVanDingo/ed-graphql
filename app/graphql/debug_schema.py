# app/graphql/schema.py
import strawberry
import asyncio


@strawberry.type
class Query:
    ok: str = "ok"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def ping(self) -> str:
        # proves WS + Strawberry are working
        yield "pong"
        await asyncio.sleep(0.1)
        yield "pong2"


schema = strawberry.Schema(query=Query, subscription=Subscription)
