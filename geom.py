#!/usr/bin/env python3
# coding: utf-8
import math
from functools import reduce

from util import UniqueList, float_close, float_gt, float_lt


π = math.pi
TWOπ = 2 * π


class Plot():
    def __init__(self):
        import matplotlib.pyplot as plt

        self.plot = plt
        self.fig, self.ax = plt.subplots()
        self.ax.axis('equal')
        self.ax.grid(True)


class Geometry():
    """A Geometry represents some division of a coordinate space.

    Geometries in general divide the coordinate space into three categories:

    - interior
    - boundary
    - exterior

    Points are special in that they don't have any boundary, but otherwise all
    geometries have an interior, a boundary and an exterior.

    Spatial relationships between geometries are based on how their interiors,
    boundaries and exteriors intersect with each other.
    """
    __slots__ = []

    @property
    def base(self):
        """Return the most basic possible representation of this geometry.

        For single geometries, the basic representation is itself.
        """
        return self

    @property
    def dimension(self) -> int:
        """Return the dimension of the geometry as an integer.

        0 - Point
        1 - Line
        2 - Shape
        """
        return self.DIMENSION

    def disjoint(self, other):
        """Return whether two geometries are spatially disjoint.

        Two geometries are spatially disjoint if they have no contact
        whatsoever. If the geometries overlap, touch, or cross then they are
        not disjoint.
        """
        raise NotImplementedError()

    def intersection_collection(self, other):
        """Return an intersection between this geometry and a collection."""
        if self.disjoint(other):
            return None

        result = self
        for item in other:
            result = self.intersection(item)
            if result is None:
                return None
        return result

    def intersection(self, other):
        """Return a geometry of the mutual interior from both inputs.

        If the geometries have no space in common (they are disjoint) then the
        result is None.

        Otherwise, the type of geometry returned depends on the inputs and the
        degree of overlap between them:
        - Point & anything => Point
        - Line  & Line     => Line or Point
        - Line  & Shape    => Line, Point or a Collection of Lines and Points
        - Shape & Shape    => Line, Point, Shape or any Collection

        The intersection of a point with any geometry is the point itself, if
        there is any intersection, otherwise None.
        """

    def union(self, other):
        """Return a geometry of the combined interior of both inputs."""
        return union(self, other)

    def intersects(self, other):
        return self.intersection(other) is not None

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def add_to_plot(self, plot):
        raise NotImplementedError()

    def plot(self):
        """Add this geometry to a new Plot object and return the Plot."""
        plot = Plot()
        self.add_to_plot(plot)
        return plot


class Collection(Geometry):
    __slots__ = ['items']

    def __init__(self, items=None):
        self.items = set()
        if items:
            self.items = set(tuple(items))

    @property
    def base(self):
        """Return the most basic possible representation of this geometry.

        For collections with a single member, the basic representation is that
        member as a single geometry.  Otherwise, it is the entire collection.
        """
        if len(self) == 1:
            return tuple(self.items)[0]
        return self

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        if not isinstance(other, Collection):
            return False
        if len(self) != len(other):
            return False
        return self.items == other.items

    def __iter__(self):
        return iter(self.items)

    def __contains__(self, item):
        return item in self.items

    def __str__(self):
        return ', '.join(map(str, tuple(self.items)))

    def __repr__(self):
        return f'{self.__class__.__name__}({self})'

    def add_to_plot(self, plot):
        for item in self:
            item.add_to_plot(plot)

    @staticmethod
    def make(items):
        """Produce a Collection instance according to the types of the inputs.

        This function will return a homogeneous collection if possible.  That
        is, if all the inputs are Points, it will return a MultiPoint.  If all
        the inputs are Lines, it will return a MultiLine, and so on.

        If there are no inputs, or the inputs contain a mixture of types,
        return a generic Collection.

        This function will not produce nested Collections.  If an input to
        make() is itself a Collection, we take the items of that Collection as
        the inputs instead.
        """
        cls = Collection
        if not items:
            return cls()

        unnested = []
        for item in items:
            if isinstance(item, Collection):
                unnested.extend(item.items)
            else:
                unnested.append(item)

        if all([isinstance(x, Polygon) for x in unnested]):
            cls = MultiPolygon
        elif all([isinstance(x, Line) for x in unnested]):
            cls = MultiLine
        elif all([isinstance(x, Point) for x in unnested]):
            cls = MultiPoint

        return cls(items)

    @property
    def bbox(self):
        """Return the overall bounding box for this collection."""
        min_x = None
        min_y = None
        max_x = None
        max_y = None
        for item in self.items:
            if isinstance(item, Point):
                bbox = item.x, item.y, item.x, item.y
            else:
                bbox = item.bbox.as_tuple()

            if min_x is None or bbox[0] < min_x:
                min_x = bbox[0]
            if min_y is None or bbox[1] < min_y:
                min_y = bbox[1]
            if max_x is None or bbox[2] > max_x:
                max_x = bbox[2]
            if max_y is None or bbox[3] > max_y:
                max_y = bbox[3]

        return BoundingBox(min_x, min_y, max_x, max_y)

    def intersects(self, other):
        # Shortcut: if this collection's bounding box doesn't intersect with the
        # other geometry, then there's no way any of its contents do.
        if not self.bbox.intersects(other):
            return False

        return any([x.intersects(other) for x in self.items])

    def disjoint(self, other):
        return not self.intersects(other)


