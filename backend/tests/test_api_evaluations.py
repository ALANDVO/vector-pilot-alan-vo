import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "vector-pilot-alan-vo"


class TestEvaluationsAPI:
    @pytest.mark.asyncio
    async def test_create_evaluation(self, client: AsyncClient, test_user):
        payload = {
            "name": "Test Evaluation",
            "description": "A test evaluation",
            "dataset_name": "test-dataset",
            "dataset_version": "1.0",
            "config": {"metric": "accuracy"},
        }
        response = await client.post(f"/api/evaluations?owner_id={test_user.id}", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Evaluation"
        assert data["dataset_name"] == "test-dataset"
        assert data["status"] == "pending"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_evaluation_invalid(self, client: AsyncClient, test_user):
        payload = {"name": "", "dataset_name": "test"}
        response = await client.post(f"/api/evaluations?owner_id={test_user.id}", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_evaluations(self, client: AsyncClient, test_user):
        # Create a few evaluations
        for i in range(3):
            await client.post(
                f"/api/evaluations?owner_id={test_user.id}",
                json={"name": f"Eval {i}", "dataset_name": f"dataset-{i}"},
            )

        response = await client.get(f"/api/evaluations?owner_id={test_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_list_evaluations_pagination(self, client: AsyncClient, test_user):
        for i in range(5):
            await client.post(
                f"/api/evaluations?owner_id={test_user.id}",
                json={"name": f"Eval {i}", "dataset_name": f"dataset-{i}"},
            )

        response = await client.get(f"/api/evaluations?owner_id={test_user.id}&page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_list_evaluations_filter_by_status(self, client: AsyncClient, test_user):
        await client.post(f"/api/evaluations?owner_id={test_user.id}", json={"name": "Eval 1", "dataset_name": "ds1"})
        await client.post(f"/api/evaluations?owner_id={test_user.id}", json={"name": "Eval 2", "dataset_name": "ds2"})

        response = await client.get(f"/api/evaluations?owner_id={test_user.id}&status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_get_evaluation(self, client: AsyncClient, test_user):
        create_resp = await client.post(
            f"/api/evaluations?owner_id={test_user.id}",
            json={"name": "Test Eval", "dataset_name": "test-ds"},
        )
        eval_id = create_resp.json()["id"]

        response = await client.get(f"/api/evaluations/{eval_id}?owner_id={test_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == eval_id
        assert data["name"] == "Test Eval"
        assert "runs" in data

    @pytest.mark.asyncio
    async def test_get_evaluation_not_found(self, client: AsyncClient, test_user):
        response = await client.get(f"/api/evaluations/99999?owner_id={test_user.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_evaluation(self, client: AsyncClient, test_user):
        create_resp = await client.post(
            f"/api/evaluations?owner_id={test_user.id}",
            json={"name": "Original", "dataset_name": "ds1"},
        )
        eval_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/evaluations/{eval_id}?owner_id={test_user.id}",
            json={"name": "Updated", "description": "New description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_delete_evaluation(self, client: AsyncClient, test_user):
        create_resp = await client.post(
            f"/api/evaluations?owner_id={test_user.id}",
            json={"name": "To Delete", "dataset_name": "ds1"},
        )
        eval_id = create_resp.json()["id"]

        response = await client.delete(f"/api/evaluations/{eval_id}?owner_id={test_user.id}")
        assert response.status_code == 204

        get_resp = await client.get(f"/api/evaluations/{eval_id}?owner_id={test_user.id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_run(self, client: AsyncClient, test_user):
        create_resp = await client.post(
            f"/api/evaluations?owner_id={test_user.id}",
            json={"name": "Eval for Run", "dataset_name": "ds1"},
        )
        eval_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/evaluations/{eval_id}/runs?owner_id={test_user.id}",
            json={"model_provider": "openai", "model_name": "gpt-4", "model_config_json": {"temperature": 0.7}},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["model_provider"] == "openai"
        assert data["model_name"] == "gpt-4"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_run_for_nonexistent_evaluation(self, client: AsyncClient, test_user):
        response = await client.post(
            f"/api/evaluations/99999/runs?owner_id={test_user.id}",
            json={"model_provider": "openai", "model_name": "gpt-4"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_run(self, client: AsyncClient, test_user):
        create_resp = await client.post(
            f"/api/evaluations?owner_id={test_user.id}",
            json={"name": "Eval for Run", "dataset_name": "ds1"},
        )
        eval_id = create_resp.json()["id"]

        run_resp = await client.post(
            f"/api/evaluations/{eval_id}/runs?owner_id={test_user.id}",
            json={"model_provider": "openai", "model_name": "gpt-4"},
        )
        run_id = run_resp.json()["id"]

        response = await client.get(f"/api/evaluations/{eval_id}/runs/{run_id}?owner_id={test_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert "metrics" in data
