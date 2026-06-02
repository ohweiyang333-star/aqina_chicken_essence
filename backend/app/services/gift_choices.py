"""French Poulet gift choice normalization for Aqina offer-reset orders."""
from __future__ import annotations

import re
from typing import Any


GIFT_CHOICES: tuple[dict[str, str], ...] = (
    {
        "code": "joint-wing",
        "name": "French Poulet 3 Joint Wing",
        "weight": "500g",
        "display_name": "French Poulet 3 Joint Wing 500g",
    },
    {
        "code": "minced",
        "name": "French Poulet Minced",
        "weight": "400g",
        "display_name": "French Poulet Minced 400g",
    },
    {
        "code": "boneless-breast",
        "name": "French Poulet Boneless Breast",
        "weight": "350g",
        "display_name": "French Poulet Boneless Breast 350g",
    },
    {
        "code": "whole-leg",
        "name": "French Poulet Whole Leg",
        "weight": "400g",
        "display_name": "French Poulet Whole Leg 400g",
    },
    {
        "code": "half-chicken",
        "name": "French Poulet Half Chicken Cut 4 Pieces",
        "weight": "500g",
        "display_name": "French Poulet Half Chicken Cut 4 Pieces 500g",
    },
)

_CHOICES_BY_CODE = {choice["code"]: choice for choice in GIFT_CHOICES}

_ALIASES: dict[str, tuple[str, ...]] = {
    "joint-wing": (
        "jointwing",
        "3joint",
        "3jointwing",
        "threejoint",
        "wing",
        "chickenwing",
        "三节翅",
        "三節翅",
        "鸡翅",
        "雞翅",
    ),
    "minced": (
        "minced",
        "mince",
        "mincedmeat",
        "chickenminced",
        "chickenmince",
        "肉碎",
        "鸡肉碎",
        "雞肉碎",
        "鸡碎",
        "雞碎",
    ),
    "boneless-breast": (
        "bonelessbreast",
        "breast",
        "chickenbreast",
        "breastmeat",
        "鸡胸",
        "雞胸",
        "鸡胸肉",
        "雞胸肉",
        "去骨鸡胸",
        "去骨雞胸",
    ),
    "whole-leg": (
        "wholeleg",
        "chickenleg",
        "leg",
        "整只鸡腿",
        "整只雞腿",
        "全鸡腿",
        "全雞腿",
        "鸡腿",
        "雞腿",
    ),
    "half-chicken": (
        "halfchicken",
        "4pieces",
        "4piece",
        "4cut",
        "fourpieces",
        "halfcutted",
        "halfcut",
        "半只鸡",
        "半隻雞",
        "半只",
        "半隻",
        "半鸡",
        "半雞",
        "切块",
        "切塊",
        "四块",
        "四塊",
    ),
}


def normalize_gift_choice(value: Any) -> dict[str, str] | None:
    """Return a canonical gift choice dict from a string/dict/customer phrase."""
    if value is None:
        return None

    if isinstance(value, dict):
        for key in ("code", "id", "value"):
            matched = _match_choice(value.get(key))
            if matched:
                return matched
        for key in ("display_name", "displayName", "name", "label", "text"):
            matched = _match_choice(value.get(key))
            if matched:
                return matched
        return None

    return _match_choice(value)


def allowed_gift_choice_prompt_payload() -> list[dict[str, str]]:
    """Small prompt-safe list of choices for the chatbot JSON contract."""
    return [dict(choice) for choice in GIFT_CHOICES]


def _match_choice(value: Any) -> dict[str, str] | None:
    normalized = _normalize_text(value)
    if not normalized:
        return None

    if normalized in _CHOICES_BY_CODE:
        return dict(_CHOICES_BY_CODE[normalized])

    for choice in GIFT_CHOICES:
        choice_tokens = {
            _normalize_text(choice["code"]),
            _normalize_text(choice["name"]),
            _normalize_text(choice["display_name"]),
        }
        if normalized in choice_tokens or any(token and token in normalized for token in choice_tokens):
            return dict(choice)

    for code, aliases in _ALIASES.items():
        if any(alias and alias in normalized for alias in aliases):
            return dict(_CHOICES_BY_CODE[code])

    return None


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip().casefold()
    if not text:
        return ""
    return re.sub(r"[\s_\-/,，。.:：;；()（）+]+", "", text)
