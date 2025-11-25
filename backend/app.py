"""
Context Genie backend service.

Provides suggestion endpoints for both the high-fidelity Context Genie prototype and
the control condition. The service optionally integrates with an LLM (e.g. OpenAI) when
an API key is supplied, but also ships with deterministic fallbacks so that designers can
demo the UI without external dependencies.
"""
from __future__ import annotations

import os
import json
from functools import lru_cache
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

# --- Models -----------------------------------------------------------------


class Suggestion(BaseModel):
    text: str
    language: str = Field(description="Language or tone tag, e.g. en, ru, slang.")
    label: str = Field(description="Badge label shown in the pill.")
    explanation: str = Field(
        description="Short rationale the frontend can surface in tooltips."
    )
    auto_apply: bool = Field(
        default=False,
        alias="autoApply",
        description="When true, aggressive mode may auto-insert this suggestion.",
    )
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)

    class Config:
        populate_by_name = True


class ContextGenieRequest(BaseModel):
    text: str = Field(default="", description="Current composer contents.")
    cursor_word: Optional[str] = Field(
        default=None, alias="cursorWord", description="Token currently being edited."
    )
    conversation: List[str] = Field(
        default_factory=list,
        description="Recent conversation turns for additional context.",
    )
    mode: str = Field(default="balanced", description="passive | balanced | aggressive.")
    language_preferences: List[str] = Field(
        default_factory=list,
        alias="languagePreferences",
        description="Ordered language preference codes from the UI.",
    )
    tone: str = Field(
        default="neutral",
        description="Desired tone (casual, neutral, formal) as requested by the user.",
    )
    transliteration: bool = Field(
        default=True,
        description="Whether non-English text should be transliterated into Latin characters.",
    )
    api_key: Optional[str] = Field(
        default=None,
        alias="apiKey",
        description="Optional OpenAI-style API key supplied by the client.",
    )

    class Config:
        populate_by_name = True


class ControlRequest(BaseModel):
    text: str = ""
    cursor_word: Optional[str] = Field(default=None, alias="cursorWord")

    class Config:
        populate_by_name = True


class SuggestionResponse(BaseModel):
    mode: str
    used_llm: bool = Field(alias="usedLLM")
    suggestions: List[Suggestion]
    auto_override: Optional[str] = Field(
        default=None,
        alias="autoOverride",
        description="Auto-applied text for aggressive mode overrides.",
    )

    class Config:
        populate_by_name = True


# --- App setup --------------------------------------------------------------

