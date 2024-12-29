from typing import TypedDict


class Person(TypedDict):
    name: str
    age: int


person: Person = {
    "name": "John",
    "Age": 50,
    "job_title": "Manager",
}  # Type-safe dictionary, static linters like mypy can detect this
