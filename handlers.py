import json
import random
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

from database import add_user
from keyboards import main_menu_keyboard


router = Router()

Card = Dict[str, Any]


BASE_DIR = Path(__file__).resolve().parent
CARDS_DIR = BASE_DIR / "cards"

DECK_FILES = [
    CARDS_DIR / "major.json",
    CARDS_DIR / "wands.json",
    CARDS_DIR / "cups.json",
    CARDS_DIR / "swords.json",
    CARDS_DIR / "pentacles.json",
]


def create_reversed_image(image_path: Path) -> Path:
    with Image.open(image_path) as img:
        rotated = img.rotate(180, expand=True)

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        )

        temp_path = Path(temp_file.name)
        temp_file.close()

        rotated.save(temp_path)

    return temp_path


def create_spread_collage(cards: List[Card]) -> Path:
    """
    Создаёт один коллаж для расклада из 3 или 5 карт.

    Для 3 карт:
    [1][2][3]

    Для 5 карт:
    [1][2][3]
       [4][5]
    """
    card_width = 260
    card_height = 390
    padding = 30

    count = len(cards)

    if count == 3:
        cols = 3
        rows = 1
        positions = [
            (0, 0),
            (1, 0),
            (2, 0),
        ]
    elif count == 5:
        cols = 3
        rows = 2
        positions = [
            (0, 0),
            (1, 0),
            (2, 0),
            (0.5, 1),
            (1.5, 1),
        ]
    else:
        cols = count
        rows = 1
        positions = [(index, 0) for index in range(count)]

    canvas_width = cols * card_width + (cols + 1) * padding
    canvas_height = rows * card_height + (rows + 1) * padding

    canvas = Image.new("RGB", (canvas_width, canvas_height), "#111111")

    for index, card in enumerate(cards):
        image_path = BASE_DIR / card["image"]

        if not image_path.exists():
            continue

        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail((card_width, card_height))

            x_index, y_index = positions[index]

            x = int(padding + x_index * (card_width + padding))
            y = int(padding + y_index * (card_height + padding))

            card_background = Image.new("RGB", (card_width, card_height), "#222222")

            background_x = x
            background_y = y

            image_x = x + (card_width - img.width) // 2
            image_y = y + (card_height - img.height) // 2

            canvas.paste(card_background, (background_x, background_y))
            canvas.paste(img, (image_x, image_y))

    temp_file = tempfile.NamedTemporaryFile(
        suffix=".jpg",
        delete=False,
    )

    temp_path = Path(temp_file.name)
    temp_file.close()

    canvas.save(temp_path, quality=95)

    return temp_path


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


WELCOME_TEXT = """
🔮 <b>Senior Tarot</b>

Мем-таро для программистов: расклады про код, баги, дедлайны и карьеру в IT.

Никакой магии — только мемы, программирование и немного цифрового мистицизма ⚡️

Выбери действие ниже:
"""


HELP_TEXT = """
ℹ️ <b>Помощь по Senior Tarot</b>

<b>Команды:</b>

/start — начать гадание и открыть главное меню
/card — вытянуть карту дня
/spread — общий расклад из 3 карт
/career — карьерный расклад из 5 карт
/project — расклад на проект из 5 карт
/help — показать помощь

<b>Расклады:</b>

🃏 <b>Общий расклад</b>
1. Что в коде
2. Что в душе
3. Что на проде

💼 <b>Карьера</b>
1. Текущая ситуация
2. Что помогает
3. Что мешает
4. Совет
5. Итог

🚀 <b>Проект</b>
1. Состояние проекта
2. Главный риск
3. Что спасёт релиз
4. Что думает тимлид
5. Чем всё закончится
"""


