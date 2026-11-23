"""Unit tests for domain schemas and validation bounds."""

import pytest
from pydantic import ValidationError
from app.schemas import (
    GenerateRequest,
    ReviseRequest,
    AnimationPlan,
    Character,
    Scene,
    RuntimeEnum,
    MoodEnum,
    AudienceEnum,
    ComplexityEnum,
)


def test_character_validation_valid():
    char = Character(name="Barnaby", role="Small cloud", goal="Join storm")
    assert char.name == "Barnaby"
    assert char.role == "Small cloud"
    assert char.goal == "Join storm"


def test_character_validation_empty_whitespace():
    with pytest.raises(ValidationError):
        Character(name="   ", role="Small cloud", goal="Join storm")


def test_scene_validation_valid():
    scene = Scene(
        scene_number=1,
        description="A tiny cloud floats across a dark horizon looking for friends.",
        visual_suggestion="Wide panning landscape shot with soft ambient light.",
        dialogue=None,
        sound_suggestions=["Distant thunder"],
    )
    assert scene.scene_number == 1
    assert scene.dialogue is None


def test_scene_validation_negative_number():
    with pytest.raises(ValidationError):
        Scene(
            scene_number=0,
            description="Valid description here",
            visual_suggestion="Valid visual suggestion",
        )


def test_generate_request_valid():
    req = GenerateRequest(
        idea="A timid robot discovers a dying flower in an abandoned steel factory.",
        runtime=RuntimeEnum.ONE_MINUTE,
        mood=MoodEnum.HEARTWARMING,
        audience=AudienceEnum.GENERAL,
        has_dialogue=False,
        complexity=ComplexityEnum.SIMPLE,
    )
    assert req.idea.startswith("A timid robot")
    assert req.runtime == RuntimeEnum.ONE_MINUTE


def test_generate_request_idea_too_short():
    with pytest.raises(ValidationError) as exc:
        GenerateRequest(
            idea="Tiny",  # 4 chars, min is 5
            runtime=RuntimeEnum.ONE_MINUTE,
            mood=MoodEnum.FUNNY,
            audience=AudienceEnum.CHILDREN,
            has_dialogue=False,
            complexity=ComplexityEnum.SIMPLE,
        )
    assert "at least 5 characters" in str(exc.value)


def test_generate_request_idea_too_long():
    with pytest.raises(ValidationError):
        GenerateRequest(
            idea="x" * 501,  # max is 500
            runtime=RuntimeEnum.ONE_MINUTE,
            mood=MoodEnum.FUNNY,
            audience=AudienceEnum.CHILDREN,
            has_dialogue=False,
            complexity=ComplexityEnum.SIMPLE,
        )


def test_revise_request_validation():
    plan = AnimationPlan(
        title="Sparks Fly",
        logline="A tiny spark wants to create an aurora borealis across the Arctic sky.",
        runtime=RuntimeEnum.THIRTY_SECONDS,
        mood=MoodEnum.FUNNY,
        audience=AudienceEnum.CHILDREN,
        complexity=ComplexityEnum.SIMPLE,
        characters=[
            Character(name="Sparky", role="A little spark", goal="Light up the sky")
        ],
        scenes=[
            Scene(
                scene_number=1,
                description="Sparky leaps into the cold air with high enthusiasm.",
                visual_suggestion="Close-up with glowing particle trails.",
            ),
            Scene(
                scene_number=2,
                description="Sparky collides with a snowflake and creates an unexpected rainbow.",
                visual_suggestion="Wide dynamic reveal shot.",
            ),
        ],
        sound_suggestions=["Sparkling chime"],
    )

    # Valid revision
    rev = ReviseRequest(previous_plan=plan, revision_instruction="Make the ending more comedic")
    assert rev.revision_instruction == "Make the ending more comedic"

    # Too short revision instruction
    with pytest.raises(ValidationError):
        ReviseRequest(previous_plan=plan, revision_instruction="No")
