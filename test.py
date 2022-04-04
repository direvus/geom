import unittest

import geom


class TestPoint(unittest.TestCase):
    def test_point_eq(self):
        self.assertEqual(geom.Point((1, 1)), geom.Point((1.0, 1.0)))
        self.assertNotEqual(geom.Point((1, 1)), geom.Point((1.0001, 1.0)))


class TestLine(unittest.TestCase):
    def assertPointEqual(self, a, b):
        self.assertAlmostEqual(a[0], b[0])
        self.assertAlmostEqual(a[1], b[1])

    def test_constructor(self):
        with self.assertRaises(ValueError):
            geom.Line((3, 5), (3.0, 5.0))

    def test_in_bound(self):
        with self.assertRaises(ValueError):
            geom.in_bound((2, 1), (2, 1), (1, 1))

        # Horizontal
        assert geom.in_bound((1, 2), (5, 2), (3, 2)) is None
        assert geom.in_bound((1, 2), (5, 2), (3, 3)) is False
        assert geom.in_bound((1, 2), (5, 2), (3, 1)) is True

        # Vertical
        assert geom.in_bound((-1, 2), (-1, 5), (-1, 4)) is None
        assert geom.in_bound((-1, 2), (-1, 5), (3, 3)) is True
        assert geom.in_bound((-1, 2), (-1, 5), (-5, 7)) is False

        # Non-orthogonal
        assert geom.in_bound((1, 2), (4, 1), (3, 2)) is False
        assert geom.in_bound((1, 2), (4, 1), (-1, 2)) is True
        assert geom.in_bound((1, 2), (4, 1), (3, 4/3)) is None
        assert geom.in_bound((-1, 2), (-4, 1), (-3, 2)) is True
        assert geom.in_bound((-1, 2), (-4, 1), (0, 2)) is False

    def test_intersects_h(self):
        self.assertTrue(geom.Line((0, 0), (2, 2)).intersects_y(1))
        self.assertTrue(geom.Line((2, 2), (0, 0)).intersects_y(1))
        self.assertFalse(geom.Line((-1, -1), (5, -1)).intersects_y(-1))
        self.assertFalse(geom.Line((2, 2), (0, 2)).intersects_y(1))
        self.assertFalse(geom.Line((0, 0), (-1, -1)).intersects_y(1))

    def test_get_intercept_h(self):
        self.assertEqual(geom.Line((1, 1), (3, 3)).get_y_intercept(2), 2)
        self.assertEqual(geom.Line((3, 4), (5, 1)).get_y_intercept(2), 13/3)

    def test_extrapolate_intersection(self):
        # Vertical/horizontal
        a = geom.Line((3, 3), (3, 4))
        b = geom.Line((9, 9), (7, 9))
        expect = (3, 9)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        # Both vertical
        b = geom.Line((7, 7), (7, 5))
        self.assertIsNone(a.extrapolate_intersection(b))
        self.assertIsNone(b.extrapolate_intersection(a))

        # Vertical/non-orthogonal
        b = geom.Line((1, 2), (5, 3))
        expect = (3, 2.5)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        b = geom.Line((4, 5), (5, 2))
        expect = (3, 8)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        # Both horizontal
        a = geom.Line((1, 2), (4, 2))
        b = geom.Line((5, 6), (6, 6))
        self.assertIsNone(a.extrapolate_intersection(b))
        self.assertIsNone(b.extrapolate_intersection(a))

        # Horizontal/vertical
        b = geom.Line((9, 3), (9, -1))
        expect = (9, 2)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        # Horizontal/non-orthogonal
        b = geom.Line((9, 3), (10, 5))
        expect = (8.5, 2)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        # Both non-orthogonal
        a = geom.Line((0, 1), (4, 2))
        b = geom.Line((2, 4), (4, 3))
        expect = (5 + 1/3, 2 + 1/3)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        a = -a
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

    def test_intersects_point(self):
        # Vertical
        line = geom.Line((3, 3), (3, 4))
        self.assertTrue(line.intersects_point(geom.Point(3, 3.5)))
        self.assertFalse(line.intersects_point(geom.Point(4, 3)))

        # Horizontal
        line = geom.Line((-2, -2), (2, -2))
        self.assertTrue(line.intersects_point(geom.Point(0, -2)))
        self.assertFalse(line.intersects_point(geom.Point(0, -1.999)))

        # Other
        line = geom.Line((0, 0), (2, 2))
        self.assertTrue(line.intersects_point(geom.Point(1, 1)))
        self.assertFalse(line.intersects_point(geom.Point(3, 3)))


