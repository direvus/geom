import unittest

import geom
from geom import P, L, B, Pg


class TestPoint(unittest.TestCase):
    def test_point_eq(self):
        self.assertEqual(P((1, 1)), P((1.0, 1.0)))
        self.assertNotEqual(P((1, 1)), P((1.0001, 1.0)))


class TestLine(unittest.TestCase):
    def assertPointEqual(self, a, b):
        self.assertAlmostEqual(a[0], b[0])
        self.assertAlmostEqual(a[1], b[1])

    def test_constructor(self):
        with self.assertRaises(ValueError):
            L((3, 5), (3.0, 5.0))

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
        self.assertTrue(L((0, 0), (2, 2)).intersects_y(1))
        self.assertTrue(L((2, 2), (0, 0)).intersects_y(1))
        self.assertFalse(L((-1, -1), (5, -1)).intersects_y(-1))
        self.assertFalse(L((2, 2), (0, 2)).intersects_y(1))
        self.assertFalse(L((0, 0), (-1, -1)).intersects_y(1))

    def test_get_intercept_h(self):
        self.assertEqual(L((1, 1), (3, 3)).get_y_intercept(2), 2)
        self.assertEqual(L((3, 4), (5, 1)).get_y_intercept(2), 13/3)

    def test_extrapolate_intersection(self):
        # Vertical/horizontal
        a = L((3, 3), (3, 4))
        b = L((9, 9), (7, 9))
        expect = (3, 9)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        # Both vertical
        b = L((7, 7), (7, 5))
        self.assertIsNone(a.extrapolate_intersection(b))
        self.assertIsNone(b.extrapolate_intersection(a))

        # Vertical/non-orthogonal
        b = L((1, 2), (5, 3))
        expect = (3, 2.5)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        b = L((4, 5), (5, 2))
        expect = (3, 8)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        b = -b
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        # Both horizontal
        a = L((1, 2), (4, 2))
        b = L((5, 6), (6, 6))
        self.assertIsNone(a.extrapolate_intersection(b))
        self.assertIsNone(b.extrapolate_intersection(a))

        # Horizontal/vertical
        b = L((9, 3), (9, -1))
        expect = (9, 2)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        # Horizontal/non-orthogonal
        b = L((9, 3), (10, 5))
        expect = (8.5, 2)
        self.assertPointEqual(a.extrapolate_intersection(b), expect)
        self.assertPointEqual(b.extrapolate_intersection(a), expect)

        # Both non-orthogonal
        a = L((0, 1), (4, 2))
        b = L((2, 4), (4, 3))
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
        line = L((3, 3), (3, 4))
        self.assertTrue(line.intersects_point(P(3, 3.5)))
        self.assertFalse(line.intersects_point(P(4, 3)))

        # Horizontal
        line = L((-2, -2), (2, -2))
        self.assertTrue(line.intersects_point(P(0, -2)))
        self.assertFalse(line.intersects_point(P(0, -1.999)))

        # Other
        line = L((0, 0), (2, 2))
        self.assertTrue(line.intersects_point(P(1, 1)))
        self.assertFalse(line.intersects_point(P(3, 3)))

    def test_intersects_line(self):
        # Vertical
        a = L((3, 3), (3, 5))
        self.assertFalse(a.intersects_line(L((4, 3), (4, 5))))
        self.assertFalse(a.intersects_line(L((0, 2), (4, 2))))
        self.assertTrue(a.intersects_line(L((3, 3), (4, 4))))
        self.assertTrue(a.intersects_line(L((0, 1), (5, 6))))
        self.assertTrue(a.intersects_line(L((3, 4), (3, 6))))

        # Horizontal
        a = L((3, 3), (-1, 3))
        self.assertFalse(a.intersects_line(L((-1, 2), (5, 2))))
        self.assertFalse(a.intersects_line(L((0, 2), (0, 0))))
        self.assertTrue(a.intersects_line(L((3, 3), (4, 4))))
        self.assertTrue(a.intersects_line(L((0, 0), (1, 5))))
        self.assertTrue(a.intersects_line(L((0, 3), (1, 3))))

        # Other
        a = L((0, 3), (4, 0))
        self.assertFalse(a.intersects_line(L((0, 0), (4, -3))))
        self.assertFalse(a.intersects_line(L((-1, 0), (0, 5))))
        self.assertTrue(a.intersects_line(L((0, 0), (5, 5))))
        self.assertTrue(a.intersects_line(L((4, 0), (-2, 1))))
        self.assertTrue(a.intersects_line(L((2, 1.5), (-2, 4.5))))

    def test_intersection_line(self):
        # Vertical
        a = L((3, 3), (3, 5))
        self.assertIsNone(a.intersection_line(L((4, 3), (4, 5))))
        self.assertIsNone(a.intersection_line(L((0, 2), (4, 2))))
        self.assertEqual(
                a.intersection_line(L((3, 3), (4, 4))),
                P(3, 3))
        self.assertEqual(
                a.intersection_line(L((0, 1), (5, 6))),
                P(3, 4))
        self.assertEqual(
                a.intersection_line(L((3, 4), (3, 6))),
                L((3, 4), (3, 5)))

        # Horizontal
        a = L((3, 3), (-1, 3))
        self.assertIsNone(a.intersection_line(L((-1, 2), (5, 2))))
        self.assertIsNone(a.intersection_line(L((0, 2), (0, 0))))
        self.assertEqual(
                a.intersection_line(L((3, 3), (4, 4))),
                P(3, 3))
        self.assertEqual(
                a.intersection_line(L((0, 0), (1, 5))),
                P(3/5, 3))
        self.assertEqual(
                a.intersection_line(L((0, 3), (1, 3))),
                L((1, 3), (0, 3)))

        # Other
        a = L((0, 3), (4, 0))
        self.assertIsNone(a.intersection_line(L((0, 0), (4, -3))))
        self.assertIsNone(a.intersection_line(L((-1, 0), (0, 5))))
        self.assertEqual(
                a.intersection_line(L((4, 0), (0, 3))),
                L((0, 3), (4, 0)))
        self.assertEqual(
                a.intersection_line(L((0, 0), (5, 5))),
                P(12/7, 12/7))
        self.assertEqual(
                a.intersection_line(L((4, 0), (-2, 1))),
                P(4, 0))
        self.assertEqual(
                a.intersection_line(L((2, 1.5), (-2, 4.5))),
                L((0, 3), (2, 1.5)))


