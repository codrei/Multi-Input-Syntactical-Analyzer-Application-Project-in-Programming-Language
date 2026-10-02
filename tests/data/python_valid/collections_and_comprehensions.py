# Lists, dictionaries, sets, slicing and comprehensions.
numbers = [5, 3, 8, 1, 9, 2]
matrix = [
    [1, 2, 3],
    [4, 5, 6],
]
person = {"name": "Ada", "age": 36, "languages": ["Python", "Java"]}
unique = {1, 2, 3}
empty_tuple = ()
single = (1,)

evens = [n for n in numbers if n % 2 == 0]
squares = {n: n * n for n in range(5)}
flat = [cell for row in matrix for cell in row]
total = sum(n for n in numbers if n > 2)

first, *rest = numbers
a, b = 1, 2
a, b = b, a
middle = numbers[1:-1]
reversed_copy = numbers[::-1]
corner = matrix[0][-1]

if (n := len(numbers)) > 3 and 3 in numbers and 7 not in numbers and person is not None:
    print(f"{n} numbers")

merged = {**person, "city": "London"}
combined = [*numbers, *unique]
print(*numbers, sep=", ")
chained = 1 < 2 <= 3 != 4
bits = 5 & 3 | 2 ^ 1 << 2 >> 1
inverted = ~5
