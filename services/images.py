import tempfile

from pathlib import Path
from typing import Any, Dict, List

from PIL import Image


Card = Dict[str, Any]


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


def create_spread_collage(cards: List[Card], base_dir: Path) -> Path:
    card_width = 260
    card_height = 390
    padding = 30

    count = len(cards)

    if count == 3:
        cols = 3
        rows = 1
        positions = [(0, 0), (1, 0), (2, 0)]
    elif count == 5:
        cols = 3
        rows = 2
        positions = [(0, 0), (1, 0), (2, 0), (0.5, 1), (1.5, 1)]
    else:
        cols = count
        rows = 1
        positions = [(index, 0) for index in range(count)]

    canvas_width = cols * card_width + (cols + 1) * padding
    canvas_height = rows * card_height + (rows + 1) * padding

    canvas = Image.new("RGB", (canvas_width, canvas_height), "#111111")

    for index, card in enumerate(cards):
        image_path = base_dir / card["image"]

        if not image_path.exists():
            continue

        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img.thumbnail((card_width, card_height))

            x_index, y_index = positions[index]

            x = int(padding + x_index * (card_width + padding))
            y = int(padding + y_index * (card_height + padding))

            card_background = Image.new("RGB", (card_width, card_height), "#222222")

            image_x = x + (card_width - img.width) // 2
            image_y = y + (card_height - img.height) // 2

            canvas.paste(card_background, (x, y))
            canvas.paste(img, (image_x, image_y))

    temp_file = tempfile.NamedTemporaryFile(
        suffix=".jpg",
        delete=False,
    )

    temp_path = Path(temp_file.name)
    temp_file.close()

    canvas.save(temp_path, quality=95)

    return temp_path