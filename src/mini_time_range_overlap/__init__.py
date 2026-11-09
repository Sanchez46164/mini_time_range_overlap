"""Public surface for mini_time_range_overlap.

Only the names re-exported here are part of the supported API.
"""

from .core import (
    TimeRange,
    InvalidRangeError,
    intersection,
    union,
    merge,
    total_duration,
)

__all__ = [
    "TimeRange",
    "InvalidRangeError",
    "intersection",
    "union",
    "merge",
    "total_duration",
]
