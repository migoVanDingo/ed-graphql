# app/graphql/dashboard/types/project_type.py

from typing import Optional, List
from datetime import datetime
import strawberry
from strawberry.types import Info

from platform_common.db.dal.dataset_dal import DatasetDAL
from platform_common.db.session import get_session
from platform_common.errors.base import ForbiddenError, InternalServerError
from platform_common.logging.logging import get_logger
from platform_common.utils.time_helpers import to_datetime_utc

from app.graphql.schema.dataset_schema import DatasetType

logger = get_logger("graphql_dashboard_project")


@strawberry.type
class ProjectType:
    id: str
    name: str
    status: str
    description: Optional[str]
    created_at: datetime

    @strawberry.field
    async def datasets(
        self,
        info: Info,
    ) -> List[DatasetType]:
        current_user = info.context.get("current_user")

        if not current_user:
            raise ForbiddenError("You are not allowed to access this project")

        try:
            async for session in get_session():
                dataset_dal = DatasetDAL(session)
                datasets = await dataset_dal.list_for_project(str(self.id))
                break
        except Exception as e:
            logger.error("Error loading datasets for project %s: %r", self.id, e)
            raise InternalServerError("Failed to load project datasets")

        return [
            DatasetType(
                id=d.id,
                name=d.name,
                description=d.description,
                created_at=to_datetime_utc(d.created_at),
            )
            for d in datasets
        ]