class Point(Geometry):
    """A Point represents a single location in space.

    For the purposes of this library, a Point has no boundary, and is its own
    interior.  The exterior of the Point is all space that is not equal to the
    Point.
    """
    __slots__ = ['x', 'y']
    DIMENSION = 0

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
        """Return whether this point is exactly equal to another.

        Note that this is not the same thing as spatially equal.  This
        function, and the == operator, test for strict simple equality
        according to normal Python semantics.  The 'equals' method, on the
        other hand, behaves as per the DE-9IM spatial predicate function.
        """
        if other is None:
            return False
        if isinstance(other, (Line, Shape)):
            return False
        if not isinstance(other, Point):
            other = Point(other)
        return self.as_tuple() == other.as_tuple()

    def close(self, other):
        """Return whether this point is 'close' to another.

        In this case, 'close' is shorthand for 'close enough to be considered
        equal, given the quirks of binary floating point math'.
        """
        if other is None or not isinstance(other, Geometry):
            return False
        other = other.base
        if isinstance(other, (Line, Shape)):
            return False
        if not isinstance(other, Point):
            other = Point(other)
        return float_close(self.x, other.x) and float_close(self.y, other.y)

    def __len__(self):
        return 2

    def __getitem__(self, key):
        if not isinstance(key, (str, int)):
            raise TypeError()
        if key == 'x' or key == 0:
            return self.x
        if key == 'y' or key == 1:
            return self.y
        raise KeyError()

    def as_tuple(self):
        return (self.x, self.y)

    def intersection(self, other):
        other = other.base
        if isinstance(other, Point):
            return self if self == other else None

        return self if other.intersects(self) else None

    def equals(self, other) -> bool:
        """Return whether the point is spatially equal to some geometry.

        This is not the same thing as the simple equality you get with the
        __eq__ method and == operator.

        Two geometries are spatially equal if their interiors intersect, and no
        part of the interior or boundary of one geometry intersects the
        exterior of the other.

        In the case of a point, it can only be spatially equal to another
        point, as anything else would necessarily intersect with the exterior
        of the point.
        """
        if isinstance(other, Geometry):
            other = other.base
        else:
            other = Point(other)
        return isinstance(other, Point) and self.close(other)

    def intersects(self, other):
        """Return whether the point intersects some geometry.

        This is True if and only if the point lies within the interior
        or boundary of the other geometry.
        """
        other = other.base
        if isinstance(other, Point):
            return self.equals(other)

        return other.intersects(self)

    def disjoint(self, other):
        """Return whether the point is spatially disjoint with some geometry.

        This is True if and only if the point does not lie within any interior
        or boundary of the other geometry.
        """
        other = other.base
        if isinstance(other, Point):
            return not self.equals(other)

        return not other.intersects(self)

    def touches(self, other):
        """Return whether the point touches some geometry.

        This is true if the point lies in the boundary of the other geometry,
        but false otherwise.

        By this definition, it is impossible for a point to 'touch' another
        point, because points have no boundary.
        """
        other = other.base
        if isinstance(other, Point):
            return False

        if isinstance(other, Line):
            return self.equals(other.a) or self.equals(other.b)

        if isinstance(other, Polygon):
            return any([self.intersects(x) for x in other.lines])

        return other.touches(self)

    def crosses(self, other):
        """Return whether the point crosses some geometry.

        This is always false for a single point, regardless of what the other
        geometry is.
        """
        return False

    def contains(self, other):
        """Return whether this point contains some geometry.

        This is true if the other geometry has no points exterior to this
        point, which can only be true if the other geometry is also a point,
        and is equal to this one.
        """
        other = other.base
        return (isinstance(other, Point) and self.equals(other))

    def covers(self, other):
        """Return whether this point covers some geometry.

        This is true if the other geometry lies entirely within this point,
        which can only be true if the other geometry is also a point, and is
        equal to this one.
        """
        other = other.base
        return (isinstance(other, Point) and self.equals(other))

    def within(self, other):
        """Return whether this point is within some geometry.

        This is true if the point lies in the interior of the other geometry,
        not the boundary.  So for point/point, it is only true when the points
        are equal.  For point/line, it is only true if the point lies along the
        line but isn't equal to either endpoint.
        """
        other = other.base
        if isinstance(other, Point):
            return self.equals(other)

        if isinstance(other, Line):
            return (
                    self.intersects(other)
                    and not self.equals(other.a)
                    and not self.equals(other.b))

        if isinstance(other, Polygon):
            if self.disjoint(other):
                return False
            for line in other.lines:
                if self.intersects(line):
                    return False
            return True

        return other.contains(self)

    def overlaps(self, other):
        """Return whether this point overlaps some geometry.

        This is always false for single points, regardless of what the other
        geometry is.
        """
        return False

    def distance(self, other):
        """Return the Euclidean distance between two points."""
        other = other.base
        if self == other:
            return 0
        try:
            return math.dist(self.as_tuple(), other.as_tuple())
        except AttributeError:
            # math.dist was added in Python 3.8, we might be running on an
            # earlier version.
            dx = other.x - self.x
            dy = other.y - self.y
            return math.sqrt((dy ** 2.0) + (dx ** 2.0))

    def move(self, x=0, y=0):
        """Return a new Point with position relative to this one."""
        return Point(self.x + x, self.y + y)

    def __and__(self, other):
        return self.intersection(other)

    def __str__(self):
        return f"({self.x},{self.y})"

    def __repr__(self):
        return f"Point({self.x},{self.y})"

    def __hash__(self):
        return hash(('Point', self.x, self.y))

    def add_to_plot(self, plot):
        plot.ax.plot((self.x,), (self.y,))