class TestBoundingBox(unittest.TestCase):
    def test_contains(self):
        bbox = geom.BoundingBox(-2, -7/3, 3.1, 6)
        f = bbox.contains
        self.assertTrue(f(geom.Point(0, 0)))
        self.assertFalse(f(geom.Point(0, 6)))
        self.assertFalse(f(geom.Point(12, -8)))

        self.assertTrue(f(geom.Line((0, 0), (1, 1))))
        self.assertFalse(f(geom.Line((0, 0), (7, 7))))
        self.assertFalse(f(geom.Line((-3, 0), (-4, 1))))
        # geom.Lines on the boundary are not contained
        self.assertFalse(f(geom.Line((3.1000000001, 0), (3.1000000001, -1))))

        self.assertTrue(f(geom.BoundingBox(0, 0, 1, 1)))
        self.assertFalse(f(geom.BoundingBox(0, 0, 1000, 1000)))
        self.assertFalse(f(geom.BoundingBox(-7, -7, -6, -6)))

        # A shape contains itself
        self.assertTrue(f(bbox))

        poly = geom.Polygon([(-1, -1), (0, 3), (3, 0), (-1, -1)])
        self.assertTrue(f(poly))
        poly = geom.Polygon([(6, 6), (7, 10), (10, 7), (6, 6)])
        self.assertFalse(f(poly))


class TestPolygon(unittest.TestCase):
    def test_constructor(self):
        # not enough distinct points
        with self.assertRaises(ValueError):
            poly = geom.Polygon([(1, 2), (1, 2), (3, 5), (1, 2)])

        # backtracking
        with self.assertRaises(ValueError):
            poly = geom.Polygon([(1, 2), (3, 6), (2, 4)])

        # self-intersection
        with self.assertRaises(ValueError):
            poly = geom.Polygon([(1, 2), (3, 6), (5, 4), (-1, 4), (1, 2)])

        # simple triangle
        poly = geom.Polygon([(1, 2), (3, 5), (4, 1), (1, 2)])
        self.assertEqual(len(poly), 4)

    def test_is_convex(self):
        # simple triangle
        poly = [(1, 2), (3, 5), (4, 1), (1, 2)]
        assert geom.is_convex(poly) is True

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
        assert geom.is_convex(poly) is True

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
        assert geom.is_convex(poly) is False

    def test_in_bbox(self):
        bbox = (-100/3, -47.1027895, 5, 22.9)
        self.assertTrue(geom.in_bbox(bbox, (0, 0)))
        self.assertTrue(geom.in_bbox(bbox, (-33.3333333333, 22.9)))
        self.assertFalse(geom.in_bbox(bbox, (-33.3333333333, 22.9), False))
        self.assertFalse(geom.in_bbox(bbox, (6, 0)))

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
            geom.divide_polygon(poly, 0, 0)
        with self.assertRaises(ValueError):
            geom.divide_polygon(poly, 0, 1)
        with self.assertRaises(ValueError):
            geom.divide_polygon(poly, 4, 3)
        with self.assertRaises(ValueError):
            geom.divide_polygon(poly, -1, 3)
        with self.assertRaises(ValueError):
            geom.divide_polygon(poly, 4, 9)
        with self.assertRaises(ValueError):
            geom.divide_polygon(poly, 7, 0)

        self.assertEqual(
                geom.divide_polygon(poly, 0, 3),
                (
                    [(1, 1), (1, 6), (2, 5), (2, 2), (1, 1)],
                    [(1, 1), (2, 2), (4, 2), (3, 4), (5, 4), (4, 0), (1, 1)],
                    ))
        self.assertEqual(
                geom.divide_polygon(poly, 4, 8),
                (
                    [(4, 2), (3, 4), (5, 4), (4, 0), (1, 1), (4, 2)],
                    [(1, 1), (1, 6), (2, 5), (2, 2), (4, 2), (1, 1)],
                    ))
        self.assertEqual(
                geom.divide_polygon(poly, 4, 7),
                (
                    [(4, 2), (3, 4), (5, 4), (4, 0), (4, 2)],
                    [(1, 1), (1, 6), (2, 5), (2, 2), (4, 2), (4, 0), (1, 1)],
                    ))

    def test_shift_polygon(self):
        # simple triangle
        poly = [(1, 2), (3, 5), (4, 1), (1, 2)]
        self.assertEqual(geom.shift_polygon(poly, 0), poly)

        shift1 = [(3, 5), (4, 1), (1, 2), (3, 5)]
        shift2 = [(4, 1), (1, 2), (3, 5), (4, 1)]
        self.assertEqual(geom.shift_polygon(poly, 1), shift1)
        self.assertEqual(geom.shift_polygon(poly, 2), shift2)
        self.assertEqual(geom.shift_polygon(poly, 3), poly)
        self.assertEqual(geom.shift_polygon(poly, 4), shift1)

    def test_point_in_polygon(self):
        # simple triangle
        poly = [(1, 2), (3, 5), (4, 1), (1, 2)]
        self.assertTrue(geom.point_in_polygon(poly, (3, 2)))
        self.assertFalse(geom.point_in_polygon(poly, (2, 4)))

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
        self.assertTrue(geom.point_in_polygon(poly, (1, 1)))
        self.assertTrue(geom.point_in_polygon(poly, (1, -1)))
        self.assertTrue(geom.point_in_polygon(poly, (-1, -1)))
        self.assertTrue(geom.point_in_polygon(poly, (-1, 1)))
        self.assertFalse(geom.point_in_polygon(poly, (2, 2)))

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
                        geom.point_in_polygon(poly, (x, y)),
                        expect[y][x],
                        f"({x}, {y})")
