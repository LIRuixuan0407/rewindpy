from __future__ import annotations


def load_users() -> list[dict[str, str]]:
    return [
        {"id": "100", "name": "Alice"},
        {"id": "200", "name": "Bob"},
    ]


def find_user(
    users: list[dict[str, str]],
    user_id: str,
) -> dict[str, str] | None:
    for user in users:
        if user["id"] == user_id:
            return user

    return None


def render_profile(user: dict[str, str]) -> str:
    return f"Welcome, {user.get('name').upper()}"


users = load_users()
current_user = find_user(users, "999")
print(render_profile(current_user))