class Line(Geometry):
    """A one-dimensional geometry that extends from one point to another.

    A Line is considered to be a finite geometry bounded by its points.  That
    is, its interior is the one-dimensional space that lies between the two
    endpoints (but not including them), and the boundary is the endpoints
    themselves.

    A Line has a direction -- it begins at point A and ends at point B.
    """
    __slots__ = ['a', 'b']
    DIMENSION = 1

    def __init__(self, a, b):
        self.a = Point(a)
        self.b = Point(b)

        if self.a.equals(b):
            raise ValueError("Invalid line: the two points are too close.")

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

    def relative_angle(self, other):
        """Return the relative angle between this line and another line.

        The relative angle is given as a number of radians between π and -π,
        and is the amount of counter-clockwise rotation you would apply to this
        line, anchored at its start point, in order for it to parallel the
        other line.
        """
        if self.a.equals(other.a) and self.b.equals(other.b):
            return 0
        if self.a.equals(other.b) and self.b.equals(other.a):
            return π
        return normalise_angle(other.angle - self.angle)

    @property
    def points(self):
        """Return an iterable of this line's points."""
        return (self.a, self.b)

    @property
    def bbox(self):
        """Return this line's bounding box."""
        return BoundingBox(
                min(self.a.x, self.b.x),
                min(self.a.y, self.b.y),
                max(self.a.x, self.b.x),
                max(self.a.y, self.b.y),
                )

    @property
    def length(self):
        """Return the Euclidean distance between this line's endpoints."""
        return math.dist(self.a.as_tuple(), self.b.as_tuple())

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

    def parallel(self, other):
        """Return whether this line is parallel with another line."""
        return self.angle in {other.angle, (-other).angle}

    def in_bound(self, point):
        """Return whether the given point lies within this line's boundary.

        Considering this line as a Euclidean line that extends infinitely in
        both directions, return True if 'point' lies on the right-hand side of
        that line, False if it lies of the left-hand side, or None if it lies
        exactly on the line.

        In this context, "right-hand" means from the point of view of an
        observer at point A, looking towards point B.
        """
        a = self.a
        b = self.b
        p = Point(point)
        # Shortcut case: point is equal to one of the line endpoints
        if a == p or b == p:
            return None

        angle_ab = self.angle
        angle_ap = Line(a, p).angle
        if float_close(angle_ab, angle_ap):
            return None
        relative_angle = normalise_angle(angle_ap - angle_ab)
        return relative_angle < 0

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

        if self.parallel(other):
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
                    float_close(point.x, self.a.x) and not (
                        float_lt(point.y, bbox.min_y) or
                        float_gt(point.y, bbox.max_y)))

        if self.is_horizontal:
            return (
                    float_close(point.y, self.a.y) and not (
                        float_lt(point.x, bbox.min_x) or
                        float_gt(point.x, bbox.max_x)))

        y = self.get_x_intercept(point.x)
        return float_close(y, point.y)

    def intersects_line(self, other):
        """Return whether two bounded lines intersect each other.

        This is true if the two lines share any points along their length,
        including their endpoints.
        """
        bbox = self.bbox
        if bbox.disjoint(other.bbox):
            return False
        if (
                self.a in {other.a, other.b} or
                self.b in {other.a, other.b} or
                self.intersects_point(other.a) or
                self.intersects_point(other.b)):
            return True

        p = self.extrapolate_intersection(other)
        return not (p is None or bbox.disjoint(p) or other.bbox.disjoint(p))

    def intersects(self, other):
        """Return whether this line intersects some other geometry.
        """
        if isinstance(other, Point):
            return self.intersects_point(other)
        if isinstance(other, Line):
            return self.intersects_line(other)

        return other.intersects(self)

    def disjoint(self, other):
        return not self.intersects(other)

    def intersection_line(self, other):
        """Return the shared geometry between two bounded lines.

        This will be None if the two lines are disjoint, a Point if the lines
        cross each other, or a Line if the lines are parallel and have some
        mutual space.
        """
        if self.bbox.disjoint(other.bbox):
            return None
        if self == other:
            return self
        if self.parallel(other):
            if self.is_vertical:
                x = self.a.x
                if not float_close(x, other.a.x):
                    return None
                # Lines share the same vertical; overlap?
                y1 = max(min(self.a.y, self.b.y), min(other.a.y, other.b.y))
                y2 = min(max(self.a.y, self.b.y), max(other.a.y, other.b.y))
                if float_close(y1, y2):
                    return Point(x, y1)
                if float_lt(y1, y2):
                    a = x, y1
                    b = x, y2
                    if self.a.y > self.b.y:
                        a, b = b, a
                    return Line(a, b)
                return None

            if not float_close(
                    self.get_x_intercept(0), other.get_x_intercept(0)):
                return None

            # Lines share the same Euclidean, do they overlap?
            x1 = max(min(self.a.x, self.b.x), min(other.a.x, other.b.x))
            x2 = min(max(self.a.x, self.b.x), max(other.a.x, other.b.x))
            if float_close(x1, x2):
                return Point(x1, self.get_x_intercept(x1))
            if float_lt(x1, x2):
                a = x1, self.get_x_intercept(x1)
                b = x2, self.get_x_intercept(x2)
                if self.a.x > self.b.x:
                    a, b = b, a
                return Line(a, b)
            return None

        if self.a in {other.a, other.b}:
            return self.a
        if self.b in {other.a, other.b}:
            return self.b

        if self.intersects_point(other.a):
            return other.a
        if self.intersects_point(other.b):
            return other.b
        if other.intersects_point(self.a):
            return self.a
        if other.intersects_point(self.b):
            return self.b

        p = self.extrapolate_intersection(other)
        if p is None or self.bbox.disjoint(p) or other.bbox.disjoint(p):
            return None
        return p

    def intersection(self, other):
        """Return the intersection of this line with some geometry.

        Depending on the type of the geometry, and the extent of overlap, this
        will return None, a Point, a Line or a Collection of Points and Lines.
        """
        bbox = self.bbox
        if bbox.disjoint(other.bbox):
            return None

        if isinstance(other, Point):
            return other if self.intersects_point(other) else None

        if isinstance(other, Line):
            return self.intersection_line(other)

        if isinstance(other, Geometry):
            return other.intersection(self)

    def crop_line(self, other):
        """Crop this line along an infinite line.

        Consider the 'other' line as an infinite Euclidean extending in both
        directions, and return a geometry that represents the part of this line
        that does not fall on the left-hand side of the 'other' line.  The
        result can be None, a Point, or a Line.
        """
        bound_a = other.in_bound(self.a)
        bound_b = other.in_bound(self.b)

        if bound_a is False and bound_b is False:
            return None

        if not (bound_a is False or bound_b is False):
            return self

        if bound_a is None:
            return self.a
        if bound_b is None:
            return self.b

        sect = self.extrapolate_intersection(other)
        if bound_a is True:
            return Line(self.a, sect)
        else:
            return Line(sect, self.b)

    def move(self, x=0, y=0):
        """Return a new Line spatially shifted relative to this Line."""
        return Line(self.a.move(x, y), self.b.move(x, y))

    def get_adjacent_line(self, angle, length):
        """Return a new line adjacent to this line.
        
        The new line will begin at the endpoint B of the current line, and its
        direction will be as the current line, rotated counter-clockwise by `angle`
        radians.
        """
        xangle = normalise_angle(self.angle + angle)
        x = length * math.cos(xangle)
        y = math.sqrt(length**2 - x**2)
        if xangle < 0:
            y = -y
        c = (self.b.x + x, self.b.y + y)
        return Line(self.b, c)

    def __eq__(self, other):
        """Return whether two lines are exactly equal.

        Two lines are considered equal if their endpoints and direction are
        equal.
        """
        if not isinstance(other, Line):
            return False
        return (self.a, self.b) == (other.a, other.b)

    def equals(self, other):
        """Return whether this line is spatially equal to some other geometry.
        """
        other = other.base
        if isinstance(other, Point):
            return False
        if not isinstance(other, Line):
            raise NotImplementedError()
        return ((self.a.equals(other.a) and self.b.equals(other.b))
                or (self.a.equals(other.b) and self.b.equals(other.a)))

    def coterminous(self, other):
        """Return whether the two lines have exactly the same endpoints.

        Two lines are coterminous if they share the same set of endpoints.  The
        lines need not have the same direction.
        """
        return {self.a, self.b} == {other.a, other.b}

    def __neg__(self):
        """Return the negation of the line.

        The result is a line with the same points, but travelling in the
        opposite direction (a and b are reversed).
        """
        return Line(self.b, self.a)

    def __str__(self):
        return f"{self.a} → {self.b}"

    def __repr__(self):
        return f"Line({self})"

    def __hash__(self):
        return hash(('Line', self.a, self.b))

    def add_to_plot(self, plot):
        plot.ax.plot((self.a.x, self.b.x), (self.a.y, self.b.y))


