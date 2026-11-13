# mini_time_range_overlap

Compute the intersection and union of multiple datetime ranges.

```python
from datetime import datetime
from mini_time_range_overlap import TimeRange, intersection, union, total_duration

morning = TimeRange(datetime(2024, 1, 1, 9), datetime(2024, 1, 1, 12))
afternoon = TimeRange(datetime(2024, 1, 1, 11), datetime(2024, 1, 1, 14))

evening = TimeRange(datetime(2024, 1, 1, 18), datetime(2024, 1, 1, 20))

common = intersection([morning, afternoon])
# TimeRange(datetime(2024, 1, 1, 11, 0), datetime(2024, 1, 1, 12, 0))

combined = union([morning, afternoon, evening])
# [TimeRange(2024-01-01 09:00, 2024-01-01 14:00),
#  TimeRange(2024-01-01 18:00, 2024-01-01 20:00)]

print(total_duration([morning, afternoon, evening]))
# 7:00:00
```

## Why this exists

Scheduling code constantly needs to answer two questions: *when is everyone
free at the same time?* and *when is anyone busy?* Doing that with raw
datetimes means re-implementing the same comparisons, sorting, and
coalescing logic in every project, and getting the boundary conditions
wrong. This library fixes one boundary convention and implements it once.

Every range is **half-open**: `[start, end)`. That single decision means
`[09:00, 10:00)` and `[10:00, 11:00)` do **not** overlap, but their union is
`[09:00, 11:00)`. Real schedules behave that way: a meeting ending at 10:00
and another starting at 10:00 are back-to-back, not concurrent. The
trade-off is that a zero-length range is impossible; `TimeRange` raises
`InvalidRangeError` rather than silently accepting a start equal to its end.

## API

The package exports `TimeRange`, `InvalidRangeError`, `intersection`,
`union`, `merge`, and `total_duration`.

- `TimeRange(start, end)` — half-open interval. `start` must be strictly
  before `end` or `InvalidRangeError` is raised. Has `.start`, `.end`,
  `.duration`, `.overlaps(other)`, `.intersection(other)` (returns a
  `TimeRange` or `None`), and `.union(other)` (merges touching ranges,
  returns `None` for a gap).
- `intersection(ranges)` — the common overlap of every range, or `None` if
  the input is empty or any pair is disjoint.
- `merge(ranges)` — sorted list of disjoint `TimeRange` objects with
  overlapping and touching ranges coalesced.
- `union(ranges)` — alias for `merge`; returns the same sorted list.
- `total_duration(ranges)` — a `timedelta` counting overlapping time once.

All the n-ary functions accept either `TimeRange` instances or plain
`(start, end)` tuples, so callers can pass raw pairs without wrapping them.

## The awkward edge

Because ranges are half-open, `[09:00, 10:00)` and `[10:00, 11:00)` touch
without overlapping. `TimeRange.overlaps` returns `False` for them, and
`TimeRange.union` returns `[09:00, 11:00)`. `merge` and `union` follow the
same rule and join touching ranges. If you expected touching ranges to stay
separate, this library is not for you; the convention is deliberate and
tested.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

