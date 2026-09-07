# -*- coding: utf-8 -*-
"""Name → part registry.

Exists so that plugging in a new algorithm **does not touch existing files**.
One line — `@ACQUISITIONS.register("XX")` — and the part shows up in the
screen list, the report, and the reproduction script automatically.

Deliberately small. No plugin loading, no dependency injection — the number
of parts this program will ever take is countable on one hand, and anything
beyond that is debt.
"""
from __future__ import annotations

from typing import Callable, Generic, Iterator, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """A collection of labeled classes. Registration order is display order."""

    def __init__(self, what: str):
        self.what = what
        self._items: dict[str, type[T]] = {}

    def register(self, name: str) -> Callable[[type[T]], type[T]]:
        def wrap(cls: type[T]) -> type[T]:
            if name in self._items:
                raise ValueError(f"{self.what} '{name}' is already registered")   # i18n: skip (a programming mistake)
            cls.name = name                       # type: ignore[attr-defined]
            self._items[name] = cls
            return cls
        return wrap

    def create(self, name: str, **kwargs) -> T:
        """Build a part by name. An unknown name **tells you what exists.**"""
        if name not in self._items:
            raise KeyError(
                f"Unknown {self.what}: '{name}'. Available — {', '.join(self._items)}")   # i18n: skip (a programming mistake)
        return self._items[name](**kwargs)

    def label_of(self, name: str) -> str:
        return getattr(self._items[name], "label", name)

    def names(self) -> list[str]:
        return list(self._items)

    def __contains__(self, name: object) -> bool:
        return name in self._items

    def __iter__(self) -> Iterator[tuple[str, type[T]]]:
        return iter(self._items.items())

    def __len__(self) -> int:
        return len(self._items)