class Shape(Geometry):
    """A Shape is any two-dimensional geometry that has an interior area.
    """
    __slots__ = []
    DIMENSION = 2

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

    def covers(self, other):
        """Return whether this shape covers some geometry.

        A shape covers another geometry if no part of that geometry lies in
        the exterior of the shape.  That is, the entire geometry is within the
        interior and/or the boundary of the shape.
        """
        raise NotImplementedError()


class BoundingBox(Shape):
    __slots__ = ['min_x', 'min_y', 'max_x', 'max_y']

    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    @property
    def bbox(self):
        return self

    @property
    def points(self):
        """Return the corners of this box's boundary as an iterable of Points.

        The Points are returned starting with the lower-left corner and
        proceeding clockwise.
        """
        return [
                Point(self.min_x, self.min_y),
                Point(self.min_x, self.max_y),
                Point(self.max_x, self.max_y),
                Point(self.max_x, self.min_y),
                ]

    @property
    def boundary(self):
        """Return this box's boundary, as an iterable of Lines.

        The Lines are returned starting from the lower-left corner and
        proceeding clockwise.

        Note that a BoundingBox boundary does not necessarily consitute a valid
        Polygon.  A Polygon must enclose some amount of interior space, whereas
        a BoundingBox need not.
        """
        a, b, c, d = self.points
        return [
                Line(a, b),
                Line(b, c),
                Line(c, d),
                Line(d, a),
                ]

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

        return not self.intersects(other)

    def intersects(self, other):
        """Return whether this box intersects some other geometry."""
        if isinstance(other, (Point, BoundingBox)):
            return not self.disjoint(other)

        if isinstance(other, (Shape, Collection)):
            if self.disjoint(other.bbox):
                return False

        if self.contains(other):
            return True

        if isinstance(other, Line):
            for line in self.boundary:
                if line.intersects(other):
                    return True
            return False

        if isinstance(other, Polygon):
            if self.covers(other) or other.covers(self):
                return True
            for box_line in self.boundary:
                for poly_line in other.lines:
                    if box_line.intersects(poly_line):
                        return True
            return False

        if isinstance(other, Collection):
            return any([self.intersects(x) for x in other])

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
                        float_close(other.a.y, self.min_y) or
                        float_close(other.a.y, self.max_y))) or
                    (other.is_vertical and (
                        float_close(other.a.x, self.min_x) or
                        float_close(other.a.x, self.max_x))))

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

        if isinstance(other, Collection):
            return (
                    self.covers(other) and
                    any([self.contains(x) for x in other]))

    def covers(self, other):
        if isinstance(other, Point):
            return not self.disjoint(other)

        if isinstance(other, Line):
            # The line is covered if neither of its points is outside the box.
            return not (self.disjoint(other.a) or self.disjoint(other.b))

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

        if isinstance(other, Collection):
            return all([self.covers(x) for x in other])

    def intersection_line(self, other):
        """Return the intersection of this box with a Line.

        The result will be either None, a Point or a Line.
        """
        if self.disjoint(other):
            return None

        if self.covers(other):
            return other

        if other.is_vertical:
            x = other.a.x
            if other.a.y < other.b.y:
                a = (x, max(other.a.y, self.min_y))
                b = (x, min(other.b.y, self.max_y))
            else:
                b = (x, max(other.b.y, self.min_y))
                a = (x, min(other.a.y, self.max_y))
            return Line(a, b)

        a, b = other.a, other.b
        for boundary in self.boundary:
            sect = boundary.intersection(Line(a, b))
            if isinstance(sect, Line):
                return sect
            if isinstance(sect, Point):
                if boundary.in_bound(a) is False:
                    a = sect
                if boundary.in_bound(b) is False:
                    b = sect
                if a.equals(b):
                    return a
        return Line(a, b)

    def intersection_bbox(self, other):
        """Return the intersection of this box with another box.

        The result can be None, a Point, a Line or a BoundingBox.
        """
        if self.equals(other):
            return self

        if self.disjoint(other):
            return None

        return BoundingBox(
                max(self.min_x, other.min_x),
                max(self.min_y, other.min_y),
                min(self.max_x, other.max_x),
                min(self.max_y, other.max_y))

    def intersection(self, other):
        if isinstance(other, Point):
            return other if self.intersects(other) else None

        if isinstance(other, Line):
            return self.intersection_line(other)

        if isinstance(other, BoundingBox):
            return self.intersection_bbox(other)

        if isinstance(other, Collection):
            return self.intersection_collection(other)

        return other.intersection(self)

    def as_tuple(self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)

    def __eq__(self, other):
        if not isinstance(other, BoundingBox):
            return False
        return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        return hash(tuple('BoundingBox') + self.as_tuple())

    def equals(self, other) -> bool:
        """Return whether this box is spatially equal to some other geometry.
        """
        if not isinstance(other, BoundingBox):
            raise NotImplementedError()
        z = zip(self.as_tuple(), other.as_tuple())
        return all([float_close(a, b) for a, b in z])

    def __str__(self):
        return f"{self.min_x},{self.min_y},{self.max_x},{self.max_y}"

    def __repr__(self):
        return f"BoundingBox({self})"

    def add_to_plot(self, plot):
        x = (self.min_x, self.max_x, self.max_x, self.min_x, self.min_x)
        y = (self.min_y, self.min_y, self.max_y, self.max_y, self.min_y)
        plot.ax.plot(x, y)


