# app/graphql/dashboard_schema.py

import strawberry
from typing import List, Optional
from datetime import datetime

from platform_common.models.user import User as UserModel
from platform_common.db.dal.datastore_dal import DatastoreDAL
from platform_common.db.dal.project_dal import ProjectDAL
from platform_common.db.dal.dataset_dal import DatasetDAL
from platform_common.db.dal.organization_dal import OrganizationDAL
from platform_common.db.session import get_session
from platform_common.errors.base import ForbiddenError, InternalServerError
from platform_common.logging.logging import get_logger
from platform_common.utils.time_helpers import to_datetime_utc
from platform_common.models.file import File as FileModel

logger = get_logger("graphql_dashboard")


# ─────────────────────────────────────────
# GraphQL Types
# ─────────────────────────────────────────


@strawberry.type
class OrganizationType:
    id: str
    name: str
    # Adjust these fields to whatever your Organization model actually has
    description: Optional[str]
    created_at: datetime


@strawberry.type
class ProjectType:
    id: str
    name: str
    description: Optional[str]
    created_at: datetime


@strawberry.type
class DatasetType:
    id: str
    name: str
    description: Optional[str]
    created_at: datetime


@strawberry.type
class DatastoreFileType:
    id: str
    filename: str
    content_type: str
    size: int
    created_at: datetime


@strawberry.type
class DatastoreFileTypeBreakdownType:
    content_type: str
    file_count: int
    total_bytes: int


@strawberry.type
class DatastoreFileCategoryBreakdownType:
    # e.g. "csv", "json", "mp4", "wav", "audio", "video", "other"
    category: str

    # if you want to show the underlying MIME types in a tooltip, etc.
    content_types: List[str]

    file_count: int
    total_bytes: int


@strawberry.type
class DatastoreMetricsType:
    capacity_bytes: Optional[int]
    used_bytes: int
    free_bytes: Optional[int]
    used_percent: Optional[float]

    file_count: int
    last_upload_at: Optional[datetime]

    # ← changed to category-based breakdown:
    by_category: List[DatastoreFileCategoryBreakdownType]


@strawberry.type
class DatastoreFilesPageType:
    items: List[DatastoreFileType]
    total_count: int
    # simple offset-based pagination for now
    limit: int
    offset: int


@strawberry.type
class DatastoreType:
    id: str
    name: str
    description: Optional[str]
    created_at: datetime

    @strawberry.field
    async def metrics(self, info) -> DatastoreMetricsType:
        from app.resolvers.datastore_resolvers import get_datastore_metrics

        return await get_datastore_metrics(info, datastore_id=self.id)

    @strawberry.field
    async def files(
        self,
        info,
        limit: int = 25,
        offset: int = 0,
    ) -> DatastoreFilesPageType:
        from app.resolvers.datastore_resolvers import get_datastore_files_page

        return await get_datastore_files_page(
            info,
            datastore_id=self.id,
            limit=limit,
            offset=offset,
        )


@strawberry.type
class UserType:
    """
    User type used for the dashboard `me` query.

    All nested fields (organizations/datastores/projects/datasets) are resolved
    based on the *current* authenticated user from the GraphQL context.
    No userId is ever accepted from the client for authorization.
    """

    id: str
    email: str
    display_name: Optional[str]

    # ─────────────────────────────────────────
    # Organizations
    # ─────────────────────────────────────────
    @strawberry.field
    async def organizations(self, info) -> List[OrganizationType]:
        """
        All organizations this user is a member of.
        """
        current_user: UserModel = info.context["current_user"]

        if current_user.id != self.id:
            raise ForbiddenError("You are not allowed to view these organizations")

        try:
            async for session in get_session():
                org_dal = OrganizationDAL(session)
                orgs = await org_dal.list_for_user(current_user.id)
                break
        except Exception as e:
            logger.error(
                "Error loading organizations for user %s: %r", current_user.id, e
            )
            raise InternalServerError("Failed to load organizations")

        return [
            OrganizationType(
                id=o.id,
                name=o.name,
                description=getattr(o, "description", None),
                created_at=to_datetime_utc(o.created_at),
            )
            for o in orgs
        ]

    # ─────────────────────────────────────────
    # Datastores
    # ─────────────────────────────────────────
    @strawberry.field
    async def datastores(self, info) -> List[DatastoreType]:
        """
        Datastores visible to this user.

        Strategy here:
          - If the User model has a primary `organization_id`, we use it
            as the org scope.
          - Otherwise, DatastoreDAL.list_for_user falls back to owner_id.
        """
        current_user: UserModel = info.context["current_user"]

        if current_user.id != self.id:
            raise ForbiddenError("You are not allowed to view these datastores")

        org_id = getattr(current_user, "organization_id", None)

        try:
            async for session in get_session():
                datastore_dal = DatastoreDAL(session)
                datastores = await datastore_dal.list_for_user(
                    user_id=current_user.id,
                    organization_id=org_id,
                )
                break
        except Exception as e:
            logger.error("Error loading datastores for user %s: %r", current_user.id, e)
            raise InternalServerError("Failed to load datastores")

        return [
            DatastoreType(
                id=d.id,
                name=d.name,
                description=getattr(d, "description", None),
                created_at=to_datetime_utc(d.created_at),
            )
            for d in datastores
        ]

    # ─────────────────────────────────────────
    # Projects
    # ─────────────────────────────────────────
    @strawberry.field
    async def projects(self, info) -> List[ProjectType]:
        """
        Projects visible to this user.
        """
        current_user: UserModel = info.context["current_user"]

        if current_user.id != self.id:
            raise ForbiddenError("You are not allowed to view these projects")

        org_id = getattr(current_user, "organization_id", None)

        try:
            async for session in get_session():
                project_dal = ProjectDAL(session)
                projects = await project_dal.list_for_user(
                    user_id=current_user.id,
                    organization_id=org_id,
                )
                break
        except Exception as e:
            logger.error("Error loading projects for user %s: %r", current_user.id, e)
            raise InternalServerError("Failed to load projects")

        return [
            ProjectType(
                id=p.id,
                name=p.name,
                description=getattr(p, "description", None),
                created_at=to_datetime_utc(p.created_at),
            )
            for p in projects
        ]

    # ─────────────────────────────────────────
    # Datasets
    # ─────────────────────────────────────────
    @strawberry.field
    async def datasets(self, info) -> List[DatasetType]:
        """
        Datasets visible to this user.
        """
        current_user: UserModel = info.context["current_user"]

        if current_user.id != self.id:
            raise ForbiddenError("You are not allowed to view these datasets")

        org_id = getattr(current_user, "organization_id", None)

        try:
            async for session in get_session():
                dataset_dal = DatasetDAL(session)
                datasets = await dataset_dal.list_for_user(
                    user_id=current_user.id,
                    organization_id=org_id,
                )
                break
        except Exception as e:
            logger.error("Error loading datasets for user %s: %r", current_user.id, e)
            raise InternalServerError("Failed to load datasets")

        return [
            DatasetType(
                id=d.id,
                name=d.name,
                description=getattr(d, "description", None),
                created_at=to_datetime_utc(d.created_at),
            )
            for d in datasets
        ]


# ─────────────────────────────────────────
# Root Dashboard Query
# ─────────────────────────────────────────


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
