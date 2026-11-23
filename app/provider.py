"""NVIDIA NIM / Hosted Model Provider Adapter for Frame by Frame."""

import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from pydantic import ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)

from app.config import settings
from app.schemas import (
    AnimationPlan,
    GenerateRequest,
    ReviseRequest,
    Character,
    Scene,
    RuntimeEnum,
)
from app.prompts import build_generate_messages, build_revise_messages

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Provider Exceptions
# ---------------------------------------------------------------------------
class ProviderError(Exception):
    """Base exception for AI provider issues."""

    def __init__(self, message: str, code: str = "PROVIDER_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message


class ProviderNotConfiguredError(ProviderError):
    """Raised when the NVIDIA API key is not configured."""

    def __init__(self, message: str = "NVIDIA AI Provider is not configured. Please set NVIDIA_API_KEY."):
        super().__init__(message, code="PROVIDER_NOT_CONFIGURED")


class ProviderTimeoutError(ProviderError):
    """Raised when upstream API exceeds the timeout limit."""

    def __init__(self, message: str = "The AI model request timed out. Please try again."):
        super().__init__(message, code="PROVIDER_TIMEOUT")


class ProviderAPIError(ProviderError):
    """Raised when upstream API returns an HTTP error code."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, code="PROVIDER_ERROR")
        self.status_code = status_code


class ProviderJSONParseError(ProviderError):
    """Raised when model output fails to parse into a valid AnimationPlan."""

    def __init__(self, message: str = "The AI provider returned an invalid or incomplete plan structure."):
        super().__init__(message, code="PROVIDER_PARSE_ERROR")


# ---------------------------------------------------------------------------
# Multi-Stage JSON Extractor
# ---------------------------------------------------------------------------
def extract_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """
    Robustly extracts and parses JSON from raw model text.
    1. Direct json.loads
    2. Strips markdown fences: ```json ... ``` or ``` ... ```
    3. Searches for outermost balanced braces { ... }
    """
    if not raw_text or not raw_text.strip():
        raise ProviderJSONParseError("Model returned an empty response.")

    text = raw_text.strip()

    # Stage 1: Direct JSON parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Stage 2: Strip Markdown code blocks
    fence_pattern = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
    match = fence_pattern.search(text)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Stage 3: Extract content between first '{' and last '}'
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        candidate = text[start_idx : end_idx + 1].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to extract valid JSON from raw text length %d", len(raw_text))
    raise ProviderJSONParseError("Failed to extract a valid JSON animation plan from the model response.")


# ---------------------------------------------------------------------------
# Mock Fallback Generator (For unconfigured or dry-run development)
# ---------------------------------------------------------------------------
def generate_mock_plan(request: GenerateRequest) -> AnimationPlan:
    """Provides a realistic, schema-valid mock animation plan when API key is unconfigured."""
    is_30s = request.runtime == RuntimeEnum.THIRTY_SECONDS
    is_3m = request.runtime == RuntimeEnum.THREE_MINUTES

    if is_30s:
        scenes = [
            Scene(
                scene_number=1,
                description="The protagonist enthusiastically steps forward, preparing to showcase their big idea.",
                visual_suggestion="Medium wide shot with vibrant, warm key lighting establishing character silhouette.",
                dialogue="Watch this!" if request.has_dialogue else None,
                sound_suggestions=["Playful brass swell", "Quick footstep patter"],
            ),
            Scene(
                scene_number=2,
                description="A sudden, comedic mishap occurs, twisting the expectation into a delightfully unexpected outcome.",
                visual_suggestion="Close-up on exaggerated squash-and-stretch facial reaction, followed by gentle fade to black.",
                dialogue="Well... that worked differently." if request.has_dialogue else None,
                sound_suggestions=["Whimsical slide whistle", "Soft cymbal tap"],
            ),
        ]
    elif is_3m:
        scenes = [
            Scene(
                scene_number=1,
                description="Introduce the main character in their ordinary world, longing for a change of pace.",
                visual_suggestion="Wide tracking shot through a cozy, detailed environment.",
                dialogue="There has to be something more out there." if request.has_dialogue else None,
                sound_suggestions=["Gentle acoustic guitar theme", "Ambient nature breeze"],
            ),
            Scene(
                scene_number=2,
                description="The inciting incident: an unexpected obstacle disrupts the calm routine.",
                visual_suggestion="Low angle shot emphasizing the imposing scale of the challenge.",
                dialogue="Wait, what is happening?!" if request.has_dialogue else None,
                sound_suggestions=["Dramatic string swell", "Rattling thunderclap"],
            ),
            Scene(
                scene_number=3,
                description="First attempt to overcome the problem leads to comical or heartwarming failure.",
                visual_suggestion="Dynamic side-scrolling action beat with quick camera pans.",
                dialogue=None,
                sound_suggestions=["Staccato marimba run", "Clattering impacts"],
            ),
            Scene(
                scene_number=4,
                description="A mentor or companion offers an unconventional insight.",
                visual_suggestion="Two-shot framing with soft rim lighting highlighting emotional connection.",
                dialogue="You don't need brute force; you need rhythm." if request.has_dialogue else None,
                sound_suggestions=["Warm cello harmony"],
            ),
            Scene(
                scene_number=5,
                description="The climax: applying the new lesson in an energetic sequence.",
                visual_suggestion="High-energy circular camera move building momentum.",
                dialogue=None,
                sound_suggestions=["Triumphant orchestral build-up", "Whooshing air dynamics"],
            ),
            Scene(
                scene_number=6,
                description="Resolution: celebrating the achieved goal with a peaceful new status quo.",
                visual_suggestion="Golden hour wide shot as the characters smile together.",
                dialogue="We actually did it." if request.has_dialogue else None,
                sound_suggestions=["Warm, lingering piano melody"],
            ),
        ]
    else:  # 1m (4 scenes)
        scenes = [
            Scene(
                scene_number=1,
                description=f"Introduction: {request.idea[:60]}... The character sets their sights on a clear goal.",
                visual_suggestion="Establishing shot with clear character staging and warm directional light.",
                dialogue="Today is the day!" if request.has_dialogue else None,
                sound_suggestions=["Light woodwind arpeggios"],
            ),
            Scene(
                scene_number=2,
                description="The character confronts the first major hurdle with stubborn determination.",
                visual_suggestion="Over-the-shoulder framing focusing on the obstacle.",
                dialogue=None,
                sound_suggestions=["Playful percussion ticking", "Foley rustling"],
            ),
            Scene(
                scene_number=3,
                description="A critical turn of events forces an inventive, unconventional solution.",
                visual_suggestion="Dramatic close-up on character's sudden spark of inspiration.",
                dialogue="Aha!" if request.has_dialogue else None,
                sound_suggestions=["Sudden harp glissando", "Tinkling chime"],
            ),
            Scene(
                scene_number=4,
                description="A heartwarming resolution that leaves a lasting emotional smile.",
                visual_suggestion="Slow pull-out shot to a scenic wide composition.",
                dialogue=None,
                sound_suggestions=["Resolved chord cadence", "Gentle wind rustle"],
            ),
        ]

    return AnimationPlan(
        title=f"The Tale of {request.idea.split()[-1].capitalize() or 'Tomorrow'}",
        logline=f"Inspired by '{request.idea[:80]}', a determined character learns that unexpected answers lead to the best adventures.",
        runtime=request.runtime,
        mood=request.mood,
        audience=request.audience,
        complexity=request.complexity,
        characters=[
            Character(
                name="Pip",
                role="Spirited Protagonist",
                goal="Achieve their creative ambition against small odds",
            ),
            Character(
                name="Sage",
                role="Supportive Companion",
                goal="Keep Pip grounded and encourage their journey",
            ),
        ],
        scenes=scenes,
        sound_suggestions=[
            "Charming acoustic instrument palette (acoustic guitar, pizzicato strings, soft woodwinds)",
            "Tactile foley emphasis highlighting comedic and physical animation beats",
        ],
    )


# ---------------------------------------------------------------------------
# NVIDIA Provider Client
# ---------------------------------------------------------------------------
class NvidiaProviderAdapter:
    """Server-side client for interacting with NVIDIA NIM / Hosted models."""

    def __init__(self):
        self.base_url = settings.nvidia_base_url.rstrip("/")
        self.api_key = settings.nvidia_api_key
        self.model = settings.nvidia_model
        self.timeout = settings.nvidia_timeout_seconds
        self.max_retries = settings.nvidia_max_retries

    @property
    def is_configured(self) -> bool:
        return bool(
            self.api_key
            and self.api_key.strip()
            and not self.api_key.startswith("your_nvidia_api_key")
        )

    async def _post_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Sends chat completion request to NVIDIA NIM with retry logic."""
        if not self.is_configured:
            raise ProviderNotConfiguredError()

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2500,
            "top_p": 0.95,
        }

        # Tenacity retry wrapper
        @retry(
            reraise=True,
            stop=stop_after_attempt(self.max_retries + 1),
            wait=wait_exponential_jitter(initial=1.0, max=5.0),
            retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout)),
        )
        async def _call():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.post(url, headers=headers, json=payload)
                except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                    logger.error("Timeout connecting to NVIDIA API: %s", str(e))
                    raise ProviderTimeoutError() from e
                except httpx.ConnectError as e:
                    logger.error("Connection error to NVIDIA API: %s", str(e))
                    raise ProviderAPIError("Unable to connect to NVIDIA API endpoint.", status_code=502) from e

                if response.status_code != 200:
                    logger.error(
                        "NVIDIA API error: HTTP %d", response.status_code
                    )
                    if response.status_code == 401:
                        raise ProviderNotConfiguredError("NVIDIA API authentication failed. Please verify NVIDIA_API_KEY.")
                    if response.status_code == 429:
                        raise ProviderAPIError("NVIDIA API rate limit exceeded.", status_code=429)
                    raise ProviderAPIError(
                        f"NVIDIA API returned error status {response.status_code}.",
                        status_code=502,
                    )

                data = response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError) as e:
                    logger.error("Unexpected response payload format from NVIDIA API: %s", str(e))
                    raise ProviderAPIError("Invalid response structure received from NVIDIA API.", status_code=502) from e

        return await _call()

    async def generate_plan(self, request: GenerateRequest) -> AnimationPlan:
        """Generates an animation plan from an initial prompt."""
        if not self.is_configured:
            logger.info("NVIDIA API key not configured. Returning realistic mock plan.")
            return generate_mock_plan(request)

        messages = build_generate_messages(request)
        raw_text = await self._post_chat_completion(messages)
        parsed_dict = extract_and_parse_json(raw_text)

        # Ensure parameters match request
        parsed_dict["runtime"] = request.runtime
        parsed_dict["mood"] = request.mood
        parsed_dict["audience"] = request.audience
        parsed_dict["complexity"] = request.complexity

        try:
            return AnimationPlan(**parsed_dict)
        except ValidationError as e:
            logger.error("Pydantic validation failed on model output: %s", str(e))
            raise ProviderJSONParseError(f"Generated plan did not meet structure requirements: {e.errors()[0]['msg']}") from e

    async def revise_plan(self, request: ReviseRequest) -> AnimationPlan:
        """Revises an existing animation plan based on user delta instructions."""
        if not self.is_configured:
            logger.info("NVIDIA API key not configured. Applying mock revision.")
            # Create a revised copy with updated title and note
            revised = request.previous_plan.model_copy(deep=True)
            revised.title = f"{revised.title} (Revised)"
            if revised.scenes:
                last_scene = revised.scenes[-1]
                last_scene.description = f"{last_scene.description} [Revised: {request.revision_instruction[:60]}]"
            return revised

        messages = build_revise_messages(request)
        raw_text = await self._post_chat_completion(messages)
        parsed_dict = extract_and_parse_json(raw_text)

        # Preserve previous constraints unless updated
        if "runtime" not in parsed_dict:
            parsed_dict["runtime"] = request.previous_plan.runtime
        if "mood" not in parsed_dict:
            parsed_dict["mood"] = request.previous_plan.mood
        if "audience" not in parsed_dict:
            parsed_dict["audience"] = request.previous_plan.audience
        if "complexity" not in parsed_dict:
            parsed_dict["complexity"] = request.previous_plan.complexity

        try:
            return AnimationPlan(**parsed_dict)
        except ValidationError as e:
            logger.error("Pydantic validation failed on revised model output: %s", str(e))
            raise ProviderJSONParseError(f"Revised plan failed structure requirements: {e.errors()[0]['msg']}") from e


provider_adapter = NvidiaProviderAdapter()