class Polygon(Shape):
    """A shape enclosed by straight line segments.

    The polygon must be given as a sequence of points forming a clockwise
    exterior linear ring, with the interior of the polygon on the right-hand
    side from a perspective travelling along the line.

    When a polygon is initialised, we remove any consecutive duplicate or
    redundant points, and close the polygon if it is not already closed (i.e.
    ensure that the last point in the polygon is the same as the first point).
    """
    __slots__ = ['points']

    def __init__(self, value):
        if isinstance(value, Polygon):
            self.points = value.points
            return

        points = [Point(x) for x in value]

        # Filter out consecutive identical points.
        last = None
        distinct = []
        for p in points:
            if last is None or p != last:
                distinct.append(p)
                last = p
        points = distinct

        # Filter out redundant points.
        length = len(points)
        boundary = []
        for i, p in enumerate(points):
            if i > 0 and i < length - 1:
                # If the boundary doesn't change angle after this point,
                # then it makes no difference to the shape whether it is
                # included or not.  So don't.
                a = Line(points[i-1], p)
                b = Line(p, points[i+1])
                if a.angle == b.angle:
                    continue
            boundary.append(p)

        # If the polygon isn't closed, close it now.
        if boundary and boundary[0] != boundary[-1]:
            boundary.append(boundary[0])

        if len(boundary) < 4:
            raise ValueError("Not enough valid points for a closed polygon.")

        self.points = tuple(boundary)

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
        if isinstance(key, (int, slice)):
            return self.points[key]
        raise TypeError()

    def __contains__(self, point):
        """Return whether 'point' is spatially equal to any of the polygon's
        vertices.

        Despite the name of the Python magic method, this doesn't test
        "containment" in the geometric sense, but rather it tests *membership*.
        To test whether a geometry is spatially contained in the polygon, use
        contains().
        """
        p = Point(point)
        return any([p.equals(x) for x in self.points])

    def __str__(self):
        return " → ".join(map(str, self.points))

    def __eq__(self, other):
        """Return whether this polygon is equal to another.

        The polygons are considered equal if all their vertices are exactly
        equal, and appear in the same order.  The two polygons do not need to
        begin at the same point.
        """
        if not isinstance(other, Polygon):
            return False
        if len(self) != len(other):
            return False

        return self.points_standard == other.points_standard

    def __hash__(self):
        return hash(tuple('Polygon') + self.points_standard)

    @property
    def points_standard(self):
        """Return this polygon's points with a standardised starting point.

        The result is a linear ring of the points in this polygon, with the
        starting point adjusted to be the point with the lowest 'x' value.  If
        multiple points tie for the lowest 'x' value, the lowest 'y' value
        among them is the start point.

        The main purpose of this property is to enable "apples to apples"
        comparisons between two polygons, and also to make Polygon hashable.
        """
        start = 0
        min_x = None
        min_y = None
        for i, p in enumerate(self.points):
            if min_x is None or p.x < min_x or (p.x == min_x and p.y < min_y):
                start = i
                min_x, min_y = p.x, p.y
        if start == 0:
            return self.points
        return self.points[start:] + self.points[1:start+1]

    @property
    def bbox(self):
        """Return the bounding box for this polygon."""
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
        return BoundingBox(min_x, min_y, max_x, max_y)

    @property
    def lines(self):
        """Return an iterable of all the line segments in the polygon."""
        return [Line(self[i], self[i+1]) for i in range(len(self) - 1)]

    @property
    def is_convex(self):
        """Return whether this polygon is convex.

        The polygon is considered convex if no point lies on the left-hand side
        of the line formed by the preceding two points.
        """
        for i in range(0, len(self) - 2):
            if in_bound(self[i], self[i+1], self[i+2]) is False:
                return False
        return True

    def contains_point(self, value):
        """Return whether the given point is contained by this polygon.

        A polygon only contains points that lie within its interior.  Points on
        the boundary of the polygon are not contained by it.
        """
        p = Point(value)

        # Shortcut case: if the point is not contained by the polygon's
        # bounding box, then it is definitely not contained by the polygon.
        if not self.bbox.contains(p):
            return False

        # Shortcut case: if the point is equal to one of the polygon's
        # vertices, then it is on the boundary.
        if p in self:
            return False

        lines = self.lines
        # Check for the point lying exactly on a boundary line.
        for line in lines:
            if line.intersects_point(p):
                return False

        # Search for the nearest line segment on either side of the point that
        # lie on the same horizontal.
        hlines = [l for l in lines if l.intersects_y(p.y)]
        if not hlines:
            return False

        xdiffs = [l.get_y_intercept(p.y) - p.x for l in hlines]

        left = None
        right = None
        negx = None
        posx = None
        for i, x in enumerate(xdiffs):
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

    def contains_line(self, other):
        """Return whether this polygon contains a Line.

        See comments at Shape.contains for the particulars.
        """
        if self.disjoint(other.a) or self.disjoint(other.b):
            return False

        # Shortcut: for convex polygons, since we have already ruled out
        # endpoints outside the polygon, the line must either lie on a
        # boundary, or be contained by the polygon.
        if self.is_convex:
            for line in self.lines:
                if isinstance(line & other, Line):
                    return False
            return True

        if any([x == other for x in self.lines]):
            return False
        lines = [x for x in self.lines if x.intersects(other)]
        length = len(lines)
        if length == 0:
            # No line intersections, must be fully internal
            return True
        if len(lines) == 1 and isinstance(lines[0] & other, Line):
            # Line intersection on exactly one boundary
            return False

        # If we've arrived here, the line is contained if and only if neither
        # endpoint of the line is out of bounds of any of the polygon
        # boundaries that it intersects.
        for line in lines:
            if (
                    line.in_bound(other.a) is False or
                    line.in_bound(other.b) is False):
                return False
        return True

    def contains_bbox(self, other):
        """Return whether this polygon contains a BoundingBox.

        See comments at Shape.contains for the particulars.
        """
        points = other.points
        for p in points:
            if self.disjoint(p):
                return False

        if self.is_convex:
            return True

        for line in other.boundary:
            if not self.covers_line(line):
                return False
        return True

    def contains_polygon(self, other):
        """Return whether this polygon contains another polygon.

        See comments at Shape.contains for the particulars.
        """
        for p in other.points:
            if self.disjoint(p):
                return False

        if self.is_convex:
            return True

        for line in other.lines:
            if not self.covers_line(line):
                return False
        return True

    def contains(self, other):
        """Return whether this polygon contains some other geometry.

        See comments at Shape.contains for the particulars.
        """
        if isinstance(other, Point):
            return self.contains_point(other)

        # Shortcut: if the geometry is outside this polygon's bounding box,
        # then it definitely isn't contained by the polygon.
        if self.bbox.disjoint(other):
            return False

        if isinstance(other, Line):
            return self.contains_line(other)

        if isinstance(other, BoundingBox):
            return self.contains_bbox(other)

        if isinstance(other, Polygon):
            return self.contains_polygon(other)

        if isinstance(other, Collection):
            return (
                    self.covers(other) and
                    any([self.contains(x) for x in other]))

        raise ValueError(
                f"Unsupported type for polygon contains: {type(other)}.")

    def covers_line(self, other):
        """Return whether this polygon covers a Line.

        See comments at Shape.covers for the particulars.
        """
        if self.disjoint(other.a) or self.disjoint(other.b):
            return False

        # Shortcut: for convex polygons, since we have already ruled out
        # endpoints outside the polygon, the line must either lie on a
        # boundary, or be contained by the polygon.
        if self.is_convex:
            return True

        if any([x == other for x in self.lines]):
            return True

        lines = [x for x in self.lines if x.intersects(other)]
        length = len(lines)
        if length == 0:
            # No line intersections, must be fully internal
            return True
        if len(lines) == 1 and isinstance(lines[0] & other, Line):
            # Line intersection on exactly one boundary
            return True

        # If we've arrived here, the line is covered if and only if neither
        # endpoint of the line is out of bounds of any of the polygon
        # boundaries that it intersects.
        for line in lines:
            if (
                    line.in_bound(other.a) is False or
                    line.in_bound(other.b) is False):
                return False
        return True

    def covers_bbox(self, other):
        """Return whether this polygon covers a BoundingBox.

        See comments at Shape.covers for the particulars.
        """
        points = other.points
        for p in points:
            if self.disjoint(p):
                return False

        if self.is_convex:
            return True

        for line in other.boundary:
            if not self.covers_line(line):
                return False
        return True

    def covers(self, other):
        if self.disjoint(other):
            return False

        if isinstance(other, Point):
            return True

        if isinstance(other, Line):
            return self.covers_line(other)

        if isinstance(other, BoundingBox):
            return self.covers_bbox(other)

    def disjoint(self, other):
        """Return whether this polygon is disjoint with some other geometry.

        Two geometries are disjoint if they share no interior space or boundary
        whatsoever, be it by overlapping, crossing, or touching.
        """
        return not self.intersects(other)

    def intersects_line(self, other):
        """Return whether this polygon intersects a Line.

        See comments at Geometry.intersects for the particulars.
        """
        for line in self.lines:
            if line.intersects(other):
                return True
        return self.contains(other)

    def intersects_bbox(self, other):
        """Return whether this polygon intersects a BoundingBox.

        See comments at geometry.intersects for the particulars.
        """
        for point in other.points:
            if self.intersects(point):
                return True

        for line in self.lines:
            if other.intersects(line):
                return True
        return other.contains(self)

    def intersects_polygon(self, other):
        """Return whether this polygon intersects another polygon.

        See comments at geometry.intersects for the particulars.
        """
        for point in other.points:
            if self.intersects(point):
                return True

        for line in other.lines:
            if self.intersects(line):
                return True
        return other.contains(self)

    def intersects(self, other):
        """Return whether this polygon intersects some other geometry.

        See comments at Geometry.intersects for the particulars.
        """
        # Shortcut: if the geometry is outside this polygon's bounding box,
        # then it definitely doesn't intersect with the polygon.
        if self.bbox.disjoint(other):
            return False

        if isinstance(other, Point):
            # True if the point is on the boundary or in the interior.
            for line in self.lines:
                if line.intersects_point(other):
                    return True
            return self.contains_point(other)

        if isinstance(other, Line):
            return self.intersects_line(other)

        if isinstance(other, BoundingBox):
            return self.intersects_bbox(other)

        if isinstance(other, Polygon):
            return self.intersects_polygon(other)

        raise ValueError(
                f"Unsupported type for polygon intersects: {type(other)}.")

    def intersection_line(self, other):
        """Return the intersection of this Polygon with a Line.

        The result will be None, a Point, a Line, or a Collection of Points and
        Lines.
        """
        if self.disjoint(other):
            return None

        if self.covers(other):
            return other

        if self.is_convex:
            result = other
            for line in self.lines:
                crop = result.crop_line(line)
                if not isinstance(crop, Line):
                    return crop
                result = crop
            return result

        # Non-convex, yuck.  Surely there is a more elegant way to do this, but
        # for now this is all I've got ...
        lines = [x for x in self.lines if x.intersects(other)]
        if not lines:
            return None

        intersections = {x: other.intersection(x) for x in lines}

        def sortkey(line):
            t = intersections[line]
            if isinstance(t, Line):
                return min(other.a.distance(t.a), other.a.distance(t.b))
            return other.a.distance(t)
        lines.sort(key=sortkey)
        remain = other
        result = set()
        for line in lines:
            if line.in_bound(other.a):
                result.add(remain.crop_line(line))
                remain = remain.crop_line(-line)
            else:
                remain = remain.crop_line(line)

        # Filter out points that are covered by lines.
        def f(x):
            return not isinstance(x, Point) or all(
                    [x.disjoint(y) for y in result if x != y])
        result = list(filter(f, result))

        # Merge adjacent lines together
        merged = []
        angle = other
        prev = None
        for item in result:
            if not isinstance(item, Line):
                merged.append(item)
                continue
            if prev and item.intersects(prev):
                assert isinstance(item.intersection(prev), Point)
                # Remove the mutual point and make a new line
                points = set(line.points + prev.points)
                merge = Line(*points)
                if merge.angle != angle:
                    merge = -merge
                merged.append(merge)
                prev = merge
            else:
                merged.append(item)
                prev = item

        result = merged
        if len(result) == 1:
            return result[0]
        return Collection.make(result)

    def intersection_bbox(self, other):
        """Return the intersection of this Polygon with a BoundingBox.

        The result can be any of None, Point, Line, Polygon, or a Collection of
        geometries.
        """
        if self.disjoint(other):
            return None

        if self.covers(other):
            return other

        if other.covers(self):
            return self

        result = self
        for line in other.boundary:
            crop = result.crop_line(line)
            if crop is None:
                return line.intersection(result)
            if isinstance(crop, Point):
                return crop
            result = crop
        return result

    def intersection_polygon(self, other):
        """Return the intersection of this Polygon with another Polygon.

        The result can be any of None, Point, Line, Polygon, or a Collection of
        geometries.
        """
        if self.disjoint(other):
            return None

        if self.covers(other):
            return other

        if other.covers(self):
            return self

        if other.is_convex:
            result = self
            for line in other.lines:
                crop = result.crop_line(line)
                if crop is None:
                    return line.intersection(result)
                if isinstance(crop, Point):
                    return crop
                result = crop
            return result

        # TODO: non-convex
        raise NotImplementedError()

    def intersection(self, other):
        """Return the intersection of this Polygon with some other geometry.
        """
        if self.disjoint(other):
            return None

        if isinstance(other, Point):
            return other

        if isinstance(other, Line):
            return self.intersection_line(other)

        if isinstance(other, BoundingBox):
            return self.intersection_bbox(other)

        if isinstance(other, Polygon):
            return self.intersection_polygon(other)

        if isinstance(other, Collection):
            return self.intersection_collection(other)

        if isinstance(other, Geometry):
            raise NotImplementedError()

        raise ValueError(f"Invalid type for intersection: {type(other)}.")

    def move(self, x=0, y=0):
        """Return a new Polygon spatially shifted relative to this one."""
        points = [p.move(x, y) for p in self.points]
        return Polygon(points)

    def crop_line(self, line):
        """Crop a polygon along an infinite line.

        Consider the line as an infinite Euclidean extending in both
        directions, and return a geometry that encloses the part of the
        original polygon's interior that does not fall on the left-hand side of
        the line.  The result can be None, a Point, a Line, a Polygon, or any
        Collection of Points, Lines and/or Polygons.
        """
        indexes = []
        exact = []
        for i in range(len(self) - 1):
            p = self[i]
            inbound = line.in_bound(p)
            if inbound is not False:
                indexes.append(i)
            if inbound is None:
                exact.append(i)
        if not indexes:
            return None

        if len(indexes) == len(self) - 1:
            return self

        if exact == indexes:
            assert 0 < len(exact) < 3

            if len(exact) == 1:
                return self[exact[0]]

            if len(exact) == 2:
                i, j = exact
                diff = abs(j - i)
                if diff == 1:
                    return Line(self[i], self[j])
                if diff == len(self) - 2:
                    return Line(self[j], self[i])

        if self.is_convex:
            if len(exact) == 2:
                # Shortcut: the crop line runs between two vertices of the
                # polygon
                points = self[:exact[0]+1] + self[exact[1]:]
                return Polygon(points)

            points = []
            inside = 0 in indexes
            for i in range(len(self)):
                if i in indexes or (i == len(self) - 1 and 0 in indexes):
                    if not inside:
                        # Entering the crop area
                        sect = line.extrapolate_intersection(
                                Line(self[i-1], self[i]))
                        points.append(sect)
                        inside = True
                    points.append(self[i])
                else:
                    if inside:
                        # Exiting the crop area
                        sect = line.extrapolate_intersection(
                                Line(self[i-1], self[i]))
                        points.append(sect)
                        inside = False
            return Polygon(points)

        # Non-convex
        shapes = []
        points = UniqueList()
        prev = None
        initial_bound = line.in_bound(self[0])
        prev_bound = initial_bound
        for i, p in enumerate(self.points):
            if prev_bound is False and points:
                # If there is a concavity outside the crop line, break the
                # collected points along the line that leads into the
                # concavity.
                a = self[i-2] if i > 1 else self[-2]
                b = self[i-1]
                ab = Line(a, b)
                if ab.in_bound(p) is False:
                    shape = []
                    for x in points:
                        if ab.in_bound(x) is not False:
                            shape.append(x)
                    shapes.append(shape)
                    points = [x for x in points if x not in shape]

            bound = line.in_bound(p)
            if bound is None or (
                    (i == 0 or prev_bound is not False) and
                    bound is not False):
                points.append(p)

            elif bound is False and prev_bound is True:
                p = line.extrapolate_intersection(Line(prev, p))
                points.append(p)

            elif bound is True and prev_bound is False:
                split = line.extrapolate_intersection(Line(prev, p))
                points.extend((split, p))

            prev = p
            prev_bound = bound
        if points:
            # If we started inside the crop line, merge the final group of
            # collected points with the initial ones.
            if shapes and initial_bound is not False:
                shapes[0].extend(points)
            else:
                shapes.append(points)

        if not shapes:
            return None

        result = []
        for points in shapes:
            if len(points) == 1:
                result.append(points[0])
            elif len(points) == 2:
                result.append(Line(*points))
            else:
                result.append(Polygon(points))

        if len(result) == 1:
            return result[0]

        return union(*result)

    def add_to_plot(self, plot):
        x = [p.x for p in self.points]
        y = [p.y for p in self.points]
        plot.ax.plot(x, y)


