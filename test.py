import unittest

import line
import point
import polygon


class TestPoint(unittest.TestCase):
    def test_point_eq(self):
        self.assertEqual(point.Point((1, 1)), point.Point((1.0, 1.0)))
        self.assertNotEqual(point.Point((1, 1)), point.Point((1.0001, 1.0)))


class TestLine(unittest.TestCase):
    def assertPointEqual(self, a, b):
        self.assertAlmostEqual(a[0], b[0])
        self.assertAlmostEqual(a[1], b[1])

    def test_in_bound(self):
        with self.assertRaises(ValueError):
            line.in_bound((2, 1), (2, 1), (1, 1))

        # Horizontal
        assert line.in_bound((1, 2), (5, 2), (3, 2)) is None
        assert line.in_bound((1, 2), (5, 2), (3, 3)) is False
        assert line.in_bound((1, 2), (5, 2), (3, 1)) is True

        # Vertical
        assert line.in_bound((-1, 2), (-1, 5), (-1, 4)) is None
        assert line.in_bound((-1, 2), (-1, 5), (3, 3)) is True
        assert line.in_bound((-1, 2), (-1, 5), (-5, 7)) is False

        # Non-orthogonal
        assert line.in_bound((1, 2), (4, 1), (3, 2)) is False
        assert line.in_bound((1, 2), (4, 1), (-1, 2)) is True
        assert line.in_bound((1, 2), (4, 1), (3, 4/3)) is None
        assert line.in_bound((-1, 2), (-4, 1), (-3, 2)) is True
        assert line.in_bound((-1, 2), (-4, 1), (0, 2)) is False

    def test_intersects_h(self):
        self.assertTrue(line.intersects_h((0, 0), (2, 2), 1))
        self.assertTrue(line.intersects_h((2, 2), (0, 0), 1))
        self.assertFalse(line.intersects_h((-1, -1), (5, -1), -1))
        self.assertFalse(line.intersects_h((2, 2), (0, 2), 1))
        self.assertFalse(line.intersects_h((0, 0), (-1, -1), 1))

    def test_get_intercept_h(self):
        self.assertEqual(line.get_intercept_h((1, 1), (3, 3), 2), 2)
        self.assertEqual(line.get_intercept_h((3, 4), (5, 1), 2), 13/3)

    def test_get_intersection(self):
        # Vertical/horizontal
        a = line.Line((3, 3), (3, 4))
        b = line.Line((9, 9), (7, 9))
        expect = (3, 9)
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        # Both vertical
        b = line.Line((7, 7), (7, 5))
        self.assertIsNone(a.get_intersection(b))
        self.assertIsNone(b.get_intersection(a))

        # Vertical/non-orthogonal
        b = line.Line((1, 2), (5, 3))
        expect = (3, 2.5)
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        b = line.Line((4, 5), (5, 2))
        expect = (3, 8)
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        # Both horizontal
        a = line.Line((1, 2), (4, 2))
        b = line.Line((5, 6), (6, 6))
        self.assertIsNone(a.get_intersection(b))
        self.assertIsNone(b.get_intersection(a))

        # Horizontal/vertical
        b = line.Line((9, 3), (9, -1))
        expect = (9, 2)
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        # Horizontal/non-orthogonal
        b = line.Line((9, 3), (10, 5))
        expect = (8.5, 2)
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        # Both non-orthogonal
        a = line.Line((0, 1), (4, 2))
        b = line.Line((2, 4), (4, 3))
        expect = (5 + 1/3, 2 + 1/3)
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        a = -a
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.get_intersection(b), expect)
        self.assertPointEqual(b.get_intersection(a), expect)


