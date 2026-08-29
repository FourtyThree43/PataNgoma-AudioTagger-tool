"""Event bus for decoupled application and domain events."""

from __future__ import annotations

import contextlib
from collections import defaultdict
from collections.abc import Callable

from patangoma.domain.models import DomainEvent


class EventBus:
    """Publish-subscribe event bus for framework-neutral events."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[DomainEvent], None]]] = defaultdict(
            list
        )
        self._all_subscribers: list[Callable[[DomainEvent], None]] = []

    def subscribe(
        self, event_type: str, handler: Callable[[DomainEvent], None]
    ) -> None:
        """Subscribe to a specific event type."""
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe to all published events."""
        self._all_subscribers.append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all relevant subscribers."""
        for handler in self._subscribers.get(event.event_type, []):
            with contextlib.suppress(Exception):
                handler(event)

        for handler in self._all_subscribers:
            with contextlib.suppress(Exception):
                handler(event)

    def clear(self) -> None:
        """Clear all event subscriptions."""
        self._subscribers.clear()
        self._all_subscribers.clear()
