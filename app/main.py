from app.debug.start_raw_tap import start_raw_tap
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from app.pubsub.user_changes_subscriber import start_user_changes_subscriber
from app.api.controller.health_check import router as health_router
from app.graphql.context import get_context

from platform_common.logging.logging import get_logger
from app.graphql.root_schema import schema
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL


logger = get_logger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GraphQL service starting lifespan…")
    task = asyncio.create_task(start_user_changes_subscriber())
    # tap_task = asyncio.create_task(start_raw_tap())
    app.state.user_changes_task = task
    try:
        yield
    finally:
        logger.info("GraphQL service shutting down lifespan…")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info("Subscriber task cancelled cleanly.")


app = FastAPI(title="GraphQL Service", lifespan=lifespan)


graphql_app = GraphQLRouter(
    schema,
    graphiql=True,
    subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL],
    context_getter=get_context,
)


# REST endpoints
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(graphql_app, prefix="/graphql")
