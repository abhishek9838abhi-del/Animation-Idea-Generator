"""Tests for security, rate limiting, and information sanitization."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.limiter import rate_limiter
from app.prompts import sanitize_style_instructions


def test_living_artist_style_filter():
    raw_prompt = "A girl flying on a broom in the style of Hayao Miyazaki"
    sanitized = sanitize_style_instructions(raw_prompt)
    assert "Avoid direct imitation" in sanitized
    assert "neutral visual descriptors" in sanitized


@pytest.mark.asyncio
async def test_rate_limiting_enforcement():
    rate_limiter.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Make 10 permitted requests
        for i in range(10):
            res = await client.post(
                "/api/generate",
                json={
                    "idea": "A tiny cloud wants to make thunder.",
                    "runtime": "1m",
                    "mood": "heartwarming",
                    "audience": "general",
                    "has_dialogue": False,
                    "complexity": "simple",
                },
            )
            assert res.status_code == 200

        # Request 11 should be rejected with 429
        rejected_res = await client.post(
            "/api/generate",
            json={
                "idea": "A tiny cloud wants to make thunder.",
                "runtime": "1m",
                "mood": "heartwarming",
                "audience": "general",
                "has_dialogue": False,
                "complexity": "simple",
            },
        )
        assert rejected_res.status_code == 429
        data = rejected_res.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in rejected_res.headers
    rate_limiter.reset()


@pytest.mark.asyncio
async def test_error_envelope_sanitization():
    """Ensure error envelopes do not leak internal stack traces or environment paths."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit invalid payload
        res = await client.post("/api/generate", json={"idea": "bad"})
        assert res.status_code == 422
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "SCHEMA_VALIDATION_ERROR"
        assert "Traceback" not in res.text