class TestPolygon(unittest.TestCase):
    def test_is_convex(self):
        # simple triangle
        poly = [(1, 2), (3, 5), (4, 1), (1, 2)]
        assert polygon.is_convex(poly) is True

        # octagon centred on (0, 0)
        poly = [
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
                (1, 2),
                ]
        assert polygon.is_convex(poly) is True

        # definitely non-convex
        poly = [
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ]
        assert polygon.is_convex(poly) is False

    def test_in_bbox(self):
        bbox = (-100/3, -47.1027895, 5, 22.9)
        self.assertTrue(polygon.in_bbox(bbox, (0, 0)))
        self.assertTrue(polygon.in_bbox(bbox, (-33.3333333333, 22.9)))
        self.assertFalse(polygon.in_bbox(bbox, (-33.3333333333, 22.9), False))
        self.assertFalse(polygon.in_bbox(bbox, (6, 0)))

    def test_divide_polygon(self):
        poly = [
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ]
        with self.assertRaises(ValueError):
            polygon.divide_polygon(poly, 0, 0)
        with self.assertRaises(ValueError):
            polygon.divide_polygon(poly, 0, 1)
        with self.assertRaises(ValueError):
            polygon.divide_polygon(poly, 4, 3)
        with self.assertRaises(ValueError):
            polygon.divide_polygon(poly, -1, 3)
        with self.assertRaises(ValueError):
            polygon.divide_polygon(poly, 4, 9)
        with self.assertRaises(ValueError):
            polygon.divide_polygon(poly, 7, 0)

        self.assertEqual(
                polygon.divide_polygon(poly, 0, 3),
                (
                    [(1, 1), (1, 6), (2, 5), (2, 2), (1, 1)],
                    [(1, 1), (2, 2), (4, 2), (3, 4), (5, 4), (4, 0), (1, 1)],
                    ))
        self.assertEqual(
                polygon.divide_polygon(poly, 4, 8),
                (
                    [(4, 2), (3, 4), (5, 4), (4, 0), (1, 1), (4, 2)],
                    [(1, 1), (1, 6), (2, 5), (2, 2), (4, 2), (1, 1)],
                    ))
        self.assertEqual(
                polygon.divide_polygon(poly, 4, 7),
                (
                    [(4, 2), (3, 4), (5, 4), (4, 0), (4, 2)],
                    [(1, 1), (1, 6), (2, 5), (2, 2), (4, 2), (4, 0), (1, 1)],
                    ))

    def test_shift_polygon(self):
        # simple triangle
        poly = [(1, 2), (3, 5), (4, 1), (1, 2)]
        self.assertEqual(polygon.shift_polygon(poly, 0), poly)

        shift1 = [(3, 5), (4, 1), (1, 2), (3, 5)]
        shift2 = [(4, 1), (1, 2), (3, 5), (4, 1)]
        self.assertEqual(polygon.shift_polygon(poly, 1), shift1)
        self.assertEqual(polygon.shift_polygon(poly, 2), shift2)
        self.assertEqual(polygon.shift_polygon(poly, 3), poly)
        self.assertEqual(polygon.shift_polygon(poly, 4), shift1)

    def test_point_in_polygon(self):
        with self.assertRaises(ValueError):
            polygon.point_in_polygon([(1, 2)], (3, 4))

        # simple triangle
        poly = [(1, 2), (3, 5), (4, 1), (1, 2)]
        self.assertTrue(polygon.point_in_polygon(poly, (3, 2)))
        self.assertFalse(polygon.point_in_polygon(poly, (2, 4)))

        # octagon centred on (0, 0)
        poly = [
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
                (1, 2),
                ]
        self.assertTrue(polygon.point_in_polygon(poly, (1, 1)))
        self.assertTrue(polygon.point_in_polygon(poly, (1, -1)))
        self.assertTrue(polygon.point_in_polygon(poly, (-1, -1)))
        self.assertTrue(polygon.point_in_polygon(poly, (-1, 1)))
        self.assertFalse(polygon.point_in_polygon(poly, (2, 2)))

        # horseshoe
        poly = [
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ]
        expect = (
                (False, False, False, False,  True, False, False),
                (False,  True,  True,  True,  True, False, False),
                (False,  True,  True,  True,  True, False, False),
                (False,  True,  True, False,  True, False, False),
                (False,  True,  True,  True,  True,  True, False),
                (False,  True,  True, False, False, False, False),
                (False,  True, False, False, False, False, False),
                )
        for y in range(len(expect)):
            for x in range(len(expect[y])):
                self.assertIs(
                        polygon.point_in_polygon(poly, (x, y)),
                        expect[y][x],
                        f"({x}, {y})")
