from typing import TypedDict


class Person(TypedDict):
    name: str
    age: int


person: Person = {
    "name": "Alice",
    "age": "wrong",
}  # Type-safe dictionary, static linters like mypy can detect this
