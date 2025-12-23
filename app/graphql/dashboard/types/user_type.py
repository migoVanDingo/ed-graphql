from typing import List, Optional

import strawberry

from platform_common.models.user import User as UserModel
from platform_common.db.dal.datastore_dal import DatastoreDAL
from platform_common.db.dal.project_dal import ProjectDAL
from platform_common.db.dal.dataset_dal import DatasetDAL
from platform_common.db.dal.organization_dal import OrganizationDAL
from platform_common.db.session import get_session
from platform_common.errors.base import ForbiddenError, InternalServerError
from platform_common.logging.logging import get_logger
from platform_common.utils.time_helpers import to_datetime_utc

from .organization_type import OrganizationType
from .datastore_type import DatastoreType
from .project_type import ProjectType
from .dataset_type import DatasetType

logger = get_logger("graphql_dashboard_user")


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
                status=p.status,
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
