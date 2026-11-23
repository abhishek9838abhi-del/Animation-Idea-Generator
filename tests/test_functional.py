"""End-to-end API functional tests."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.limiter import rate_limiter


@pytest.fixture(autouse=True)
def reset_limiter():
    rate_limiter.reset()
    yield
    rate_limiter.reset()


@pytest.mark.asyncio
async def test_static_and_index_serving():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert "<title>Frame by Frame: Animation Idea Generator</title>" in res.text

        css_res = await client.get("/static/styles.css")
        assert css_res.status_code == 200
        assert ":root" in css_res.text

        js_res = await client.get("/static/app.js")
        assert js_res.status_code == 200
        assert "document.addEventListener" in js_res.text


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "provider" in data
        assert data["provider"]["name"] == "nvidia"


@pytest.mark.asyncio
async def test_generate_endpoint_mock_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "idea": "A lonely lighthouse bulb wants to learn how to wink at passing ships.",
            "runtime": "1m",
            "mood": "funny",
            "audience": "children",
            "has_dialogue": False,
            "complexity": "simple",
        }
        res = await client.post("/api/generate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "title" in data
        assert "logline" in data
        assert "characters" in data
        assert len(data["characters"]) >= 1
        assert "scenes" in data
        assert len(data["scenes"]) >= 2
        assert "X-RateLimit-Remaining" in res.headers


@pytest.mark.asyncio
async def test_revise_endpoint_mock_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First generate
        gen_res = await client.post(
            "/api/generate",
            json={
                "idea": "A tiny sprout wants to reach the top of a garden fence.",
                "runtime": "30s",
                "mood": "heartwarming",
                "audience": "general",
                "has_dialogue": False,
                "complexity": "simple",
            },
        )
        plan = gen_res.json()

        # Request revision
        rev_payload = {
            "previous_plan": plan,
            "revision_instruction": "Add a friendly snail that gives the sprout a boost.",
        }
        rev_res = await client.post("/api/revise", json=rev_payload)
        assert rev_res.status_code == 200
        rev_data = rev_res.json()
        assert "Revised" in rev_data["title"] or len(rev_data["scenes"]) >= 2
