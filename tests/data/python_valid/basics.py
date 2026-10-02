# Basic statements: assignment, arithmetic, conditions and loops.
x = 10
y = 3
total = x + y * 2 - (x // y) % 4 ** 2
average = total / 2.5
is_valid = x > 5 and not y == 0 or x <= -1

if (x > 5):
    print("Value is valid")
elif x == 5:
    print('Exactly five')
else:
    print("Too small")

count = 0
while count < 3:
    count += 1
    if count == 2:
        continue
    print("count =", count)

for i in range(1, 10, 2):
    if i > 7:
        break
    print(i, end=" ")
else:
    print()

name = "Ada" if x else input("Name: ")
print(f"Hello, {name}! You scored {average:.2f} points.")
