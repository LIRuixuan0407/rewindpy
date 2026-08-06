def remove_even_numbers(numbers):
    for number in numbers:
        if number % 2 == 0:
            numbers.remove(number)
    return numbers


result = remove_even_numbers([2, 4, 6])
assert result == [], f"Expected an empty list, got {result}"
