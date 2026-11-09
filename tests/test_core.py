import unittest
from datetime import datetime, timedelta

from mini_time_range_overlap import (
    InvalidRangeError,
    TimeRange,
    intersection,
    merge,
    total_duration,
    union,
)


def dt(hour: int, minute: int = 0) -> datetime:
    """Fixed reference date; tests never rely on the wall clock."""
    return datetime(2024, 1, 1, hour, minute)


class TestConstruction(unittest.TestCase):
    def test_start_must_precede_end(self):
        with self.assertRaises(InvalidRangeError):
            TimeRange(dt(10), dt(10))
        with self.assertRaises(InvalidRangeError):
            TimeRange(dt(11), dt(10))

    def test_duration(self):
        r = TimeRange(dt(9), dt(10, 30))
        self.assertEqual(r.duration, timedelta(hours=1, minutes=30))

    def test_equality_and_hash(self):
        a = TimeRange(dt(9), dt(10))
        b = TimeRange(dt(9), dt(10))
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertNotEqual(a, TimeRange(dt(9), dt(11)))


class TestOverlap(unittest.TestCase):
    def test_overlaps_true(self):
        a = TimeRange(dt(9), dt(11))
        b = TimeRange(dt(10), dt(12))
        self.assertTrue(a.overlaps(b))
        self.assertTrue(b.overlaps(a))

    def test_adjacent_half_open_ranges_do_not_overlap(self):
        a = TimeRange(dt(9), dt(10))
        b = TimeRange(dt(10), dt(11))
        self.assertFalse(a.overlaps(b))
        self.assertFalse(b.overlaps(a))

    def test_contained_range_overlaps(self):
        outer = TimeRange(dt(9), dt(17))
        inner = TimeRange(dt(12), dt(13))
        self.assertTrue(outer.overlaps(inner))
        self.assertTrue(inner.overlaps(outer))


class TestPairwiseIntersection(unittest.TestCase):
    def test_intersection_returns_overlap(self):
        a = TimeRange(dt(9), dt(11))
        b = TimeRange(dt(10), dt(12))
        self.assertEqual(a.intersection(b), TimeRange(dt(10), dt(11)))

    def test_intersection_none_when_disjoint(self):
        a = TimeRange(dt(9), dt(10))
        b = TimeRange(dt(11), dt(12))
        self.assertIsNone(a.intersection(b))

    def test_intersection_none_when_touching(self):
        a = TimeRange(dt(9), dt(10))
        b = TimeRange(dt(10), dt(11))
        self.assertIsNone(a.intersection(b))


class TestPairwiseUnion(unittest.TestCase):
    def test_union_overlapping(self):
        a = TimeRange(dt(9), dt(11))
        b = TimeRange(dt(10), dt(12))
        self.assertEqual(a.union(b), TimeRange(dt(9), dt(12)))

    def test_union_touching_merges(self):
        a = TimeRange(dt(9), dt(10))
        b = TimeRange(dt(10), dt(11))
        self.assertEqual(a.union(b), TimeRange(dt(9), dt(11)))

    def test_union_disjoint_is_none(self):
        a = TimeRange(dt(9), dt(10))
        b = TimeRange(dt(11), dt(12))
        self.assertIsNone(a.union(b))


class TestNaryIntersection(unittest.TestCase):
    def test_empty_input(self):
        self.assertIsNone(intersection([]))

    def test_single_range(self):
        r = TimeRange(dt(9), dt(10))
        self.assertEqual(intersection([r]), r)

    def test_common_overlap(self):
        ranges = [
            TimeRange(dt(9), dt(12)),
            TimeRange(dt(10), dt(13)),
            TimeRange(dt(11), dt(14)),
        ]
        self.assertEqual(intersection(ranges), TimeRange(dt(11), dt(12)))

    def test_no_common_overlap(self):
        ranges = [
            TimeRange(dt(9), dt(10)),
            TimeRange(dt(10), dt(11)),
        ]
        self.assertIsNone(intersection(ranges))

    def test_accepts_tuples(self):
        ranges = [
            (dt(9), dt(12)),
            (dt(10), dt(13)),
        ]
        self.assertEqual(intersection(ranges), TimeRange(dt(10), dt(12)))


class TestMerge(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(merge([]), [])

    def test_single(self):
        r = TimeRange(dt(9), dt(10))
        self.assertEqual(merge([r]), [r])

    def test_coalesces_overlapping_and_touching(self):
        ranges = [
            TimeRange(dt(9), dt(10)),
            TimeRange(dt(10), dt(11)),
            TimeRange(dt(10, 30), dt(12)),
            TimeRange(dt(14), dt(15)),
        ]
        self.assertEqual(
            merge(ranges),
            [TimeRange(dt(9), dt(12)), TimeRange(dt(14), dt(15))],
        )

    def test_contained_range_is_absorbed(self):
        ranges = [
            TimeRange(dt(9), dt(17)),
            TimeRange(dt(12), dt(13)),
        ]
        self.assertEqual(merge(ranges), [TimeRange(dt(9), dt(17))])

    def test_output_is_sorted(self):
        ranges = [
            TimeRange(dt(14), dt(15)),
            TimeRange(dt(9), dt(10)),
        ]
        self.assertEqual(
            merge(ranges),
            [TimeRange(dt(9), dt(10)), TimeRange(dt(14), dt(15))],
        )


class TestUnion(unittest.TestCase):
    def test_union_is_merge(self):
        ranges = [
            TimeRange(dt(9), dt(10)),
            TimeRange(dt(10), dt(11)),
            TimeRange(dt(14), dt(15)),
        ]
        self.assertEqual(union(ranges), merge(ranges))
        self.assertEqual(
            union(ranges),
            [TimeRange(dt(9), dt(11)), TimeRange(dt(14), dt(15))],
        )

    def test_union_empty(self):
        self.assertEqual(union([]), [])


class TestTotalDuration(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(total_duration([]), timedelta(0))

    def test_counts_overlaps_once(self):
        ranges = [
            TimeRange(dt(9), dt(11)),
            TimeRange(dt(10), dt(12)),
        ]
        self.assertEqual(total_duration(ranges), timedelta(hours=3))

    def test_touching_ranges_are_contiguous(self):
        ranges = [
            TimeRange(dt(9), dt(10)),
            TimeRange(dt(10), dt(11)),
        ]
        self.assertEqual(total_duration(ranges), timedelta(hours=2))

    def test_disjoint_ranges_sum(self):
        ranges = [
            TimeRange(dt(9), dt(10)),
            TimeRange(dt(14), dt(15)),
        ]
        self.assertEqual(total_duration(ranges), timedelta(hours=2))


class TestTypeErrors(unittest.TestCase):
    def test_rejects_non_range_input(self):
        with self.assertRaises(TypeError):
            merge(["not a range"])

    def test_rejects_wrong_tuple_arity(self):
        with self.assertRaises(TypeError):
            merge([(dt(9),)])


if __name__ == "__main__":
    unittest.main()