class TestBoundingBox(unittest.TestCase):
    def test_contains(self):
        bbox = B(-2, -7/3, 3.1, 6)
        f = bbox.contains
        self.assertTrue(f(P(0, 0)))
        self.assertFalse(f(P(0, 6)))
        self.assertFalse(f(P(12, -8)))

        self.assertTrue(f(L((0, 0), (1, 1))))
        self.assertFalse(f(L((0, 0), (7, 7))))
        self.assertFalse(f(L((-3, 0), (-4, 1))))
        # Lines on the boundary are not contained
        self.assertFalse(f(L((3.1000000001, 0), (3.1000000001, -1))))

        self.assertTrue(f(B(0, 0, 1, 1)))
        self.assertFalse(f(B(0, 0, 1000, 1000)))
        self.assertFalse(f(B(-7, -7, -6, -6)))

        # A shape contains itself
        self.assertTrue(f(bbox))

        poly = Pg([(-1, -1), (0, 3), (3, 0), (-1, -1)])
        self.assertTrue(f(poly))
        poly = Pg([(6, 6), (7, 10), (10, 7), (6, 6)])
        self.assertFalse(f(poly))

    def test_intersects(self):
        bbox = B(0, 0, 10, 5)
        f = bbox.intersects

        # Points
        self.assertFalse(f(P(11, 0)))
        self.assertFalse(f(P(-1, 0)))
        self.assertFalse(f(P(1, -1)))
        self.assertFalse(f(P(1, 6)))

        self.assertTrue(f(P(3, 3)))
        self.assertTrue(f(P(0, 0)))
        self.assertTrue(f(P(0, 1)))
        self.assertTrue(f(P(0, 5)))
        self.assertTrue(f(P(5, 5)))
        self.assertTrue(f(P(10, 5)))
        self.assertTrue(f(P(10, 2)))
        self.assertTrue(f(P(10, 0)))
        self.assertTrue(f(P(9, 0)))

        # Lines:
        # - External
        self.assertFalse(f(L((11, 0), (11, 5))))
        # - Internal
        self.assertTrue(f(L((1, 1), (4, 3))))
        # - Overlapping
        self.assertTrue(f(L((-7, 4), (12, 4))))
        # - Boundary
        self.assertTrue(f(L((0, 0), (0, 5))))
        self.assertTrue(f(L((10, 4), (10, 6))))
        # - Corner
        self.assertTrue(f(L((9, -1), (11, 1))))

        # Polygons:
        poly = Pg([(0, 6), (0, 9), (4, 6), (0, 6)])

        # - External
        self.assertFalse(f(poly))
        # - Internal
        poly = poly.move(1, -5)
        self.assertTrue(f(poly))
        # - Overlapping
        poly = poly.move(8, 0)
        self.assertTrue(f(poly))
        # - Shared boundary line
        poly = poly.move(1, 0)
        self.assertTrue(f(poly))
        # - Shared boundary point
        poly = poly.move(-14, 0)
        self.assertTrue(f(poly))
        poly = poly.move(0, 4)
        self.assertTrue(f(poly))

    def test_intersection_point(self):
        bbox = B(0, 0, 10, 5)
        f = bbox.intersection

        self.assertIsNone(f(P(-1, 0)))
        p = P(0, 0)
        self.assertEqual(f(p), p)
        p = P(3, 3)
        self.assertEqual(f(p), p)
        p = P(10, 5)
        self.assertEqual(f(p), p)

    def test_intersection_line(self):
        bbox = B(0, 0, 10, 5)
        f = bbox.intersection

        # Fully external
        self.assertIsNone(f(L((11, 1), (12, 6))))

        # Fully internal
        line = L((1, 1), (9, 4))
        self.assertEqual(f(line), line)

        # Partly internal
        self.assertEqual(f(L((-1, 3), (1, 3))), L((0, 3), (1, 3)))
        self.assertEqual(f(L((5, 0), (11, 12))), L((5, 0), (7.5, 5)))

        # Shared boundary
        self.assertEqual(f(L((10, 5), (10, 0))), L((10, 5), (10, 0)))
        self.assertEqual(f(L((1, 5), (9, 5))), L((1, 5), (9, 5)))
        self.assertEqual(f(L((0, 2), (0, -2))), L((0, 2), (0, 0)))

        # Point contact
        self.assertEqual(f(L((15, 0), (5, 10))), P(10, 5))
        self.assertEqual(f(L((3, 5), (4, 8))), P(3, 5))

    def test_intersection_bbox(self):
        a = B(0, 0, 10, 5)
        f = a.intersection

        b = B(-5, -1, -1, 4)
        self.assertIsNone(f(b))

        b = B(2, 3, 8, 4)
        self.assertEqual(f(b), b)

        b = B(-10, -2, 15, 10)
        self.assertEqual(f(b), a)

        b = a
        self.assertEqual(f(b), a)

        b = B(8, -2, 12, 2)
        self.assertEqual(f(b), B(8, 0, 10, 2))

    def test_intersection_polygon(self):
        bbox = B(0, 0, 10, 5)
        f = bbox.intersection

        # No intersection
        poly = Pg([(12, 1), (13, 4), (17, 2), (12, 1)])
        self.assertIsNone(f(poly))

        # Fully internal
        poly = Pg([(1, 1), (3, 4), (7, 2), (1, 1)])
        self.assertEqual(f(poly), poly)

        # Fully containing
        poly = Pg([(-1, -1), (-2, 9), (13, 11), (14, -6), (-1, -1)])
        self.assertEqual(f(poly), bbox)

        # Partly internal
        poly = Pg([(8, 0), (12, 4), (12, 0), (8, 0)])
        self.assertEqual(f(poly), Pg([(8, 0), (10, 2), (10, 0), (8, 0)]))

        # Internal, shared boundary
        poly = Pg([(0, 0), (4, 5), (4, 0), (0, 0)])
        self.assertEqual(f(poly), poly)

        # External, shared boundary
        poly = Pg([(0, 0), (-4, 0), (0, 5), (0, 0)])
        self.assertEqual(f(poly), L((0, 0), (0, 5)))

        # Point contact
        poly = Pg([(3, 9), (7, 9), (5, 5), (3, 9)])
        self.assertEqual(f(poly), P(5, 5))


