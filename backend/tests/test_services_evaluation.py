import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation, EvaluationRun, EvaluationMetric, EvaluationStatus
from app.models.user import User, Role
from app.schemas.evaluation import EvaluationCreate, EvaluationRunCreate, EvaluationMetricBase
from app.services.evaluation import EvaluationService


@pytest.mark.asyncio
async def test_create_evaluation_service(db_session: AsyncSession):
    service = EvaluationService(db_session)
    eval_in = EvaluationCreate(
        name="Service Test",
        description="Testing service layer",
        dataset_name="service-dataset",
        dataset_version="1.0",
        config={"threshold": 0.8},
    )
    evaluation = await service.create_evaluation(eval_in, owner_id=1)
    assert evaluation.id is not None
    assert evaluation.name == "Service Test"
    assert evaluation.status == EvaluationStatus.PENDING


@pytest.mark.asyncio
async def test_get_evaluation_service(db_session: AsyncSession):
    service = EvaluationService(db_session)
    eval_in = EvaluationCreate(name="Get Service", dataset_name="get-svc")
    created = await service.create_evaluation(eval_in, owner_id=1)

    found = await service.get_evaluation(created.id, owner_id=1)
    assert found is not None
    assert found.id == created.id

    not_found = await service.get_evaluation(99999, owner_id=1)
    assert not_found is None


@pytest.mark.asyncio
async def test_list_evaluations_service(db_session: AsyncSession):
    service = EvaluationService(db_session)
    for i in range(3):
        await service.create_evaluation(
            EvaluationCreate(name=f"List {i}", dataset_name=f"ds-{i}"),
            owner_id=1,
        )

    result = await service.list_evaluations(owner_id=1, page=1, page_size=10)
    assert result.total == 3
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_update_evaluation_service(db_session: AsyncSession):
    service = EvaluationService(db_session)
    eval_in = EvaluationCreate(name="Original", dataset_name="orig")
    created = await service.create_evaluation(eval_in, owner_id=1)

    from app.schemas.evaluation import EvaluationUpdate
    updated = await service.update_evaluation(
        created.id,
        EvaluationUpdate(name="Updated", description="New desc"),
        owner_id=1,
    )
    assert updated is not None
    assert updated.name == "Updated"
    assert updated.description == "New desc"


@pytest.mark.asyncio
async def test_delete_evaluation_service(db_session: AsyncSession):
    service = EvaluationService(db_session)
    eval_in = EvaluationCreate(name="Delete Me", dataset_name="del")
    created = await service.create_evaluation(eval_in, owner_id=1)

    deleted = await service.delete_evaluation(created.id, owner_id=1)
    assert deleted is True

    found = await service.get_evaluation(created.id, owner_id=1)
    assert found is None


@pytest.mark.asyncio
async def test_create_run_service(db_session: AsyncSession):
    service = EvaluationService(db_session)
    eval_in = EvaluationCreate(name="Run Eval", dataset_name="run-ds")
    evaluation = await service.create_evaluation(eval_in, owner_id=1)

    run_in = EvaluationRunCreate(model_provider="openai", model_name="gpt-4")
    run = await service.create_run(evaluation.id, run_in, owner_id=1)
    assert run is not None
    assert run.model_provider == "openai"
    assert run.status == EvaluationStatus.PENDING
    # Check evaluation status updated
    updated_eval = await service.get_evaluation(evaluation.id, owner_id=1)
    assert updated_eval.status == EvaluationStatus.RUNNING


@pytest.mark.asyncio
async def test_add_metrics_service(db_session: AsyncSession):
    service = EvaluationService(db_session)
    eval_in = EvaluationCreate(name="Metrics Eval", dataset_name="metrics-ds")
    evaluation = await service.create_evaluation(eval_in, owner_id=1)

    run_in = EvaluationRunCreate(model_provider="ollama", model_name="llama3")
    run = await service.create_run(evaluation.id, run_in, owner_id=1)

    metrics = [
        EvaluationMetricBase(name="accuracy", value=0.92, details={"samples": 100}),
        EvaluationMetricBase(name="f1", value=0.89, details={"samples": 100}),
    ]
    added = await service.add_metrics(run.id, metrics)
    assert len(added) == 2
    assert added[0].name == "accuracy"
    assert added[0].value == 0.92


@pytest.mark.asyncio
async def test_complete_evaluation_service(db_session: AsyncSession):
    service = EvaluationService(db_session)
    eval_in = EvaluationCreate(name="Complete Eval", dataset_name="complete-ds")
    evaluation = await service.create_evaluation(eval_in, owner_id=1)

    run_in = EvaluationRunCreate(model_provider="openai", model_name="gpt-4")
    run = await service.create_run(evaluation.id, run_in, owner_id=1)

    # Complete the run
    await service.update_run_status(run.id, EvaluationStatus.COMPLETED)

    # Complete evaluation
    completed = await service.complete_evaluation(evaluation.id)
    assert completed is not None
    assert completed.status == EvaluationStatus.COMPLETED
    assert completed.completed_at is not None