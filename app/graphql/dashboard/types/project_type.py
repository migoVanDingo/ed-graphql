# app/graphql/dashboard/types/project_type.py

from typing import Optional
from datetime import datetime
import strawberry


@strawberry.type
class ProjectType:
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