class HomogeneousCollection(Collection):
    __slots__ = []
    item_type = None

    def __init__(self, items):
        self.items = set()
        for item in items:
            if not isinstance(item, self.item_type):
                item = self.item_type(item)
            self.items.add(item)


class MultiPoint(HomogeneousCollection):
    __slots__ = []
    item_type = Point


class MultiLine(HomogeneousCollection):
    __slots__ = []
    item_type = Line


class MultiPolygon(Shape, HomogeneousCollection):
    __slots__ = []
    item_type = Polygon


# Class aliases
P = Point
L = Line
B = BoundingBox
Pg = Polygon
Co = Collection
MP = MultiPoint
ML = MultiLine
MPg = MultiPolygon


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
    return Line(a, b).in_bound(p)


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


def get_adjacent_line(a, b, angle, length):
    """Return a new line adjacent to the line (a, b).
    
    The new line will begin at the endpoint (b) of the current line, and its
    direction will be as the current line, rotated counter-clockwise by `angle`
    radians.
    """
    line = Line(a, b)
    return line.get_adjacent_line(angle, length)


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


def _union2(a:Geometry, b:Geometry) -> Geometry:
    """Return a spatial union of two geometries.

    `a` and `b` must be both be geometries.

    The result is a geometry, or a collection of geometries, that includes all the
    points included by any of the arguments, with no interior overlaps between
    `a` and `b`.
    """
    if not isinstance(a, Geometry):
        raise ValueError("Argument 'a' is not a Geometry object.")
    if not isinstance(b, Geometry):
        raise ValueError("Argument 'b' is not a Geometry object.")

    if a == b or (isinstance(a, Shape) and a.covers(b)):
        return a
    if isinstance(b, Shape) and b.covers(a):
        return b
    if a.disjoint(b):
        return Collection.make((a, b))

    # TODO: handle 'touches'
    # TODO: handle interior intersections


