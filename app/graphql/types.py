import strawberry
from strawberry.scalars import JSON


@strawberry.type
class UserChange:
    # Derived from your trigger payload
    operation: str  # "INSERT" | "UPDATE" | "DELETE"
    payload: JSON  # full payload from the trigger (table, data, old_data)
