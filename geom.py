#!/usr/bin/env python3
# coding: utf-8
import math

from util import flatten_coords, float_eq, float_gt, float_lt, in_bbox


class Geometry():
    def disjoint(self, other):
        """Return whether two geometries are spatially disjoint.

        Two geometries are spatially disjoint if they have no contact
        whatsoever. If the geometries overlap, touch, or cross then they are
        not disjoint.
        """
        raise NotImplementedError()

    def intersection(self, other):
        """Return a geometry of the mutual interior from both inputs.

        If the geometries have no space in common (they are disjoint) then the
        result is None.

        Otherwise, the type of geometry returned depends on the inputs and the
        degree of overlap between them:
        - Point & anything => Point
        - Line  & Line     => Line or Point
        - Line  & Shape    => Line or Point
        - Shape & Shape    => Shape or Line or Point

        The intersection of a point with any geometry is the point itself, if
        there is any intersection, otherwise None.
        """
        raise NotImplementedError()

    def union(self, other):
        """Return a geometry of the combined interior of both inputs."""
        raise NotImplementedError()

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)


class Point(Geometry):
    def __init__(self, *args):
        if len(args) == 1:
            value = args[0]
            if isinstance(value, Point):
                self.x = value.x
                self.y = value.y
                return

            if isinstance(value, (list, tuple)):
                self.x, self.y = value
                return

            if isinstance(value, dict):
                self.x = value['x']
                self.y = value['y']

            raise ValueError(f"Unknown input type for Point: {type(value)}.")
        elif len(args) == 2:
            self.x, self.y = args
        else:
            raise ValueError(
                    f"Invalid number of arguments for Point: {len(args)}.")

    def __eq__(self, other):
        """Return whether this point is "nearly" equal to another.

        Two points are considered equal if the differences between their
        respective ordinates are both less than the EPSILON value.
        """
        if not isinstance(other, Point):
            other = Point(other)
        return float_eq(self.x, other.x) and float_eq(self.y, other.y)

    def __len__(self):
        return 2

    def __getitem__(self, key):
        if key == 'x' or key == 0:
            return self.x
        if key == 'y' or key == 1:
            return self.y
        raise KeyError()

    def intersection(self, other):
        if isinstance(other, Point):
            return self if self == other else None

        return self if other.intersects(self) else None

    def __and__(self, other):
        return self.intersection(other)

    def __str__(self):
        return f"({self.x},{self.y})"