app = FastAPI(
    title="Context Genie API",
    version="0.2.0",
    description="Backend to power multilingual autocorrect suggestions.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- LLM integration --------------------------------------------------------


@lru_cache
def _has_openai_sdk() -> bool:
    try:
        import openai  # noqa: F401

        return True
    except ImportError:
        return False


def call_llm(
    prompt: str,
    api_key: Optional[str],
) -> Optional[List[Suggestion]]:
    """
    Attempt to call an OpenAI compatible endpoint and parse structured suggestions.

    Returns None on failure so the caller can fallback to handcrafted suggestions.
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    if not _has_openai_sdk():
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        response = client.responses.create(
            model=os.getenv("CONTEXT_GENIE_MODEL", "gpt-4o-mini"),
            input=[
                {
                    "role": "system",
                    "content": (
                        "You power a multilingual keyboard suggestion bar. "
                        "Respond with raw JSON only, no code blocks or prose. "
                        "Structure: {\"suggestions\": [{\"text\": str, \"language\": str, "
                        "\"label\": str, \"explanation\": str, \"autoApply\": bool, "
                        "\"confidence\": number}]}. "
                        "Limit to 4 items, keep slang when requested, and respect transliterations."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        message = response.output[0].content[0].text
        try:
            raw = json.loads(message)
        except json.JSONDecodeError:
            return None

        items = raw.get("suggestions")
        if not isinstance(items, list):
            return None

        structured: List[Suggestion] = []
        for item in items:
            try:
                structured.append(Suggestion.model_validate(item))
            except ValidationError:
                continue

        return structured or None
    except Exception:
        # Silently degrade to heuristics; logging can be added if needed.
        return None


# --- Fallback heuristics ----------------------------------------------------

SLANG_CHOICES = {
    "yu": Suggestion(
        text="Yu",
        language="slang",
        label="SL",
        explanation="Keeping relaxed tone for close friends.",
    ),
    "imma": Suggestion(
        text="Imma",
        language="slang",
        label="SL",
        explanation="US slang contraction for informal plans.",
    ),
    "wassup": Suggestion(
        text="Wassup!",
        language="slang",
        label="SL",
        explanation="Friendly slang alternative to “What’s up?”.",
    ),
}

MULTILINGUAL_CHOICES = {
    "kak": [
        Suggestion(
            text="Как дела?",
            language="ru",
            label="RU",
            explanation="Standard Cyrillic greeting in Russian.",
        ),
        Suggestion(
            text="Kak dilá?",
            language="id",
            label="ID",
            explanation="Bahasa slang spelling preserving intent.",
        ),
        Suggestion(
            text="Как ты?",
            language="ru",
            label="RU",
            explanation="Alternative Russian phrasing for familiarity.",
        ),
        Suggestion(
            text="Kak are you?",
            language="blend",
            label="Mix",
            explanation="Code-mixed playful suggestion using English and transliteration.",
        ),
    ],
    "priv": [
        Suggestion(
            text="Привет!",
            language="ru",
            label="RU",
            explanation="Primary greeting in Russian.",
        ),
        Suggestion(
            text="Privet 🤗",
            language="emoji",
            label="🙂",
            explanation="Adds emoji flair while staying informal.",
        ),
        Suggestion(
            text="Hey!",
            language="en",
            label="EN",
            explanation="Switch back to English tone.",
        ),
        Suggestion(
            text="Halo!",
            language="id",
            label="ID",
            explanation="Indonesian casual greeting.",
        ),
    ],
    "im": [
        Suggestion(
            text="I'm",
            language="en",
            label="EN",
            explanation="Standard English contraction.",
        ),
        SLANG_CHOICES["imma"],
        Suggestion(
            text="Я",
            language="ru",
            label="RU",
            explanation="Russian equivalent in Cyrillic.",
        ),
        Suggestion(
            text="Saya",
            language="id",
            label="ID",
            explanation="Neutral Bahasa Indonesian pronoun.",
        ),
    ],
    "ya": [
        Suggestion(
            text="Я",
            language="ru",
            label="RU",
            explanation="Switches to Cyrillic for Russian.",
        ),
        Suggestion(
            text="ya",
            language="slang",
            label="SL",
            explanation="Keeps informal Latin transliteration.",
        ),
        Suggestion(
            text="I",
            language="en",
            label="EN",
            explanation="Reverts to neutral English tone.",
        ),
        Suggestion(
            text="yaaa 🤟",
            language="emoji",
            label="🙂",
            explanation="Stylized slang variant with emoji.",
        ),
    ],
    "wass": [
        Suggestion(
            text="What's up?",
            language="en",
            label="EN",
            explanation="Standard English autocorrect.",
        ),
        SLANG_CHOICES["wassup"],
        Suggestion(
            text="Как ты?",
            language="ru",
            label="RU",
            explanation="Switches tone to Russian informal.",
        ),
        Suggestion(
            text="Apa kabar?",
            language="id",
            label="ID",
            explanation="Formal Bahasa greeting.",
        ),
    ],
    "ty": [
        Suggestion(
            text="ты",
            language="ru",
            label="RU",
            explanation="Informal Russian 'you'.",
        ),
        Suggestion(
            text="tu",
            language="slang",
            label="Mix",
            explanation="Code-mixed Spanglish tone.",
        ),
        Suggestion(
            text="you",
            language="en",
            label="EN",
            explanation="Standard English correction.",
        ),
        Suggestion(
            text="kamu",
            language="id",
            label="ID",
            explanation="Neutral Bahasa Indonesian address.",
        ),
    ],
}

DEFAULT_SUGGESTIONS = [
    SLANG_CHOICES["yu"],
    Suggestion(
        text="I'm",
        language="en",
        label="EN",
        explanation="Standard correction for English typing.",
    ),
    Suggestion(
        text="Ты",
        language="ru",
        label="RU",
        explanation="Cyrillic alternative using capitalized form.",
    ),
    SLANG_CHOICES["imma"],
]


def fallback_suggestions(trigger: str) -> List[Suggestion]:
    lowered = trigger.lower()
    for key, suggestions in MULTILINGUAL_CHOICES.items():
        if lowered.startswith(key):
            return suggestions
    return DEFAULT_SUGGESTIONS


# --- Endpoint implementations ----------------------------------------------


@app.post("/api/context-genie/suggest", response_model=SuggestionResponse)
async def suggest_context_genie(payload: ContextGenieRequest) -> SuggestionResponse:
    """
    Main endpoint powering the Context Genie prototype.

    When an API key is supplied the backend will attempt to call an OpenAI-compatible
    model for richer suggestions; otherwise it falls back to curated heuristics.
    """
    cursor = None
    if payload.cursor_word:
        cursor = payload.cursor_word.strip()
    elif payload.text:
        try:
            cursor = payload.text.split()[-1].strip()
        except IndexError:
            pass
    if not cursor:
        return SuggestionResponse(
            mode=payload.mode,
            used_llm=False,
            suggestions=[],
            auto_override=None,
        )

    prompt = (
        f"Conversation so far: {payload.conversation}\n"
        f"Current draft: {payload.text!r}\n"
        f"Cursor word: {cursor!r}\n"
        f"Mode: {payload.mode}\n"
        f"Tone: {payload.tone}\n"
        f"Transliteration: {'on' if payload.transliteration else 'off'}\n"
        f"Language preferences: {payload.language_preferences}\n"
        "Return suggestions that keep intent, respect slang, and show multiple languages."
    )

    suggestions = call_llm(prompt, payload.api_key)
    used_llm = suggestions is not None

    if not suggestions:
        suggestions = fallback_suggestions(cursor)

    # Adjust auto-apply flag based on mode
    if payload.mode == "aggressive" and suggestions:
        suggestions = [
            suggestions[0].model_copy(update={"auto_apply": True}, deep=True),
            *suggestions[1:],
        ]
        auto_override = suggestions[0].text
    else:
        suggestions = [
            suggestion.model_copy(update={"auto_apply": False}, deep=True)
            for suggestion in suggestions
        ]
        auto_override = None

    return SuggestionResponse(
        mode=payload.mode,
        used_llm=used_llm,
        suggestions=suggestions,
        auto_override=auto_override,
    )


@app.post("/api/control/suggest", response_model=SuggestionResponse)
async def suggest_control(payload: ControlRequest) -> SuggestionResponse:
    """
    Simpler endpoint for the control prototype.

    Attempts a light-touch LLM call for basic spelling/autocorrect suggestions.
    Falls back to deterministic options when the model is unavailable.
    """
    cursor = None
    if payload.cursor_word:
        cursor = payload.cursor_word.strip()
    elif payload.text:
        try:
            cursor = payload.text.split()[-1].strip()
        except IndexError:
            pass

    normalized_cursor = cursor or ""
    used_llm = False
    suggestions: List[Suggestion] = []

    if normalized_cursor:
        prompt = (
            "You are the stock autocorrect engine on a phone keyboard. "
            "Provide up to three short English suggestions for the current word. "
            "Only fix spelling, capitalization, apostrophes, or simple punctuation. "
            "Never change tone, add slang, or translate into other languages.\n\n"
            f"Full draft: {payload.text!r}\n"
            f"Current word: {normalized_cursor!r}\n"
            "Respond with JSON of the form {\"suggestions\": [{\"text\": str, "
            "\"language\": \"en\", \"label\": \"EN\", \"explanation\": str, "
            "\"autoApply\": false, \"confidence\": number}]}"
        )
        llm_result = call_llm(prompt, getattr(payload, "api_key", None))
        if llm_result:
            used_llm = True
            suggestions = llm_result

    if not suggestions:
        suggestions = fallback_suggestions(normalized_cursor)

    trimmed = [
        suggestion.model_copy(update={"auto_apply": False}, deep=True)
        for suggestion in suggestions[:3]
    ]

    return SuggestionResponse(
        mode="control",
        used_llm=used_llm,
        suggestions=trimmed,
        auto_override=None,
    )