class TestPolygon(unittest.TestCase):
    def test_constructor(self):
        # not enough distinct points
        with self.assertRaises(ValueError):
            poly = Pg([(1, 2), (1, 2), (3, 5), (1, 2)])

        # backtracking
        with self.assertRaises(ValueError):
            poly = Pg([(1, 2), (3, 6), (2, 4)])

        # self-intersection
        with self.assertRaises(ValueError):
            poly = Pg([(1, 2), (3, 6), (5, 4), (-1, 4), (1, 2)])

        # simple triangle
        poly = Pg([(1, 2), (3, 5), (4, 1), (1, 2)])
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

    def test_contains_point(self):
        # simple triangle
        poly = Pg([(1, 2), (3, 5), (4, 1), (1, 2)])
        f = poly.contains_point
        expect = (
                (False, False, False, False, False),
                (False, False, False, False, False),
                (False, False,  True,  True, False),
                (False, False,  True,  True, False),
                (False, False, False,  True, False),
                (False, False, False, False, False),
                )
        for y in range(len(expect)):
            for x in range(len(expect[y])):
                self.assertIs(f(P(x, y)), expect[y][x], f"({x}, {y})")

        # octagon centred on (0, 0)
        poly = Pg([
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
                (1, 2),
                ])
        f = poly.contains_point
        self.assertTrue(f(P(1, 1)))
        self.assertTrue(f(P(1, -1)))
        self.assertTrue(f(P(-1, -1)))
        self.assertTrue(f(P(-1, 1)))
        self.assertFalse(f(P(2, 2)))

        # horseshoe
        poly = Pg([
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ])
        f = poly.contains_point
        expect = (
                (False, False, False, False, False, False, False),
                (False, False,  True,  True,  True, False, False),
                (False, False, False, False, False, False, False),
                (False, False, False, False,  True, False, False),
                (False, False, False, False, False, False, False),
                (False, False, False, False, False, False, False),
                (False, False, False, False, False, False, False),
                )
        for y in range(len(expect)):
            for x in range(len(expect[y])):
                self.assertIs(f(P(x, y)), expect[y][x], f"({x}, {y})")

    def test_contains_line(self):
        # simple triangle
        poly = Pg([(1, 2), (3, 5), (4, 1), (1, 2)])
        f = poly.contains_line

        # Fully external
        self.assertFalse(f(L((10, 0), (10, 2))))
        self.assertFalse(f(L((2, 0), (0, 3))))
        # Partly external
        self.assertFalse(f(L((3, 3), (5, 3))))
        # Fully internal
        self.assertTrue(f(L((3, 2), (2, 3))))
        # Spanning
        self.assertTrue(f(L((1, 2), (3.5, 3))))
        # On boundary
        self.assertFalse(f(L((3.5, 3), (3.75, 2))))
        self.assertFalse(f(L((3.5, 3), (4.5, -1))))

        # horseshoe
        poly = Pg([
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ])
        f = poly.contains_line

        # Fully external
        self.assertFalse(f(L((10, 0), (10, 2))))
        self.assertFalse(f(L((3, 0), (0, 0))))
        # Partly external
        self.assertFalse(f(L((4, 3), (6, 3))))
        # Fully internal
        self.assertTrue(f(L((3, 1), (2, 1))))
        # Spanning
        self.assertTrue(f(L((1, 4), (2, 4))))
        # From boundary to internal
        self.assertTrue(f(L((1, 2), (3, 1))))
        # On boundary
        self.assertFalse(f(L((1, 2), (1, 5))))
        self.assertFalse(f(L((4, 4), (6, 4))))

    def test_contains_bbox(self):
        # simple triangle
        poly = Pg([(1, 2), (3, 5), (4, 1), (1, 2)])
        f = poly.contains_bbox
        # Fully internal
        self.assertTrue(f(B(2, 2, 3, 3)))
        # Fully external
        self.assertFalse(f(B(20, 20, 30, 30)))
        # Partly external
        self.assertFalse(f(B(1, 1, 3, 3)))
        # Point contact with boundary
        self.assertTrue(f(B(2, 2, 3.5, 3)))

        # octagon centred on (0, 0)
        poly = Pg([
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
                (1, 2),
                ])
        f = poly.contains_bbox
        # Sharing entire boundary lines
        self.assertTrue(f(B(-2, -1, 2, 1)))
        self.assertFalse(f(B(-1, 2, 1, 4)))

        # horseshoe
        poly = Pg([
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ])
        f = poly.contains_bbox
        self.assertTrue(f(B(2, 1, 4, 1.5)))

    def test_contains_poly(self):
        # Simple triangle
        a = Pg([(1, 2), (3, 5), (4, 1), (1, 2)])
        f = a.contains_polygon
        # Fully internal
        b = Pg([(2, 2), (3, 4), (3, 2), (2, 2)])
        self.assertTrue(f(b))
        # Fully external
        b = b.move(10, 0)
        self.assertFalse(f(b))
        # Partly external
        b = b.move(-10, -2)
        self.assertFalse(f(b))
        # Point contact with boundary
        self.assertTrue(f(Pg([(3.5, 3), (2, 2), (3, 4), (3.5, 3)])))

        # Octagon centred on (0, 0)
        a = Pg([
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
                (1, 2),
                ])
        f = a.contains_polygon
        # Sharing entire boundary lines
        b = Pg([
            (-2, -1),
            (-2,  1),
            ( 0,  2),
            ( 2,  1),
            ( 2, -1),
            ( 0, -2),
            (-2, -1),
            ])
        self.assertTrue(f(b))

        b = b.move(4, 0)
        self.assertFalse(f(b))

        # Horseshoe
        a = Pg([
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ])
        f = a.contains_polygon
        b = Pg([
            (1, 1),
            (1, 3),
            (4, 3),
            (4, 1),
            (1, 1),
            ])
        self.assertFalse(f(b))

    def test_intersects_point(self):
        # horseshoe
        poly = Pg([
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ])
        f = poly.intersects
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
                self.assertIs(f(P(x, y)), expect[y][x], f"({x}, {y})")

    def test_intersects_line(self):
        # simple triangle
        poly = Pg([(1, 2), (3, 5), (4, 1), (1, 2)])
        f = poly.intersects

        # Fully external
        self.assertFalse(f(L((10, 0), (10, 2))))
        self.assertFalse(f(L((2, 0), (0, 3))))
        # Partly external
        self.assertTrue(f(L((3, 3), (5, 3))))
        # Fully internal
        self.assertTrue(f(L((3, 2), (2, 3))))
        # Spanning
        self.assertTrue(f(L((1, 2), (3.5, 3))))
        # On boundary
        self.assertTrue(f(L((3.5, 3), (3.75, 2))))
        self.assertTrue(f(L((3.5, 3), (4.5, -1))))

        # horseshoe
        poly = Pg([
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ])
        f = poly.intersects

        # Fully external
        self.assertFalse(f(L((10, 0), (10, 2))))
        self.assertFalse(f(L((3, 0), (0, 0))))
        # Partly external
        self.assertTrue(f(L((4, 3), (6, 3))))
        # Fully internal
        self.assertTrue(f(L((3, 1), (2, 1))))
        # Spanning
        self.assertTrue(f(L((1, 4), (2, 4))))
        # From boundary to internal
        self.assertTrue(f(L((1, 2), (3, 1))))
        # On boundary
        self.assertTrue(f(L((1, 2), (1, 5))))
        self.assertTrue(f(L((4, 4), (6, 4))))

    def test_intersects_bbox(self):
        # simple triangle
        poly = Pg([(1, 2), (3, 5), (4, 1), (1, 2)])
        f = poly.intersects
        # Fully internal
        self.assertTrue(f(B(2, 2, 3, 3)))
        # Fully external
        self.assertFalse(f(B(20, 20, 30, 30)))
        # Partly external
        self.assertTrue(f(B(1, 1, 3, 3)))
        # Point contact with boundary
        self.assertTrue(f(B(2, 2, 3.5, 3)))

        # octagon centred on (0, 0)
        poly = Pg([
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
                (1, 2),
                ])
        f = poly.intersects
        # Sharing entire boundary lines
        self.assertTrue(f(B(-2, -1, 2, 1)))
        self.assertTrue(f(B(-1, 2, 1, 4)))

        # horseshoe
        poly = Pg([
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ])
        f = poly.intersects
        self.assertTrue(f(B(2, 1, 4, 1.5)))

    def test_intersects_poly(self):
        # Simple triangle
        a = Pg([(1, 2), (3, 5), (4, 1), (1, 2)])
        f = a.intersects
        # Fully internal
        b = Pg([(2, 2), (3, 4), (3, 2), (2, 2)])
        self.assertTrue(f(b))
        # Fully external
        b = b.move(10, 0)
        self.assertFalse(f(b))
        # Partly external
        b = b.move(-10, -2)
        self.assertTrue(f(b))
        # Point contact with boundary
        self.assertTrue(f(Pg([(3.5, 3), (2, 2), (3, 4), (3.5, 3)])))

        # Octagon centred on (0, 0)
        a = Pg([
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
                (1, 2),
                ])
        f = a.intersects
        # Sharing entire boundary lines
        b = Pg([
            (-2, -1),
            (-2,  1),
            ( 0,  2),
            ( 2,  1),
            ( 2, -1),
            ( 0, -2),
            (-2, -1),
            ])
        self.assertTrue(f(b))

        b = b.move(4, 0)
        self.assertTrue(f(b))

        # Horseshoe
        a = Pg([
                (1, 1),
                (1, 6),
                (2, 5),
                (2, 2),
                (4, 2),
                (3, 4),
                (5, 4),
                (4, 0),
                (1, 1),
                ])
        f = a.intersects
        b = Pg([
            (1, 1),
            (1, 3),
            (4, 3),
            (4, 1),
            (1, 1),
            ])
        self.assertTrue(f(b))