def union(*args):
    """Return a spatial union of the arguments.

    Each argument must be a geometry.

    The result is a geometry, or a collection of geometries, that includes all the
    points included by any of the arguments.  Interior overlaps between the
    arguments will be removed.  If there are no arguments, return None.
    """
    if not args:
        return None
    for i, arg in enumerate(args):
        if not isinstance(arg, Geometry):
            raise ValueError(f"Argument {i+1} is not a Geometry object.")

    # Filter out any arguments that are equal to, or covered by, another argument.
    items = []
    for i, a in enumerate(args):
        include = True
        for j, b in enumerate(args):
            if i == j:
                continue
            if a == b or (isinstance(b, Shape) and b.covers(a)):
                include = False
                break
        if include:
            items.append(a)

    if len(args) == 1:
        return args[0]

    return reduce(_union2, args)


def normalise_angle(angle):
    """Normalise an angle in radians.
    
    The result is an angle as a number of radians between π and -π.  A positive
    angle indicates a counter-clockwise turn ("left") and a negative angle
    means a clockwise turn ("right").
    """
    result = angle
    if abs(angle) > π:
        result = angle % TWOπ
    if result > π:
        result -= TWOπ
    elif result < -π:
        result += TWOπ
    return result


def regular_polygon(center:Point, sides:int, radius=None, side_length=None) -> Polygon:
    """Return a regular Polygon
    
    The returned Polygon will have `sides` sides, all sides will be of the same
    length, all angles will be the same size, and its geometric center will lie
    at the `center` point.

    You must specify either a `side_length` or a `radius` to control the size of
    the polygon, but not both.  If you use `radius`, it measures the distance
    between the center and any vertex of the polygon (if the polygon was
    inscribed within a circle, it would be the radius of that circle).

    The polygon will be oriented so that its starting point lies directly above
    the center.
    """
    if not (side_length or radius):
        raise ValueError("Neither side length nor radius given for regular polygon.")
    if side_length and radius:
        raise ValueError("Both side length and radius given for regular polygon.")
    if sides < 3:
        raise ValueError(f"Invalid number of sides for polygon: {sides}.")
    c = Point(center)
    angle = TWOπ / sides  # angle of deflection

    # Special case for triangle
    if sides == 3:
        if side_length:
            x = side_length / 2
            y = x * math.tan(π / 6)
            radius = math.sqrt(x**2 + y**2)
        else:
            y = radius * math.sin(π / 6)
            x = math.sqrt(radius**2 - y**2)
        return Polygon((
            Point(c.x, c.y + radius),
            Point(c.x + x, c.y - y),
            Point(c.x - x, c.y - y)))

    # Special case for square
    if sides == 4:
        if side_length:
            radius = math.sqrt((side_length ** 2) / 2)
        points = (
            Point(c.x, c.y + radius),
            Point(c.x + radius, c.y),
            Point(c.x, c.y - radius),
            Point(c.x - radius, c.y))
        return Polygon(points)

    # Now that we've got triangles and squares out of the way, it's safe to
    # assume deflection angle less than 90 degrees.
    if radius:
        a = Point(c.x, c.y + radius)
        # Work out bx and by relative to the center
        bx = radius * math.sin(angle)
        by = math.sqrt(radius**2 - bx**2)
        b = Point(c.x + bx, c.y + by)
        line = Line(a, b)
        side_length = line.length
    else:
        # Work out bx and by relative to the start point
        interior_angle = π - angle
        bx = side_length * math.sin(interior_angle / 2)
        by = math.sqrt(side_length**2 - bx**2)
        radius = bx / math.sin(angle)
        a = Point(c.x, c.y + radius)
        b = Point(a.x + bx, a.y - by)
        line = Line(a, b)
    last = Point(c.x - bx, b.y)
    points = [a, b]
    for _ in range(sides - 3):
        line = line.get_adjacent_line(-angle, side_length)
        points.append(line.b)
    points.append(last)
    return Polygon(points)