class Line(Geometry):
    """A one-dimensional geometry that extends from one point to another.

    A Line is considered to be a finite geometry bounded by its points.  That
    is, it consists of both its endpoints, plus all of the points that lie
    along the straight line which connects them.  It also has a direction -- it
    begins at point A and ends at point B.
    """
    def __init__(self, a, b):
        self.a = Point(a)
        self.b = Point(b)

        if a == b:
            raise ValueError("Invalid line: the two points are equal.")

    @property
    def is_horizontal(self):
        return self.a.y == self.b.y

    @property
    def is_vertical(self):
        return self.a.x == self.b.x

    @property
    def dy(self):
        """Return the difference in y-value between the end points."""
        return self.b.y - self.a.y

    @property
    def dx(self):
        """Return the difference in x-value between the end points."""
        return self.b.x - self.a.x

    @property
    def gradient(self):
        """Return the gradient of the line.

        The gradient is defined as 'dy/dx', that is, the increase in 'y' value
        per unit increase in 'x' value.

        Horizontal lines have a gradient of zero.  Vertical lines have no such
        thing as a gradient, so return None for vertical lines.
        """
        if self.is_vertical:
            return None
        if self.is_horizontal:
            return 0
        return self.dy / self.dx

    @property
    def angle(self):
        """Return the direction of the line.

        The result is the size of angle between the line and the positive X
        axis, as a number of radians between π and -π.  A positive angle means
        the line heads "above" the X axis, in the positive Y direction.  A
        negative angle means the line heads "below" the X axis, in the negative
        Y direction.
        """
        return math.atan2(self.dy, self.dx)

    @property
    def bbox(self):
        """Return this line's bounding box."""
        return BoundingBox(
                min(self.a.x, self.b.x),
                min(self.a.y, self.b.y),
                max(self.a.x, self.b.x),
                max(self.a.y, self.b.y),
                )

    def get_x_intercept(self, x):
        """Return the y-value where the line intersects a vertical.

        Return the y-value of the point where this line meets the vertical
        given by the 'x' argument.

        Return None if this line is vertical.
        """
        if self.is_vertical:
            return None
        if self.is_horizontal:
            return self.a[1]
        return self.a[1] + (x - self.a[0]) * self.gradient

    def get_y_intercept(self, y):
        """Return the x-value where the line intersects a horizontal.

        Return the x-value of the point where this line meets the horizontal
        given by the 'y' argument.

        Return None if this line is horizontal.
        """
        if self.is_horizontal:
            return None
        if self.is_vertical:
            return self.a[0]
        return self.a[0] + (y - self.a[1]) * 1 / self.gradient

    def intersects_x(self, x):
        """Return whether a line intersects with a vertical.

        Return True if any point on the line, including its endpoints, lies at
        the given 'x' value.  Vertical lines are not considered to intersect
        any 'x' value.
        """
        if self.is_vertical:
            return False
        x1 = self.a.x
        x2 = self.b.x
        if x1 > x2:
            x1, x2 = x2, x1
        return not (float_gt(x1, x) or float_lt(x2, x))

    def intersects_y(self, y):
        """Return whether a line intersects with a horizontal.

        Return True if any point on the line, including its endpoints, lies at
        the given 'y' value.  Horizontal lines are not considered to intersect
        any 'y' value.
        """
        if self.is_horizontal:
            return False
        y1 = self.a.y
        y2 = self.b.y
        if y1 > y2:
            y1, y2 = y2, y1
        return not (float_gt(y1, y) or float_lt(y2, y))

    def extrapolate_intersection(self, other):
        """Return the point of intersection between two infinite lines.

        If the lines are not parallel, consider both lines to extend infinitely
        in both directions, and return the Point at which they intersect.

        If the lines are parallel, return None.
        """
        if self.is_vertical:
            if other.is_vertical:
                return None
            if other.is_horizontal:
                return Point(self.a[0], other.a[1])
            xdist = self.a[0] - other.a[0]
            return Point(self.a[0], other.a[1] + xdist * other.gradient)

        if other.is_vertical:
            if self.is_horizontal:
                return Point(other.a[0], self.a[1])
            xdist = other.a[0] - self.a[0]
            return Point(other.a[0], self.a[1] + xdist * self.gradient)

        if self.is_horizontal:
            if other.is_horizontal:
                return None
            ydist = self.a[1] - other.a[1]
            return Point(other.a[0] + ydist * 1 / other.gradient, self.a[1])

        if other.is_horizontal:
            ydist = other.a[1] - self.a[1]
            return Point(self.a[0] + ydist * 1 / self.gradient, other.a[1])

        if self.angle in {other.angle, (-other).angle}:
            return None
        if self.a == other.a or self.a == other.b:
            return self.a
        if self.b == other.a or self.b == other.b:
            return self.b

        convergence = self.gradient - other.gradient
        assert convergence != 0

        ydist = other.get_x_intercept(self.a[0]) - self.a[1]
        x = self.a[0] + ydist / convergence
        return Point(x, self.get_x_intercept(x))

    def intersects_point(self, point):
        """Return whether this line intersects with a Point.

        Return true if the point lies anywhere on the line between (and
        including) its endpoints, and false otherwise.
        """
        if point == self.a or point == self.b:
            return True

        bbox = self.bbox
        if bbox.disjoint(point):
            return False

        if self.is_vertical:
            return (
                    float_eq(point.x, self.a.x) and not (
                        float_lt(point.y, bbox.min_y) or
                        float_gt(point.y, bbox.max_y)))

        if self.is_horizontal:
            return (
                    float_eq(point.y, self.a.y) and not (
                        float_lt(point.x, bbox.min_x) or
                        float_gt(point.x, bbox.max_x)))

        y = self.get_x_intercept(point.x)
        return float_eq(y, point.y)

    def intersects_line(self, other):
        """Return whether two bounded lines intersect each other.

        This is true if the two lines are not parallel and, when considered as
        infinite lines, their point of intersection is not outside the bounding
        box of either line.
        """
        if self.bbox.disjoint(other.bbox):
            return False
        return self.intersection(other) is not None

    def intersects(self, other):
        """Return whether this line intersects some other geometry.
        """
        if isinstance(other, Point):
            return self.intersects_point(other)
        if isinstance(other, Line):
            return self.intersects_line(other)

        # TODO: bbox, polygon

    def intersection(self, other):
        """Return the intersection of this line with some geometry.

        Depending on the type of the geometry, and the extent of overlap, this
        will return None, a Point, or a Line.
        """
        bbox = self.bbox
        if bbox.disjoint(other.bbox):
            return None

        if isinstance(other, Point):
            return other if self.intersects_point(other) else None

        if isinstance(other, Line):
            p = self.extrapolate_intersection(other)
            if p is None or bbox.disjoint(p) or other.bbox.disjoint(p):
                return None
            return p

    def __neg__(self):
        """Return the negation of the line.

        The result is a line with the same points, but travelling in the
        opposite direction (a and b are reversed).
        """
        return Line(self.b, self.a)

    def __str__(self):
        return f"{self.a} → {self.b}"


class Shape(Geometry):
    """A Shape is any geometry that has an interior."""
    @property
    def bbox(self):
        raise NotImplementedError()

    def contains(self, other):
        """Return whether this shape contains some geometry.

        A shape contains another geometry if some part of that geometry lies in
        the interior of the shape, and no part of the geometry lies in the
        exterior of the shape.

        This means that a shape does not contain its own boundary, nor points
        nor lines lying entirely on the boundary.

        A shape does contain itself.
        """
        raise NotImplementedError()