SPREADS = {
    "spread": {
        "title": "🃏 Общий расклад",
        "intro": "Смотрим, что происходит в коде, душе и на проде...",
        "positions": [
            {
                "title": "1. Что в коде",
                "hint": "Текущее состояние задач, архитектуры, багов и технического хаоса.",
                "field": "meaning",
            },
            {
                "title": "2. Что в душе",
                "hint": "Твоё внутреннее состояние как разработчика.",
                "field": "advice",
            },
            {
                "title": "3. Что на проде",
                "hint": "Чего ждать от релиза, инфраструктуры и внезапных инцидентов.",
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
                "hint": "Где ты сейчас находишься в профессиональном развитии.",
                "field": "meaning",
            },
            {
                "title": "2. Что помогает",
                "hint": "Твой главный ресурс, навык или обстоятельство.",
                "field": "helping",
            },
            {
                "title": "3. Что мешает",
                "hint": "То, что тормозит рост, повышение или переход на новый уровень.",
                "field": "blocking",
            },
            {
                "title": "4. Совет",
                "hint": "Что стоит сделать прямо сейчас.",
                "field": "advice",
            },
            {
                "title": "5. Итог",
                "hint": "К чему всё идёт, если продолжить текущий путь.",
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
                "hint": "Что реально происходит с проектом сейчас.",
                "field": "meaning",
            },
            {
                "title": "2. Главный риск",
                "hint": "Что может сломать сроки, релиз или команду.",
                "field": "blocking",
            },
            {
                "title": "3. Что спасёт релиз",
                "hint": "Что поможет довести проект до результата.",
                "field": "helping",
            },
            {
                "title": "4. Что думает тимлид",
                "hint": "Скрытый взгляд руководства, команды или менеджмента.",
                "field": "advice",
            },
            {
                "title": "5. Чем всё закончится",
                "hint": "Наиболее вероятный исход проекта.",
                "field": "outcome",
            },
        ],
    },
}


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


async def send_card(
    message: Message,
    card: Card,
    title: str | None = None,
    is_reversed: bool = False,
) -> None:
    image_path = BASE_DIR / card["image"]

    card_name = get_card_display_name(card, is_reversed)
    prediction = get_daily_prediction(card, is_reversed)

    caption = f"""
🔮 <b>{title or "Карта"}</b>

🃏 <b>{card_name}</b>

📖 <b>Описание</b>
{card['description']}

🔮 <b>Предсказание</b>
{prediction}
"""

    if image_path.exists():
        if is_reversed:
            reversed_image_path = create_reversed_image(image_path)
            photo = FSInputFile(reversed_image_path)
        else:
            photo = FSInputFile(image_path)

        await message.answer_photo(
            photo=photo,
            caption=caption,
        )
    else:
        await message.answer(
            f"{caption}\n\n⚠️ Изображение не найдено: <code>{card['image']}</code>"
        )


async def send_single_card(message: Message) -> None:
    card = draw_cards(1)[0]
    is_reversed = random.choice([True, False])

    await send_card(
        message=message,
        card=card,
        title="Карта дня",
        is_reversed=is_reversed,
    )


async def send_spread(message: Message, spread_key: str) -> None:
    spread = SPREADS[spread_key]
    positions = spread["positions"]
    cards = draw_cards(len(positions))

    collage_path = create_spread_collage(cards)

    text_parts = [
        f"<b>{spread['title']}</b>",
        spread["intro"],
    ]

    for position, card in zip(positions, cards):
        field = position.get("field", "meaning")
        interpretation = get_card_text(card, field)

        text_parts.append(
            f"""
<b>{position['title']}</b>
🃏 {card['name']}
{interpretation}
""".strip()
        )

    caption = "\n\n".join(text_parts)

    await message.answer_photo(
        photo=FSInputFile(collage_path),
        caption=caption,
    )


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    user = message.from_user

    if user:
        add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
        )

    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        HELP_TEXT,
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("card"))
async def cmd_card(message: Message) -> None:
    await send_single_card(message)


@router.message(Command("spread"))
async def cmd_spread(message: Message) -> None:
    await send_spread(message, "spread")


@router.message(Command("career"))
async def cmd_career(message: Message) -> None:
    await send_spread(message, "career")


@router.message(Command("project"))
async def cmd_project(message: Message) -> None:
    await send_spread(message, "project")


@router.callback_query(F.data == "card")
async def callback_card(callback: CallbackQuery) -> None:
    await callback.answer()

    if callback.message:
        await send_single_card(callback.message)


@router.callback_query(F.data == "spread")
async def callback_spread(callback: CallbackQuery) -> None:
    await callback.answer()

    if callback.message:
        await send_spread(callback.message, "spread")


@router.callback_query(F.data == "career")
async def callback_career(callback: CallbackQuery) -> None:
    await callback.answer()

    if callback.message:
        await send_spread(callback.message, "career")


@router.callback_query(F.data == "project")
async def callback_project(callback: CallbackQuery) -> None:
    await callback.answer()

    if callback.message:
        await send_spread(callback.message, "project")


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery) -> None:
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            HELP_TEXT,
            reply_markup=main_menu_keyboard(),
        )
