from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.evaluation import EvaluationService
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationRead,
    EvaluationWithRuns,
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationRunWithMetrics,
    EvaluationListResponse,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    evaluation_in: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    owner_id: int = 1,  # TODO: Replace with actual auth
):
    service = EvaluationService(db)
    evaluation = await service.create_evaluation(evaluation_in, owner_id)
    return EvaluationRead.model_validate(evaluation)


@router.get("", response_model=EvaluationListResponse)
async def list_evaluations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    owner_id: int = 1,  # TODO: Replace with actual auth
):
    service = EvaluationService(db)
    return await service.list_evaluations(owner_id=owner_id, page=page, page_size=page_size, status=status)


@router.get("/{evaluation_id}", response_model=EvaluationWithRuns)
async def get_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
    owner_id: int = 1,  # TODO: Replace with actual auth
):
    service = EvaluationService(db)
    evaluation = await service.get_evaluation_with_runs(evaluation_id, owner_id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return EvaluationWithRuns.model_validate(evaluation)


@router.patch("/{evaluation_id}", response_model=EvaluationRead)
async def update_evaluation(
    evaluation_id: int,
    evaluation_in: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    owner_id: int = 1,  # TODO: Replace with actual auth
):
    service = EvaluationService(db)
    evaluation = await service.update_evaluation(evaluation_id, evaluation_in, owner_id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return EvaluationRead.model_validate(evaluation)


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
    owner_id: int = 1,  # TODO: Replace with actual auth
):
    service = EvaluationService(db)
    deleted = await service.delete_evaluation(evaluation_id, owner_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")


@router.post("/{evaluation_id}/runs", response_model=EvaluationRunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    evaluation_id: int,
    run_in: EvaluationRunCreate,
    db: AsyncSession = Depends(get_db),
    owner_id: int = 1,  # TODO: Replace with actual auth
):
    service = EvaluationService(db)
    run = await service.create_run(evaluation_id, run_in, owner_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return EvaluationRunRead.model_validate(run)


@router.get("/{evaluation_id}/runs/{run_id}", response_model=EvaluationRunWithMetrics)
async def get_run(
    evaluation_id: int,
    run_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = EvaluationService(db)
    run = await service.get_run(run_id)
    if not run or run.evaluation_id != evaluation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return EvaluationRunWithMetrics.model_validate(run)