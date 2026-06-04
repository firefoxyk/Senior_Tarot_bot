import json
import random

from pathlib import Path
from typing import Any, Dict, List


Card = Dict[str, Any]

BASE_DIR = Path(__file__).resolve().parent.parent
CARDS_DIR = BASE_DIR / "cards"

DECK_FILES = [
    CARDS_DIR / "major.json",
    CARDS_DIR / "wands.json",
    CARDS_DIR / "cups.json",
    CARDS_DIR / "swords.json",
    CARDS_DIR / "pentacles.json",
]


SPREADS = {
    "spread": {
        "title": "🃏 Общий расклад",
        "intro": "Смотрим, что происходит в коде, душе и на проде...",
        "positions": [
            {
                "title": "1. Что в коде",
                "field": "meaning",
            },
            {
                "title": "2. Что в душе",
                "field": "advice",
            },
            {
                "title": "3. Что на проде",
                "field": "outcome",
            },
        ],
    },
    "career": {
        "title": "💼 Карьерный расклад",
        "intro": "Смотрим карьерный путь: рост, препятствия и итог.",
        "positions": [
            {
                "title": "1. Текущая ситуация",
                "field": "meaning",
            },
            {
                "title": "2. Что помогает",
                "field": "helping",
            },
            {
                "title": "3. Что мешает",
                "field": "blocking",
            },
            {
                "title": "4. Совет",
                "field": "advice",
            },
            {
                "title": "5. Итог",
                "field": "outcome",
            },
        ],
    },
    "project": {
        "title": "🚀 Расклад на проект",
        "intro": "Смотрим судьбу проекта, риски и шанс успешного релиза.",
        "positions": [
            {
                "title": "1. Состояние проекта",
                "field": "meaning",
            },
            {
                "title": "2. Главный риск",
                "field": "blocking",
            },
            {
                "title": "3. Что спасёт релиз",
                "field": "helping",
            },
            {
                "title": "4. Что думает тимлид",
                "field": "advice",
            },
            {
                "title": "5. Чем всё закончится",
                "field": "outcome",
            },
        ],
    },
}


def load_cards() -> List[Card]:
    cards: List[Card] = []

    for deck_file in DECK_FILES:
        if not deck_file.exists():
            raise FileNotFoundError(f"Файл колоды не найден: {deck_file}")

        with deck_file.open("r", encoding="utf-8") as file:
            deck_cards = json.load(file)

        if not isinstance(deck_cards, list):
            raise ValueError(f"Файл {deck_file} должен содержать JSON-массив карт")

        cards.extend(deck_cards)

    return cards


CARDS = load_cards()


def ensure_deck_has_cards(required_count: int) -> None:
    if len(CARDS) < required_count:
        raise ValueError(
            f"В колоде недостаточно карт. Нужно минимум {required_count}, сейчас: {len(CARDS)}"
        )


def draw_cards(count: int) -> List[Card]:
    ensure_deck_has_cards(count)
    return random.sample(CARDS, count)


def get_card_text(card: Card, field: str) -> str:
    value = card.get(field)

    if isinstance(value, str) and value.strip():
        return value

    return card.get("meaning", "Толкование для этой позиции пока не заполнено.")


def get_daily_prediction(card: Card, is_reversed: bool) -> str:
    field = "reversed_meaning" if is_reversed else "meaning"
    value = card.get(field)

    if isinstance(value, str) and value.strip():
        return value

    return card.get("meaning", "Предсказание для этой карты пока не заполнено.")


def get_card_display_name(card: Card, is_reversed: bool = False) -> str:
    name = card["name"]

    if is_reversed:
        return f"{name} (перевёрнутая)"

    return name