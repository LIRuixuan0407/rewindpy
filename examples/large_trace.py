def noisy_work() -> dict[str, str]:
    total = 0
    for index in range(20_000):
        total += index

    data = {"userid": str(total)}
    return data


result = noisy_work()
print(result["user_id"])
