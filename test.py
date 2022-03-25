import unittest


import geom


class TestGeom(unittest.TestCase):
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

    def test_intersects_h(self):
        self.assertTrue(geom.intersects_h((0, 0), (2, 2), 1))
        self.assertTrue(geom.intersects_h((2, 2), (0, 0), 1))
        self.assertFalse(geom.intersects_h((-1, -1), (5, -1), -1))
        self.assertFalse(geom.intersects_h((2, 2), (0, 2), 1))
        self.assertFalse(geom.intersects_h((0, 0), (-1, -1), 1))

    def test_get_intercept_h(self):
        self.assertEqual(geom.get_intercept_h((1, 1), (3, 3), 2), 2)
        self.assertEqual(geom.get_intercept_h((3, 4), (5, 1), 2), 13/3)

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

    def test_in_polygon(self):
        with self.assertRaises(ValueError):
            geom.in_polygon([(1, 2)], (3, 4))

        # simple triangle
        poly = [(1, 2), (3, 5), (4, 1), (1, 2)]
        self.assertTrue(geom.in_polygon(poly, (3, 2)))
        self.assertFalse(geom.in_polygon(poly, (2, 4)))

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
        self.assertTrue(geom.in_polygon(poly, (1, 1)))
        self.assertTrue(geom.in_polygon(poly, (1, -1)))
        self.assertTrue(geom.in_polygon(poly, (-1, -1)))
        self.assertTrue(geom.in_polygon(poly, (-1, 1)))
        self.assertFalse(geom.in_polygon(poly, (2, 2)))

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
                        geom.in_polygon(poly, (x, y)),
                        expect[y][x],
                        f"({x}, {y})")
