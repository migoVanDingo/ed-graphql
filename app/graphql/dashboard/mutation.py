# app/graphql/dashboard/mutation.py
import strawberry
from typing import Optional, List
from strawberry.types import Info

from platform_common.db.dal.dataset_dal import DatasetDAL
from platform_common.db.dal.dataset_item_dal import DatasetItemDAL
from platform_common.db.dal.project_dataset_link_dal import ProjectDatasetLinkDAL
from platform_common.db.dal.project_dal import ProjectDAL
from platform_common.db.dal.file_dal import FileDAL
from platform_common.db.session import get_session
from platform_common.errors.base import AuthError, ForbiddenError, NotFoundError
from platform_common.models.dataset import Dataset
from platform_common.models.dataset_item import DatasetItem
from platform_common.utils.time_helpers import to_datetime_utc

from app.graphql.schema.dataset_schema import DatasetType, CreateDatasetInput


@strawberry.type
class DashboardMutation:
    """
    Root mutation mixin for the dashboard.
    You can keep adding more mutations here later.
    """

    @strawberry.mutation
    async def createDataset(
        self,
        info: Info,
        input: CreateDatasetInput,
    ) -> DatasetType:
        current_user = info.context.get("current_user")
        if not current_user:
            raise AuthError("Not authenticated")

        project_id_str: Optional[str] = (
            str(input.project_id) if input.project_id else None
        )

        async for session in get_session():
            dataset_dal = DatasetDAL(session)
            project_dal = ProjectDAL(session)
            link_dal = ProjectDatasetLinkDAL(session)

            if project_id_str:
                project = await project_dal.get_by_id(project_id_str)
                if project is None:
                    raise NotFoundError("Project not found")
                if project.owner_id and project.owner_id != current_user.id:
                    raise ForbiddenError(
                        "Not allowed to attach dataset to this project"
                    )

            dataset = Dataset(
                datastore_id=str(input.datastore_id),
                name=input.name,
                description=input.description,
                owner_id=current_user.id,
            )
            dataset = await dataset_dal.save(dataset)

            if project_id_str:
                await link_dal.create_link(project_id_str, dataset.id)
            break

        return DatasetType(
            id=dataset.id,
            org_id=getattr(current_user, "organization_id", None),
            datastore_id=dataset.datastore_id,
            project_id=project_id_str,
            name=dataset.name,
            description=dataset.description,
            created_at=to_datetime_utc(dataset.created_at),
            updated_at=to_datetime_utc(dataset.updated_at),
        )

    @strawberry.mutation
    async def attachDatasetToProject(
        self,
        info: Info,
        dataset_id: strawberry.ID,
        project_id: strawberry.ID,
    ) -> DatasetType:
        current_user = info.context.get("current_user")
        if not current_user:
            raise AuthError("Not authenticated")

        async for session in get_session():
            dataset_dal = DatasetDAL(session)
            project_dal = ProjectDAL(session)
            link_dal = ProjectDatasetLinkDAL(session)

            dataset = await dataset_dal.get_by_id(str(dataset_id))
            if dataset is None:
                raise NotFoundError("Dataset not found")

            project = await project_dal.get_by_id(str(project_id))
            if project is None:
                raise NotFoundError("Project not found")

            if dataset.owner_id and dataset.owner_id != current_user.id:
                raise ForbiddenError("Not allowed to modify this dataset")
            if project.owner_id and project.owner_id != current_user.id:
                raise ForbiddenError("Not allowed to modify this project")

            await link_dal.create_link(str(project_id), dataset.id)
            updated = dataset
            break

        return DatasetType(
            id=updated.id,
            org_id=getattr(current_user, "organization_id", None),
            datastore_id=updated.datastore_id,
            project_id=str(project_id),
            name=updated.name,
            description=updated.description,
            created_at=to_datetime_utc(updated.created_at),
            updated_at=to_datetime_utc(updated.updated_at),
        )

    @strawberry.mutation
    async def addFilesToDataset(
        self,
        info: Info,
        dataset_id: strawberry.ID,
        file_ids: List[strawberry.ID],
    ) -> DatasetType:
        current_user = info.context.get("current_user")
        if not current_user:
            raise AuthError("Not authenticated")

        async for session in get_session():
            dataset_dal = DatasetDAL(session)
            dataset_item_dal = DatasetItemDAL(session)
            file_dal = FileDAL(session)

            dataset = await dataset_dal.get_by_id(str(dataset_id))
            if dataset is None:
                raise NotFoundError("Dataset not found")

            if dataset.owner_id and dataset.owner_id != current_user.id:
                raise ForbiddenError("Not allowed to modify this dataset")

            files = await file_dal.get_many_by_ids([str(fid) for fid in file_ids])
            if len(files) != len(file_ids):
                missing = set(map(str, file_ids)) - {f.id for f in files}
                raise NotFoundError(f"Some files not found: {missing}")

            for f in files:
                if getattr(f, "datastore_id", None) != dataset.datastore_id:
                    raise ForbiddenError(
                        "All files must belong to the same datastore as the dataset"
                    )

            for f in files:
                item = DatasetItem(
                    dataset_id=dataset.id,
                    file_id=f.id,
                )
                await dataset_item_dal.save(item)

            updated = dataset
            break

        return DatasetType(
            id=updated.id,
            org_id=getattr(current_user, "organization_id", None),
            datastore_id=updated.datastore_id,
            project_id=None,
            name=updated.name,
            description=updated.description,
            created_at=to_datetime_utc(updated.created_at),
            updated_at=to_datetime_utc(updated.updated_at),
        )