class BoundingBox(Shape):
    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    @property
    def bbox(self):
        return self

    def get_polygon(self):
        """Return this bounding box as a Polygon."""
        return Polygon([
                (self.min_x, self.min_y),
                (self.min_x, self.max_y),
                (self.max_x, self.max_y),
                (self.max_x, self.min_y),
                (self.min_x, self.min_y),
                ])

    def disjoint(self, other):
        """Return whether the two geometries are spatially disjoint.

        This is False if the geometries have any kind of contact, be it by
        overlapping, crossing or touching.
        """
        if isinstance(other, Point):
            return (
                    float_lt(other.x, self.min_x) or
                    float_gt(other.x, self.max_x) or
                    float_lt(other.y, self.min_y) or
                    float_gt(other.y, self.max_y))

        if isinstance(other, BoundingBox):
            return (
                    float_lt(other.max_x, self.min_x) or
                    float_gt(other.min_x, self.max_x) or
                    float_lt(other.max_y, self.min_y) or
                    float_gt(other.min_y, self.max_y))

    def contains(self, other):
        if isinstance(other, Point):
            # Points on the boundary are not contained
            return (
                    float_gt(other.x, self.min_x) and
                    float_lt(other.x, self.max_x) and
                    float_gt(other.y, self.min_y) and
                    float_lt(other.y, self.max_y))

        if isinstance(other, Line):
            # The line is contained if neither of its points is outside the
            # box, and also it doesn't lie on the boundary.
            if self.disjoint(other.a) or self.disjoint(other.b):
                return False
            return not (
                    (other.is_horizontal and (
                        float_eq(other.a.y, self.min_y) or
                        float_eq(other.a.y, self.max_y))) or
                    (other.is_vertical and (
                        float_eq(other.a.x, self.min_x) or
                        float_eq(other.a.x, self.max_x))))

        if isinstance(other, BoundingBox):
            return not (
                    float_lt(other.min_x, self.min_x) or
                    float_gt(other.max_x, self.max_x) or
                    float_lt(other.min_y, self.min_y) or
                    float_gt(other.max_y, self.max_y))

        if isinstance(other, Polygon):
            for p in other.points:
                if self.disjoint(p):
                    return False
            return True


class Polygon(Shape):
    """A shape enclosed by straight line segments.

    The polygon must be given as a sequence of points forming a clockwise
    exterior linear ring, with the interior of the polygon on the right-hand
    side from a perspective travelling along the line.

    When a polygon is initialised, we flatten out any structure around the
    input points, remove any consecutive duplicate points, and close the
    polygon if it is not already closed (i.e. ensure that the last point in the
    polygon is the same as the first point).
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

        # Disallow self-intersection
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

    def contains(self, other):
        """Return whether this polygon contains some other geometry.

        See comments at Shape.contains for the particulars.
        """
        if isinstance(other, Point):
            return self.contains_point(other, False)

        # TODO: line in poly, poly in poly
        raise ValueError(f"Unknown type for polygon contains {type(other)}.")


def point_eq(a, b):
    """Return whether two points (coordinate pairs) are "nearly" equal.

    Two points are considered equal if the differences between their respective
    ordinates are both less than the EPSILON value.
    """
    if not isinstance(a, Point):
        a = Point(a)
    if not isinstance(b, Point):
        b = Point(b)
    return a == b


def in_bound(a, b, p):
    """Return whether a given point lies within a boundary line.

    Given a line that runs from point 'a' to point 'b', and extends infinitely
    in both directions, return True if the point 'p' lies on the right-hand
    side of that line, and False if it lies of the left-hand side.  If the
    point lies exactly on the line, return None.
    """
    line = Line(a, b)
    a = line.a
    b = line.b
    p = Point(p)

    # Shortcut case: P is equal to A or B
    if a == p or b == p:
        return None

    # Shortcut case: horizontal or vertical lines
    if line.is_horizontal:
        if float_eq(p.y, a.y):
            return None
        return p.y < a.y if a.x < b.x else p.y > a.y

    if line.is_vertical:
        if float_eq(p.x, a.x):
            return None
        return p.x > a.x if a.y < b.y else p.x < a.x

    # Find the point on the line that has the same x-value as P, and then see
    # whether P lies above or below that point.
    y = line.get_x_intercept(p.x)

    if float_eq(p.y, y):
        return None
    return p.y < y if a.x < b.x else p.y > y


def get_intercept_h(a, b, y):
    """Return the x-value where a line intersects a horizontal.

    Given a line that intersects points 'a' and 'b', and a horizontal with
    y-value 'y', return the x-value of the point where the horizontal meets the
    line.

    Return None if the line between 'a' and 'b' is itself horizontal.
    """
    return Line(a, b).get_y_intercept(y)


def get_intercept_v(a, b, x):
    """Return the y-value where a line intersects a vertical.

    Given a line that intersects points 'a' and 'b', and a vertical with
    x-value 'x', return the y-value of the point where the vertical meets the
    line.

    Return None if the line between 'a' and 'b' is itself vertical.
    """
    return Line(a, b).get_x_intercept(x)


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
