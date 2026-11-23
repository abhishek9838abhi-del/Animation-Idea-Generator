"""Domain schemas and validation models for Frame by Frame."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class RuntimeEnum(str, Enum):
    THIRTY_SECONDS = "30s"
    ONE_MINUTE = "1m"
    THREE_MINUTES = "3m"


class MoodEnum(str, Enum):
    FUNNY = "funny"
    HEARTWARMING = "heartwarming"
    MYSTERIOUS = "mysterious"
    ADVENTUROUS = "adventurous"


class AudienceEnum(str, Enum):
    CHILDREN = "children"
    TEENS = "teens"
    GENERAL = "general"


class ComplexityEnum(str, Enum):
    SIMPLE = "simple"
    DETAILED = "detailed"


class Character(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Character name")
    role: str = Field(..., min_length=1, max_length=100, description="Role in the short animation")
    goal: str = Field(..., min_length=1, max_length=150, description="Immediate objective or desire")

    @field_validator("name", "role", "goal", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or purely whitespace.")
            return cleaned
        return v


class Scene(BaseModel):
    scene_number: int = Field(..., ge=1, description="Sequential scene number")
    description: str = Field(
        ..., min_length=5, max_length=500, description="Visual action and character staging"
    )
    visual_suggestion: str = Field(
        ..., min_length=5, max_length=350, description="Camera framing, lighting, or style note"
    )
    dialogue: Optional[str] = Field(
        default=None, max_length=300, description="Spoken line or narration, or null if silent"
    )
    sound_suggestions: Optional[List[str]] = Field(
        default_factory=list, description="Foley sound effects or musical cues"
    )

    @field_validator("description", "visual_suggestion", mode="before")
    @classmethod
    def strip_text(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Scene description/visual suggestion cannot be empty.")
            return cleaned
        return v


class AnimationPlan(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Short title")
    logline: str = Field(..., min_length=10, max_length=350, description="1-2 sentence core premise")
    runtime: RuntimeEnum = Field(..., description="Target runtime category")
    mood: MoodEnum = Field(..., description="Dominant emotional tone")
    audience: AudienceEnum = Field(..., description="Target audience tier")
    complexity: ComplexityEnum = Field(..., description="Production complexity level")
    characters: List[Character] = Field(
        ..., min_length=1, max_length=5, description="Primary characters"
    )
    scenes: List[Scene] = Field(
        ..., min_length=2, max_length=10, description="Scene-by-scene outline"
    )
    sound_suggestions: Optional[List[str]] = Field(
        default_factory=list, description="Overall sound design and musical palette"
    )

    @field_validator("title", "logline", mode="before")
    @classmethod
    def strip_title_logline(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Title and logline cannot be empty.")
            return cleaned
        return v


class GenerateRequest(BaseModel):
    idea: str = Field(..., min_length=5, max_length=500, description="User rough story idea")
    runtime: RuntimeEnum = Field(default=RuntimeEnum.ONE_MINUTE)
    mood: MoodEnum = Field(default=MoodEnum.HEARTWARMING)
    audience: AudienceEnum = Field(default=AudienceEnum.GENERAL)
    has_dialogue: bool = Field(default=False)
    complexity: ComplexityEnum = Field(default=ComplexityEnum.SIMPLE)

    @field_validator("idea", mode="before")
    @classmethod
    def clean_idea(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if len(cleaned) < 5:
                raise ValueError("Story idea must be at least 5 characters long.")
            return cleaned
        return v


class ReviseRequest(BaseModel):
    previous_plan: AnimationPlan = Field(..., description="The current animation plan to revise")
    revision_instruction: str = Field(
        ..., min_length=3, max_length=300, description="Specific revision directive"
    )

    @field_validator("revision_instruction", mode="before")
    @classmethod
    def clean_instruction(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if len(cleaned) < 3:
                raise ValueError("Revision instruction must be at least 3 characters long.")
            return cleaned
        return v


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[object] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
