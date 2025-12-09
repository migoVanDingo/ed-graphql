import strawberry

from platform_common.models.user import User as UserModel
from platform_common.errors.base import ForbiddenError
from platform_common.logging.logging import get_logger

from app.graphql.dashboard.types import UserType

logger = get_logger("graphql_dashboard_query")


@strawberry.type
class DashboardQuery:
    """
    Root fields for the dashboard.

    This class is meant to be mixed into your root Query via multiple
    inheritance in `root_schema.py`, e.g.:

        @strawberry.type
        class Query(DashboardQuery):
            hello: str = "ok"
    """

    @strawberry.field
    async def me(self, info) -> UserType:
        """
        Return the current authenticated user.

        - The user is injected into context by the GraphQL `context_getter`.
        - The frontend will call this in the `DashboardOverview` query to get
          user + organizations + datastores + projects + datasets in one shot.
        """
        current_user: UserModel = info.context["current_user"]
        logger.debug("Resolving me() for user_id=%s", current_user.id)

        if hasattr(current_user, "is_active") and not current_user.is_active:
            raise ForbiddenError("User account is inactive")

        return UserType(
            id=current_user.id,
            email=current_user.email,
            display_name=getattr(current_user, "display_name", None),
        )
