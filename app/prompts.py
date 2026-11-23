"""Prompt builder and AI safety directives for Frame by Frame."""

import json
import re
from typing import List, Dict, Any
from app.schemas import GenerateRequest, ReviseRequest, RuntimeEnum, ComplexityEnum

# Runtime to exact scene count expectations
RUNTIME_SCENE_MAPPING = {
    RuntimeEnum.THIRTY_SECONDS: "exactly 2 to 3 scenes. Focused on a single comedic beat or punchy moment.",
    RuntimeEnum.ONE_MINUTE: "exactly 4 to 5 scenes. Structured with a clear setup, escalation, and resolution.",
    RuntimeEnum.THREE_MINUTES: "exactly 6 to 8 scenes. An expanded short with escalating obstacles and character growth.",
}

# Living artist names pattern detection (for neutral style guidance)
LIVING_ARTISTS = [
    "hayao miyazaki",
    "glen keane",
    "tim burton",
    "makoto shinkai",
    "genndy tartakovsky",
    "craig mccracken",
    "rebecca sugar",
    "pendleton ward",
    "alex hirsch",
    "aaron blaise",
]


def sanitize_style_instructions(text: str) -> str:
    """Detects living artist references and provides neutral descriptor guidance."""
    lower_text = text.lower()
    for artist in LIVING_ARTISTS:
        if artist in lower_text:
            # Append neutral guidance for the model
            return (
                f"{text} (Note: Avoid direct imitation of {artist.title()}. "
                "Use neutral visual descriptors such as expressive line weight, pastel color palettes, "
                "or stylized silhouettes instead.)"
            )
    return text


SYSTEM_PROMPT = """You are an expert animation director, story supervisor, and creative mentor for indie animators, animation students, and small creative teams.
Your objective is to turn a rough premise into a structured, highly actionable, and feasible animation plan that fits the creator's constraints.

PRODUCTION CONSTRAINTS:
1. Beginner Feasibility:
   - Simple complexity: Maximum 1-2 characters, 1 main location, simple pantomime action.
   - Detailed complexity: Maximum 2-3 characters, 2-3 camera setups or micro-locations, nuanced visual acting.
   - Avoid massive crowds, complex fluid/particle physics, or hyper-dense VFX. Focus on clear staging, strong silhouettes, and squash-and-stretch principles.
2. Runtime & Pacing:
   - 30s: 2 to 3 scenes. Single narrative punch.
   - 1m: 4 to 5 scenes. Three-act mini short.
   - 3m: 6 to 8 scenes. Extended short with obstacle progression.
3. Dialogue Enforcement:
   - If has_dialogue is false: You must NOT provide spoken dialogue. Every character dialogue field must be null. Tell the story purely through visual pantomime and sound effects.
   - If has_dialogue is true: Keep spoken lines crisp, punchy, and sparse.
4. Living Artist Policy:
   - Never mimic or name a living artist. Translate any visual requests into neutral artistic descriptors (e.g. 'bold ink outlines with soft gouache textures', 'minimalist vector flat design').
5. Audience Calibration:
   - Children: Gentle stakes, playful humor or warmth, clear emotional cues.
   - Teens: Relatable dilemmas, stylized comedy or mystery.
   - General: Universal resonance, multi-layered visual storytelling.

OUTPUT FORMAT:
Respond with ONLY a single valid JSON object strictly matching this schema:
{
  "title": "Creative Short Title",
  "logline": "1-2 sentence core premise (max 350 chars)",
  "runtime": "30s|1m|3m",
  "mood": "funny|heartwarming|mysterious|adventurous",
  "audience": "children|teens|general",
  "complexity": "simple|detailed",
  "characters": [
    {
      "name": "Character Name",
      "role": "Role in the short",
      "goal": "Immediate desire"
    }
  ],
  "scenes": [
    {
      "scene_number": 1,
      "description": "Visual action and staging (max 400 chars)",
      "visual_suggestion": "Camera angle, lighting, or style note (max 300 chars)",
      "dialogue": "Spoken line or null if silent",
      "sound_suggestions": ["Sound effect or music cue"]
    }
  ],
  "sound_suggestions": [
    "Overall music palette or recurring foley motif"
  ]
}
Do not include any introductory commentary, markdown explanation, or text outside the JSON object."""


def build_generate_messages(request: GenerateRequest) -> List[Dict[str, str]]:
    """Builds the message list for the initial plan generation."""
    sanitized_idea = sanitize_style_instructions(request.idea)
    scene_guideline = RUNTIME_SCENE_MAPPING.get(
        request.runtime, "4 to 5 scenes."
    )
    dialogue_guideline = (
        "Include concise spoken dialogue or voiceover narration where essential."
        if request.has_dialogue
        else "STRICTLY SILENT / VISUAL ONLY. All dialogue fields must be null."
    )

    user_prompt = f"""Generate an animation plan for the following project:

- Story Idea: "{sanitized_idea}"
- Target Runtime: {request.runtime.value} ({scene_guideline})
- Mood: {request.mood.value}
- Target Audience: {request.audience.value}
- Dialogue: {dialogue_guideline}
- Complexity Level: {request.complexity.value}

Deliver a feasible, structured, engaging animation outline. Output strictly valid JSON."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def build_revise_messages(request: ReviseRequest) -> List[Dict[str, str]]:
    """Builds the message list for revising an existing animation plan."""
    sanitized_instruction = sanitize_style_instructions(request.revision_instruction)
    plan_json = request.previous_plan.model_dump_json(indent=2)

    user_prompt = f"""Here is the existing animation plan:
{plan_json}

The creator requested the following specific revision:
"{sanitized_instruction}"

Instructions for revision:
1. Apply the revision carefully while preserving character names, core premise, and unchanged scenes.
2. Maintain the same runtime ({request.previous_plan.runtime.value}), mood ({request.previous_plan.mood.value}), and complexity ({request.previous_plan.complexity.value}) unless the revision explicitly requested to change them.
3. Ensure the revised plan remains beginner-friendly and feasible.
4. Output strictly the updated JSON matching the exact schema."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
