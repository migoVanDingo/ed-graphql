# app/graphql/dashboard/types/organization_type.py

from datetime import datetime
from typing import Optional

import strawberry


@strawberry.type
class OrganizationType:
    id: str
    name: str
    # Adjust these fields to whatever your Organization model actually has
    description: Optional[str]
    created_at: datetime
