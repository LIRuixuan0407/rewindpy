def normalize_user(raw):
    normalized = dict(raw)
    normalized["userid"] = normalized.pop("user_id")
    return normalized


def create_account(data):
    return {"id": data["user_id"], "name": data["name"]}


def main():
    payload = {"user_id": "1024", "name": "Alex", "api_key": "demo-secret"}
    cleaned = normalize_user(payload)
    return create_account(cleaned)


main()
