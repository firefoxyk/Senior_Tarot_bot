import os


def get_admin_ids() -> set[int]:
    raw_admin_ids = os.getenv("ADMIN_IDS", "")
    separators = str.maketrans({",": " ", ";": " ", "\n": " "})
    normalized_admin_ids = raw_admin_ids.translate(separators)

    admin_ids: set[int] = set()

    for value in normalized_admin_ids.split():
        try:
            admin_ids.add(int(value))
        except ValueError:
            continue

    return admin_ids


def is_admin_user(user_id: int) -> bool:
    return user_id in get_admin_ids()
