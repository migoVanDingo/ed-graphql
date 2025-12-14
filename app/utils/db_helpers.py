# app/graphql/db_helpers.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from platform_common.db.session import get_session  # FastAPI-style async generator
from platform_common.db.dal.datastore_dal import DatastoreDAL


@asynccontextmanager
async def get_datastore_dal() -> AsyncGenerator[DatastoreDAL, None]:
    """
    Wrap the FastAPI-style get_session() async generator so we can use it
    as an async context manager in GraphQL code.
    """
    agen = get_session()
    session = await agen.__anext__()  # get the yielded session

    try:
        dal = DatastoreDAL(session)
        yield dal
    finally:
        # Exhaust the generator so its "finally" block runs and closes the session
        try:
            await agen.__anext__()
        except StopAsyncIteration:
            pass
