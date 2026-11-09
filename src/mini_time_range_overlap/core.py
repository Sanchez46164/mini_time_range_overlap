"""Core time range overlap logic.

A range is half-open: ``[start, end)``.  This choice keeps intersections of
adjacent ranges empty (``[0,1)`` and ``[1,2)`` do not overlap) and makes the
union of adjacent ranges a single range rather than two touching ones.  The
whole module is built around that single decision.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple


class InvalidRangeError(ValueError):
    """Raised when a range is constructed with start >= end."""


class TimeRange:
    """A half-open datetime interval ``[start, end)``.

    ``start`` must be strictly before ``end``.  Zero-length ranges are
    rejected because they are indistinguishable from an empty set and would
    make union/merge results ambiguous.
    """

    __slots__ = ("_start", "_end")

    def __init__(self, start: datetime, end: datetime) -> None:
        if start >= end:
            raise InvalidRangeError(
                f"start ({start!r}) must be strictly before end ({end!r})"
            )
        self._start = start
        self._end = end

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def end(self) -> datetime:
        return self._end

    @property
    def duration(self) -> timedelta:
        return self._end - self._start

    def overlaps(self, other: "TimeRange") -> bool:
        """True when the two half-open ranges share at least one instant."""
        return self._start < other._end and other._start < self._end

    def intersection(self, other: "TimeRange") -> Optional["TimeRange"]:
        """Return the overlap, or ``None`` when the ranges are disjoint."""
        start = max(self._start, other._start)
        end = min(self._end, other._end)
        if start >= end:
            return None
        return TimeRange(start, end)

    def union(self, other: "TimeRange") -> Optional["TimeRange"]:
        """Return the smallest range covering both, or ``None`` if disjoint.

        Touching ranges (``end == start``) merge because the ranges are
        half-open: the union of ``[0,1)`` and ``[1,2)`` is ``[0,2)``.
        """
        if not self.overlaps(other) and self._end != other._start and other._end != self._start:
            return None
        return TimeRange(min(self._start, other._start), max(self._end, other._end))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeRange):
            return NotImplemented
        return self._start == other._start and self._end == other._end

    def __hash__(self) -> int:
        return hash((self._start, self._end))

    def __repr__(self) -> str:
        return f"TimeRange({self._start!r}, {self._end!r})"


RangeLike = Tuple[datetime, datetime]


def _coerce(item: object) -> TimeRange:
    """Accept either a ``TimeRange`` or an ``(start, end)`` tuple."""
    if isinstance(item, TimeRange):
        return item
    if isinstance(item, tuple) and len(item) == 2:
        start, end = item
        return TimeRange(start, end)
    raise TypeError(f"expected TimeRange or (start, end) tuple, got {item!r}")


def intersection(ranges: Iterable[object]) -> Optional[TimeRange]:
    """Intersect every range in *ranges*.

    Returns ``None`` when the input is empty or when the ranges do not all
    share a common instant.  Accepts ``TimeRange`` instances or plain
    ``(start, end)`` tuples.
    """
    iterator: Iterator[TimeRange] = (_coerce(r) for r in ranges)
    try:
        current = next(iterator)
    except StopIteration:
        return None
    for item in iterator:
        current = current.intersection(item)
        if current is None:
            return None
    return current


def merge(ranges: Iterable[object]) -> List[TimeRange]:
    """Sort and coalesce overlapping or touching ranges.

    Adjacent half-open ranges merge, so ``[0,1)`` and ``[1,2)`` become a
    single ``[0,2)``.  Disjoint ranges are returned in ascending order.
    """
    items = sorted((_coerce(r) for r in ranges), key=lambda r: (r.start, r.end))
    if not items:
        return []
    merged: List[TimeRange] = [items[0]]
    for r in items[1:]:
        last = merged[-1]
        if r.start <= last.end:
            merged[-1] = TimeRange(last.start, max(last.end, r.end))
        else:
            merged.append(r)
    return merged


def union(ranges: Iterable[object]) -> List[TimeRange]:
    """Return the union of *ranges* as a sorted list of disjoint ranges.

    This is ``merge`` under a different name; it is kept because callers
    naturally reach for ``union`` when they mean "combine these ranges".
    """
    return merge(ranges)


def total_duration(ranges: Iterable[object]) -> timedelta:
    """Total covered time, counting overlaps only once."""
    total = timedelta(0)
    for r in merge(ranges):
        total += r.duration
    return total
