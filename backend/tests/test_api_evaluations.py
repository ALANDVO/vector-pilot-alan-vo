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
    async def test_create_evaluation(self, client: AsyncClient):
        payload = {
            "name": "Test Evaluation",
            "description": "A test evaluation",
            "dataset_name": "test-dataset",
            "dataset_version": "1.0",
            "config": {"metric": "accuracy"},
        }
        response = await client.post("/api/evaluations", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Evaluation"
        assert data["dataset_name"] == "test-dataset"
        assert data["status"] == "pending"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_evaluation_invalid(self, client: AsyncClient):
        payload = {"name": "", "dataset_name": "test"}
        response = await client.post("/api/evaluations", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_evaluations(self, client: AsyncClient):
        # Create a few evaluations
        for i in range(3):
            await client.post(
                "/api/evaluations",
                json={"name": f"Eval {i}", "dataset_name": f"dataset-{i}"},
            )

        response = await client.get("/api/evaluations")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_list_evaluations_pagination(self, client: AsyncClient):
        for i in range(5):
            await client.post(
                "/api/evaluations",
                json={"name": f"Eval {i}", "dataset_name": f"dataset-{i}"},
            )

        response = await client.get("/api/evaluations?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_list_evaluations_filter_by_status(self, client: AsyncClient):
        await client.post("/api/evaluations", json={"name": "Eval 1", "dataset_name": "ds1"})
        await client.post("/api/evaluations", json={"name": "Eval 2", "dataset_name": "ds2"})

        response = await client.get("/api/evaluations?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_get_evaluation(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/evaluations",
            json={"name": "Get Test", "dataset_name": "get-dataset"},
        )
        eval_id = create_resp.json()["id"]

        response = await client.get(f"/api/evaluations/{eval_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == eval_id
        assert data["name"] == "Get Test"
        assert "runs" in data

    @pytest.mark.asyncio
    async def test_get_evaluation_not_found(self, client: AsyncClient):
        response = await client.get("/api/evaluations/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_evaluation(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/evaluations",
            json={"name": "Original", "dataset_name": "orig-dataset"},
        )
        eval_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/evaluations/{eval_id}",
            json={"name": "Updated", "description": "New description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_delete_evaluation(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/evaluations",
            json={"name": "To Delete", "dataset_name": "del-dataset"},
        )
        eval_id = create_resp.json()["id"]

        response = await client.delete(f"/api/evaluations/{eval_id}")
        assert response.status_code == 204

        get_resp = await client.get(f"/api/evaluations/{eval_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_run(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/evaluations",
            json={"name": "Run Test", "dataset_name": "run-dataset"},
        )
        eval_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/evaluations/{eval_id}/runs",
            json={"model_provider": "openai", "model_name": "gpt-4"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["model_provider"] == "openai"
        assert data["model_name"] == "gpt-4"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_run_for_nonexistent_evaluation(self, client: AsyncClient):
        response = await client.post(
            "/api/evaluations/99999/runs",
            json={"model_provider": "openai", "model_name": "gpt-4"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_run(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/evaluations",
            json={"name": "Run Get Test", "dataset_name": "run-get-dataset"},
        )
        eval_id = create_resp.json()["id"]

        run_resp = await client.post(
            f"/api/evaluations/{eval_id}/runs",
            json={"model_provider": "anthropic", "model_name": "claude-3"},
        )
        run_id = run_resp.json()["id"]

        response = await client.get(f"/api/evaluations/{eval_id}/runs/{run_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["model_provider"] == "anthropic"
        assert "metrics" in data