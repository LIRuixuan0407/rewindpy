def find_user(users, wanted_id):
    for user in users:
        if user["id"] == wanted_id:
            return user
    return None


def display_name(user):
    return user.get("name").upper()


users = [{"id": 1, "name": "Ada"}]
selected = find_user(users, 2)
print(display_name(selected))
