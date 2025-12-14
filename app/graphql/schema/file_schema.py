# app/graphql/file_schema.py (or similar)

import strawberry
from datetime import datetime
from typing import Optional


@strawberry.type
class FileStatusEvent:
    file_id: strawberry.ID
    datastore_id: strawberry.ID
    upload_session_id: Optional[strawberry.ID]
    old_status: str
    new_status: str
    occurred_at: datetime
