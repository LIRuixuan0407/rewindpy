def warm_up() -> int:
    total = 0
    for number in range(80):
        total += number
    return total


def normalize_user(data: dict[str, str]) -> dict[str, str]:
    normalized = dict(data)
    normalized["userid"] = normalized.pop("user_id")
    return normalized


def create_account(data: dict[str, str]) -> str:
    return data["user_id"]


warm_up()
user = normalize_user({"user_id": "1024", "name": "Alex"})
create_account(user)
