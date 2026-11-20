from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.app.core.database import get_db
from backend.app.core.auth import get_current_user, get_role_required
from backend.app.models.user import User, Role
from backend.app.services.evaluation import EvaluationService
from backend.app.schemas.evaluation import (
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


# Dependency: requires authentication
auth_dependency = Depends(get_current_user)

# Dependency: requires specific roles
admin_dependency = Depends(get_role_required([Role.ADMIN]))
operator_dependency = Depends(get_role_required([Role.ADMIN, Role.OPERATOR]))


@router.post("", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    evaluation_in: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = auth_dependency,
):
    """Create a new evaluation. Requires authentication."""
    service = EvaluationService(db)
    evaluation = await service.create_evaluation(evaluation_in, current_user.id)
    return EvaluationRead.model_validate(evaluation)


@router.get("", response_model=EvaluationListResponse)
async def list_evaluations(
    db: AsyncSession = Depends(get_db),
    current_user: User = auth_dependency,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
):
    """List evaluations. Requires authentication. Role-based filtering applied in service."""
    service = EvaluationService(db)
    return await service.list_evaluations(owner_id=current_user.id, page=page, page_size=page_size, status=status)


@router.get("/{evaluation_id}", response_model=EvaluationWithRuns)
async def get_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = auth_dependency,
):
    """Get a specific evaluation. Requires authentication."""
    service = EvaluationService(db)
    evaluation = await service.get_evaluation_with_runs(evaluation_id, owner_id=current_user.id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return EvaluationWithRuns.model_validate(evaluation)


@router.patch("/{evaluation_id}", response_model=EvaluationRead)
async def update_evaluation(
    evaluation_id: int,
    evaluation_in: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = auth_dependency,
):
    """Update an evaluation. Requires authentication."""
    service = EvaluationService(db)
    evaluation = await service.update_evaluation(evaluation_id, evaluation_in, owner_id=current_user.id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return EvaluationRead.model_validate(evaluation)


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = auth_dependency,
):
    """Delete an evaluation. Requires authentication."""
    service = EvaluationService(db)
    success = await service.delete_evaluation(evaluation_id, owner_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")


@router.post("/{evaluation_id}/runs", response_model=EvaluationRunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    evaluation_id: int,
    run_in: EvaluationRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = auth_dependency,
):
    """Create a new evaluation run. Requires authentication."""
    service = EvaluationService(db)
    run = await service.create_run(evaluation_id, run_in, owner_id=current_user.id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return EvaluationRunRead.model_validate(run)


@router.get("/{evaluation_id}/runs/{run_id}", response_model=EvaluationRunWithMetrics)
async def get_run(
    evaluation_id: int,
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = auth_dependency,
):
    """Get a specific run. Requires authentication."""
    service = EvaluationService(db)
    run = await service.get_run(run_id)
    if not run or run.evaluation_id != evaluation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    # Check ownership
    evaluation = await service.get_evaluation(evaluation_id, owner_id=current_user.id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return EvaluationRunWithMetrics.model_validate(run)


@router.patch("/{evaluation_id}/runs/{run_id}/status", response_model=EvaluationRunRead)
async def update_run_status(
    evaluation_id: int,
    run_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = admin_dependency,
):
    """Update run status. Admin-only endpoint."""
    service = EvaluationService(db)
    eval_obj = await service.get_evaluation(evaluation_id, owner_id=current_user.id)
    if not eval_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    run = await service.update_run_status(run_id, status)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return EvaluationRunRead.model_validate(run)
