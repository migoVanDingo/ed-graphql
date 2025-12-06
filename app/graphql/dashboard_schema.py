# app/graphql/dashboard_schema.py

import strawberry
from typing import List, Optional
from datetime import datetime

from platform_common.models.user import User as UserModel
from platform_common.db.dal.datastore_dal import DatastoreDAL
from platform_common.db.dal.project_dal import ProjectDAL
from platform_common.db.dal.dataset_dal import DatasetDAL
from platform_common.db.dal.organization_dal import OrganizationDAL
from platform_common.errors.base import ForbiddenError, InternalServerError
from platform_common.logging.logging import get_logger

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
class DatastoreType:
    id: str
    name: str
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
        db_session = info.context["db_session"]
        current_user: UserModel = info.context["current_user"]

        if current_user.id != self.id:
            raise ForbiddenError("You are not allowed to view these organizations")

        org_dal = OrganizationDAL(db_session)

        try:
            orgs = await org_dal.list_for_user(current_user.id)
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
                created_at=o.created_at,
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
        db_session = info.context["db_session"]
        current_user: UserModel = info.context["current_user"]

        if current_user.id != self.id:
            raise ForbiddenError("You are not allowed to view these datastores")

        org_id = getattr(current_user, "organization_id", None)
        datastore_dal = DatastoreDAL(db_session)

        try:
            datastores = await datastore_dal.list_for_user(
                user_id=current_user.id,
                organization_id=org_id,
            )
        except Exception as e:
            logger.error("Error loading datastores for user %s: %r", current_user.id, e)
            raise InternalServerError("Failed to load datastores")

        return [
            DatastoreType(
                id=d.id,
                name=d.name,
                description=getattr(d, "description", None),
                created_at=d.created_at,
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
        db_session = info.context["db_session"]
        current_user: UserModel = info.context["current_user"]

        if current_user.id != self.id:
            raise ForbiddenError("You are not allowed to view these projects")

        org_id = getattr(current_user, "organization_id", None)
        project_dal = ProjectDAL(db_session)

        try:
            projects = await project_dal.list_for_user(
                user_id=current_user.id,
                organization_id=org_id,
            )
        except Exception as e:
            logger.error("Error loading projects for user %s: %r", current_user.id, e)
            raise InternalServerError("Failed to load projects")

        return [
            ProjectType(
                id=p.id,
                name=p.name,
                description=getattr(p, "description", None),
                created_at=p.created_at,
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
        db_session = info.context["db_session"]
        current_user: UserModel = info.context["current_user"]

        if current_user.id != self.id:
            raise ForbiddenError("You are not allowed to view these datasets")

        org_id = getattr(current_user, "organization_id", None)
        dataset_dal = DatasetDAL(db_session)

        try:
            datasets = await dataset_dal.list_for_user(
                user_id=current_user.id,
                organization_id=org_id,
            )
        except Exception as e:
            logger.error("Error loading datasets for user %s: %r", current_user.id, e)
            raise InternalServerError("Failed to load datasets")

        return [
            DatasetType(
                id=d.id,
                name=d.name,
                description=getattr(d, "description", None),
                created_at=d.created_at,
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
