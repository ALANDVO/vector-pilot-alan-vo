import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.evaluation import Evaluation, EvaluationRun, EvaluationMetric, EvaluationStatus
from ..models.user import User, Role
from ..schemas.evaluation import (
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationRead,
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationMetricBase,
    EvaluationListResponse,
)


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_evaluation(
        self,
        evaluation_in: EvaluationCreate,
        owner_id: int,
    ) -> Evaluation:
        evaluation = Evaluation(
            name=evaluation_in.name,
            description=evaluation_in.description,
            dataset_name=evaluation_in.dataset_name,
            dataset_version=evaluation_in.dataset_version,
            config=json.dumps(evaluation_in.config) if evaluation_in.config else None,
            owner_id=owner_id,
            status=EvaluationStatus.PENDING,
        )
        self.db.add(evaluation)
        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation

    async def get_evaluation(self, evaluation_id: int, owner_id: Optional[int] = None) -> Optional[Evaluation]:
        stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
        if owner_id is not None:
            stmt = stmt.where(Evaluation.owner_id == owner_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_evaluation_with_runs(self, evaluation_id: int, owner_id: Optional[int] = None) -> Optional[Evaluation]:
        stmt = (
            select(Evaluation)
            .options(selectinload(Evaluation.runs).selectinload(EvaluationRun.metrics))
            .where(Evaluation.id == evaluation_id)
        )
        if owner_id is not None:
            stmt = stmt.where(Evaluation.owner_id == owner_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_evaluations(
        self,
        owner_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> EvaluationListResponse:
        stmt = select(Evaluation)
        count_stmt = select(func.count(Evaluation.id))

        if owner_id is not None:
            stmt = stmt.where(Evaluation.owner_id == owner_id)
            count_stmt = count_stmt.where(Evaluation.owner_id == owner_id)

        if status:
            stmt = stmt.where(Evaluation.status == status)
            count_stmt = count_stmt.where(Evaluation.status == status)

        stmt = stmt.order_by(desc(Evaluation.created_at)).offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        return EvaluationListResponse(
            items=[EvaluationRead.model_validate(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_evaluation(
        self,
        evaluation_id: int,
        evaluation_in: EvaluationUpdate,
        owner_id: Optional[int] = None,
    ) -> Optional[Evaluation]:
        evaluation = await self.get_evaluation(evaluation_id, owner_id)
        if not evaluation:
            return None

        update_data = evaluation_in.model_dump(exclude_unset=True)
        if "config" in update_data and update_data["config"] is not None:
            update_data["config"] = json.dumps(update_data["config"])
        elif "config" in update_data and update_data["config"] is None:
            update_data["config"] = None

        for field, value in update_data.items():
            setattr(evaluation, field, value)

        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation

    async def delete_evaluation(self, evaluation_id: int, owner_id: Optional[int] = None) -> bool:
        evaluation = await self.get_evaluation(evaluation_id, owner_id)
        if not evaluation:
            return False
        await self.db.delete(evaluation)
        await self.db.commit()
        return True

    async def create_run(
        self,
        evaluation_id: int,
        run_in: EvaluationRunCreate,
        owner_id: Optional[int] = None,
    ) -> Optional[EvaluationRun]:
        evaluation = await self.get_evaluation(evaluation_id, owner_id)
        if not evaluation:
            return None

        run = EvaluationRun(
            evaluation_id=evaluation_id,
            model_provider=run_in.model_provider,
            model_name=run_in.model_name,
            model_config=json.dumps(run_in.model_config) if run_in.model_config else None,
            status=EvaluationStatus.PENDING,
        )
        self.db.add(run)

        evaluation.status = EvaluationStatus.RUNNING
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get_run(self, run_id: int) -> Optional[EvaluationRun]:
        stmt = select(EvaluationRun).options(selectinload(EvaluationRun.metrics)).where(EvaluationRun.id == run_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_run_status(
        self,
        run_id: int,
        status: EvaluationStatus,
        error_message: Optional[str] = None,
    ) -> Optional[EvaluationRun]:
        run = await self.get_run(run_id)
        if not run:
            return None

        run.status = status
        if error_message:
            run.error_message = error_message
        if status in (EvaluationStatus.COMPLETED, EvaluationStatus.FAILED):
            run.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def add_metrics(self, run_id: int, metrics: list[EvaluationMetricBase]) -> list[EvaluationMetric]:
        run = await self.get_run(run_id)
        if not run:
            return []

        metric_objects = [
            EvaluationMetric(
                run_id=run_id,
                name=m.name,
                value=m.value,
                details=json.dumps(m.details) if m.details else None,
            )
            for m in metrics
        ]
        self.db.add_all(metric_objects)
        await self.db.commit()
        for m in metric_objects:
            await self.db.refresh(m)
        return metric_objects

    async def complete_evaluation(self, evaluation_id: int) -> Optional[Evaluation]:
        evaluation = await self.get_evaluation(evaluation_id)
        if not evaluation:
            return None

        # Check if all runs are completed
        stmt = select(EvaluationRun).where(
            EvaluationRun.evaluation_id == evaluation_id,
            EvaluationRun.status.in_([EvaluationStatus.PENDING, EvaluationStatus.RUNNING]),
        )
        result = await self.db.execute(stmt)
        pending_runs = result.scalars().all()

        if not pending_runs:
            evaluation.status = EvaluationStatus.COMPLETED
            evaluation.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(evaluation)

        return evaluation