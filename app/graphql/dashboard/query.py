# app/graphql/dashboard/query.py

import strawberry

from platform_common.models.user import User as UserModel
from platform_common.errors.base import ForbiddenError, NotFoundError
from platform_common.logging.logging import get_logger
from platform_common.db.session import get_session
from platform_common.db.dal.datastore_dal import DatastoreDAL
from platform_common.utils.time_helpers import to_datetime_utc  # 👈 add this

from app.graphql.dashboard.types import UserType
from app.graphql.dashboard.types.datastore_type import DatastoreType

logger = get_logger("graphql_dashboard_query")


@strawberry.type
class DashboardQuery:
    @strawberry.field
    async def me(self, info) -> UserType:
        current_user: UserModel = info.context["current_user"]
        logger.debug("Resolving me() for user_id=%s", current_user.id)

        if hasattr(current_user, "is_active") and not current_user.is_active:
            raise ForbiddenError("User account is inactive")

        return UserType(
            id=current_user.id,
            email=current_user.email,
            display_name=getattr(current_user, "display_name", None),
        )

    @strawberry.field
    async def datastore(
        self,
        info,
        id: str,
    ) -> DatastoreType:
        current_user: UserModel = info.context["current_user"]

        async for session in get_session():
            datastore_dal = DatastoreDAL(session)
            ds_row = await datastore_dal.get_by_id(id)
            break

        if ds_row is None:
            raise NotFoundError("Datastore not found")

        mapping = getattr(ds_row, "_mapping", None)
        if mapping is not None and "Datastore" in mapping:
            ds = mapping["Datastore"]
        else:
            ds = ds_row

        if getattr(ds, "user_id", None) and ds.user_id != current_user.id:
            raise ForbiddenError("You do not have access to this datastore")

        # 👇 convert epoch -> datetime if needed
        raw_created_at = getattr(ds, "created_at", None)
        if isinstance(raw_created_at, (int, float)):
            created_at = to_datetime_utc(raw_created_at)
        else:
            created_at = raw_created_at

        return DatastoreType(
            id=ds.id,
            name=ds.name,
            description=ds.description,
            created_at=created_at,
        )
