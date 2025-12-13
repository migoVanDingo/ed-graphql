from app.debug.start_raw_tap import start_raw_tap
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from app.pubsub.user_changes_subscriber import start_user_changes_subscriber
from app.api.controller.health_check import router as health_router
from app.graphql.context import get_context
from fastapi.middleware.cors import CORSMiddleware
from platform_common.logging.logging import get_logger
from app.graphql.root_schema import schema
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from app.pubsub.upload_session_status_subscriber import (
    start_upload_session_status_subscriber,
)

logger = get_logger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GraphQL service starting lifespan…")

    # Start user changes subscriber
    user_task = asyncio.create_task(start_user_changes_subscriber())
    app.state.user_changes_task = user_task

    # Start upload_session status subscriber
    upload_session_task = asyncio.create_task(start_upload_session_status_subscriber())
    app.state.upload_session_status_task = upload_session_task

    # tap_task = asyncio.create_task(start_raw_tap())

    try:
        yield
    finally:
        logger.info("GraphQL service shutting down lifespan…")

        # Stop user changes subscriber
        user_task.cancel()
        try:
            await user_task
        except asyncio.CancelledError:
            logger.info("User changes subscriber task cancelled cleanly.")

        # Stop upload_session status subscriber
        upload_session_task.cancel()
        try:
            await upload_session_task
        except asyncio.CancelledError:
            logger.info("Upload session status subscriber task cancelled cleanly.")


app = FastAPI(title="GraphQL Service", lifespan=lifespan)

# Allowed origins for your frontend(s)
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # if you ever use CRA/Next
    # add any others you actually use
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # you're using cookies
    allow_methods=["*"],  # or ["GET", "POST"] if you want to be strict
    allow_headers=["*"],  # allow Content-Type, etc.
)


graphql_app = GraphQLRouter(
    schema=schema,
    graphiql=True,
    subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL],
    context_getter=get_context,
)


# REST endpoints
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(graphql_app, prefix="/graphql")
