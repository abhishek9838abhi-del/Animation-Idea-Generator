"""Tests for provider adapter, JSON extraction, and mock fallbacks."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.schemas import GenerateRequest, RuntimeEnum, MoodEnum, AudienceEnum, ComplexityEnum
from app.provider import (
    extract_and_parse_json,
    generate_mock_plan,
    ProviderJSONParseError,
    ProviderTimeoutError,
    ProviderAPIError,
    NvidiaProviderAdapter,
)


def test_extract_json_direct():
    raw = '{"title": "Test Title", "scenes": []}'
    parsed = extract_and_parse_json(raw)
    assert parsed["title"] == "Test Title"


def test_extract_json_markdown_wrapped():
    raw = """
Here is the animation plan you requested:
```json
{
  "title": "Cloud Adventures",
  "logline": "A story about clouds.",
  "characters": []
}
```
Hope you enjoy it!
"""
    parsed = extract_and_parse_json(raw)
    assert parsed["title"] == "Cloud Adventures"


def test_extract_json_outer_braces():
    raw = 'Some leading commentary { "title": "Inner JSON", "count": 1 } trailing note.'
    parsed = extract_and_parse_json(raw)
    assert parsed["title"] == "Inner JSON"


def test_extract_json_malformed():
    with pytest.raises(ProviderJSONParseError):
        extract_and_parse_json("Not a json at all.")

    with pytest.raises(ProviderJSONParseError):
        extract_and_parse_json("")


def test_mock_plan_generation_30s():
    req = GenerateRequest(
        idea="A rabbit tests a jetpack made of carrots.",
        runtime=RuntimeEnum.THIRTY_SECONDS,
        mood=MoodEnum.FUNNY,
        audience=AudienceEnum.CHILDREN,
        has_dialogue=False,
        complexity=ComplexityEnum.SIMPLE,
    )
    plan = generate_mock_plan(req)
    assert len(plan.scenes) == 2
    assert plan.runtime == RuntimeEnum.THIRTY_SECONDS
    for s in plan.scenes:
        assert s.dialogue is None  # dialogue was false


def test_mock_plan_generation_3m():
    req = GenerateRequest(
        idea="An adventurous penguin explores a volcano.",
        runtime=RuntimeEnum.THREE_MINUTES,
        mood=MoodEnum.ADVENTUROUS,
        audience=AudienceEnum.GENERAL,
        has_dialogue=True,
        complexity=ComplexityEnum.DETAILED,
    )
    plan = generate_mock_plan(req)
    assert len(plan.scenes) == 6
    assert plan.runtime == RuntimeEnum.THREE_MINUTES


@pytest.mark.asyncio
async def test_provider_timeout_handling():
    adapter = NvidiaProviderAdapter()
    adapter.api_key = "test_key"  # Pretend configured

    with patch("httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("Timeout reached")):
        with pytest.raises(ProviderTimeoutError):
            await adapter._post_chat_completion([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_provider_upstream_error_handling():
    adapter = NvidiaProviderAdapter()
    adapter.api_key = "test_key"

    mock_resp = httpx.Response(500, request=httpx.Request("POST", "http://test"))
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with pytest.raises(ProviderAPIError) as exc:
            await adapter._post_chat_completion([{"role": "user", "content": "hi"}])
        assert exc.value.status_code == 502
