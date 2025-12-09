# app/graphql/dashboard/types/dataset_type.py

from datetime import datetime
from typing import Optional

import strawberry


@strawberry.type
class DatasetType:
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
