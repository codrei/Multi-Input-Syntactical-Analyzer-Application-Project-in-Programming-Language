# Exceptions, context managers, match statements and other statements.
import os
import sys as system
from math import pi, sqrt

value = 5; other = 6  # two statements on one line


def check(item):
    global value
    assert item is not None, "item is required"
    try:
        result = 10 / item
    except ZeroDivisionError as error:
        print("Cannot divide:", error)
        result = None
    except (TypeError, ValueError):
        raise
    else:
        print("ok")
    finally:
        value += 1
    return result


with open(os.devnull) as handle, open(os.devnull) as other_handle:
    pass

match value:
    case 0:
        print("zero")
    case 1 | 2:
        print("small")
    case [first, *others]:
        print(first, others)
    case {"key": key}:
        print(key)
    case _:
        print("other")

long_expression = (1 +
                   2 +
                   3)
continued_line = 1 + \
    2
del long_expression
print(system.version, pi, sqrt(2))
