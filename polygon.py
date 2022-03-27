#!/usr/bin/env python3
# coding: utf-8
from line import Line, in_bound
from util import flatten_coords, float_eq, in_bbox
from point import Point


class Polygon():
    """A simple polygon.

    The polygon must be given as a sequence of points forming a clockwise
    exterior linear ring, with the interior of the polygon on the right-hand
    side.

    When a polygon is initialised, we flatten out any structure around the
    input points, remove any consecutive duplicate points, and close the
    polygon if it is not already closed.
    """
    def __init__(self, value):
        if isinstance(value, Polygon):
            self.points = value.points
            return

        # Normalise the coordinate structure to [(x0, y0), (x1, y1), ...]
        coords = flatten_coords(value)
        points = [Point(coords[i:i+2]) for i in range(0, len(coords), 2)]

        # Filter out consecutive identical points
        self.points = []
        for i, p in enumerate(points):
            if i == 0 or p != points[i-1]:
                self.points.append(p)

        # If the polygon isn't closed, close it now.
        if self.points[0] != self.points[-1]:
            self.points.append(self.points[0])

        if len(self.points) < 4:
            raise ValueError("Not enough valid points for a closed polygon.")

        # Disallow backtracking along the same line
        lines = self.lines
        length = len(lines)
        for i in range(length - 1):
            if (lines[i].angle == (-lines[i+1]).angle):
                raise ValueError(
                        f"Line {lines[i+1]} backtracks "
                        "along the previous line.")

        # Disallow intersection
        for i in range(length):
            for j in range(length):
                if i in {j, (j + 1) % length, (j - 1) % length}:
                    continue
                if lines[i].intersects(lines[j]):
                    raise ValueError(
                            f"Line {lines[i]} intersects with {lines[j]}.")

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.points[key]
        raise KeyError()

    def __contains__(self, point):
        """Return whether 'point' is equal to any of the polygon's vertices.

        Despite the name of the Python magic method, this doesn't test
        "containment" in the geometric sense, but rather it tests membership.
        To test whether a point is contained in the area of the polygon, use
        contains()
        """
        p = Point(point)
        for v in self.points:
            if v == p:
                return True
        return False

    @property
    def bbox(self):
        """Return the bounding box for this polygon.

        The return is a 4-tuple containing:

        (min_x, min_y, max_x, max_y)
        """
        min_x = None
        min_y = None
        max_x = None
        max_y = None
        for p in self.points:
            if min_x is None or p.x < min_x:
                min_x = p.x
            if min_y is None or p.y < min_y:
                min_y = p.y
            if max_x is None or p.x > max_x:
                max_x = p.x
            if max_y is None or p.y > max_y:
                max_y = p.y
        return (min_x, min_y, max_x, max_y)

    @property
    def lines(self):
        """Return an iterable of all the line segments in the polygon."""
        return [Line(self[i], self[i+1]) for i in range(len(self) - 1)]

    def contains_point(self, value, exact=True):
        """Return whether the given point lies inside this polygon.

        If 'exact' is True, then points lying exactly on the boundary of the
        polygon will be treated as inside.  Otherwise they will be treated as
        outside.
        """
        p = Point(value)

        # Shortcut case: if the point is outside the polygon's bounding box,
        # then it is definitely outside the polygon.
        if not in_bbox(self.bbox, p, exact):
            return False

        # Shortcut case: if the point is equal to one of the polygon's
        # vertices, then it is on the boundary.
        if p in self:
            return exact

        lines = self.lines
        # Edge case: check for the point lying exactly on a horizontal boundary
        # of the polygon.
        for line in lines:
            if (line.intersects_x(p.x) and
                    line.is_horizontal and
                    float_eq(line.a.y, p.y)):
                return exact

        # Search for the nearest line segment on either side of the point that
        # lie on the same horizontal.
        hlines = [l for l in lines if l.intersects_y(p.y)]
        xdiffs = [l.get_y_intercept(p.y) - p.x for l in hlines]

        left = None
        right = None
        negx = None
        posx = None
        for i, x in enumerate(xdiffs):
            if float_eq(x, 0):
                return exact
            if x < 0 and (negx is None or x > negx):
                left = i
                negx = x
            if x > 0 and (posx is None or x < posx):
                right = i
                posx = x

        if left is None or right is None:
            return False

        rline = hlines[right]
        lline = hlines[left]
        return rline.a.y > rline.b.y and lline.a.y < lline.b.y

    def contains(self, value, exact=True):
        """Return whether this polygon contains the geometry in 'value'.

        If the 'value' lies exactly on the boundary of the polygon, return the
        value of 'exact'.
        """
        if isinstance(value, Point):
            return self.contains_point(value)

        # TODO: line in poly, poly in poly
        raise ValueError(f"Unknown type for polygon contains {type(value)}.")


def get_polygon_lines(poly):
    """Return an iterable of all line segments in the polygon."""
    return [(poly[i], poly[i+1]) for i in range(len(poly) - 1)]


def is_convex(poly):
    """Return whether the given polygon is convex.

    The polygon must be given as a sequence of points forming a clockwise
    exterior linear ring, with the interior of the polygon on the right-hand
    side.

    The polygon is considered convex if no point lies on the left-hand side of
    the line formed by the preceding two points.
    """
    for i in range(0, len(poly) - 2):
        if in_bound(poly[i], poly[i+1], poly[i+2]) is False:
            return False
    return True


def divide_polygon(poly, i, j):
    """Divide a polygon along an internal line between two of its vertices.

    Given a polygon, and two indices, this function will attempt to divide the
    polygon into two parts, along the line between the points at those indices.

    The two points must separated by at least one other point (i.e. they may
    not be adjacent points on the polygon).

    This function does not attempt to check that the line between the two
    points lies internal to the polygon.  Results are not guaranteed to be
    sensible if the line is external!

    Returns a tuple of two distinct polygons that share an edge.
    """
    if i > j:
        i, j = j, i

    length = len(poly)
    diff = j - i
    if i < 0 or j >= length:
        raise ValueError(
                "Invalid indices for divide_polygon: "
                "index out of bounds.")
    if i == j or diff == length - 1:
        raise ValueError(
                "Invalid indices for divide_polygon: "
                "must specify two different points.")
    if diff < 2 or diff >= length - 2:
        raise ValueError(
                "Invalid indices for divide polygon: "
                "must not specify adjacent points.")

    a = poly[i:j+1] + [poly[i]]
    b = poly[:i+1] + poly[j:]
    return (a, b)


def shift_polygon(poly, n):
    """Shift the starting point of a polygon.

    Return a new polygon that has the same boundary as the input polygon, but a
    starting point shifted clockwise by 'n' positions.
    """
    length = len(poly) - 1
    n = n % length
    return poly[n:-1] + poly[:n+1]


def _find_next_convex_point(poly, i):
    """Return the next point on a polygon that yields a convex shape.

    Given a polygon and the index 'i' of one of its points, return the index of
    the next point that will yield a convex shape with the line segment
    beginning at 'i'.
    """
    shift = shift_polygon(poly, i)
    length = len(poly)
    for j in range(2, length):
        if not in_bound(shift[0], shift[1], shift[j]) is False:
            return (j + i) % (length - 1)
    return None


def point_in_polygon(poly, point, exact=True):
    return Polygon(poly).contains_point(point, exact)
