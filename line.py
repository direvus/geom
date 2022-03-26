#!/usr/bin/env python3
# coding: utf-8
from util import float_eq, float_gt, float_lt
from point import Point


class Line():
    def __init__(self, a, b):
        self.a = Point(a)
        self.b = Point(b)

        if a == b:
            raise ValueError("Invalid line: the two points are equal.")

    @property
    def is_horizontal(self):
        return self.a[1] == self.b[1]

    @property
    def is_vertical(self):
        return self.a[0] == self.b[0]

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
        return (self.b[1] - self.a[1]) / (self.b[0] - self.a[0])

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

    def get_intersection(self, other):
        """Return the point of intersection between two lines.

        If the lines are not parallel, return the (x, y) point where the lines
        intersect.

        If the lines are parallel, return None.
        """
        if self.is_vertical:
            if other.is_vertical:
                return None
            if other.is_horizontal:
                return (self.a[0], other.a[1])
            xdist = self.a[0] - other.a[0]
            return (self.a[0], other.a[1] + xdist * other.gradient)

        if other.is_vertical:
            if self.is_horizontal:
                return (other.a[0], self.a[1])
            xdist = other.a[0] - self.a[0]
            return (other.a[0], self.a[1] + xdist * self.gradient)

        if self.is_horizontal:
            if other.is_horizontal:
                return None
            ydist = self.a[1] - other.a[1]
            return (other.a[0] + ydist * 1 / other.gradient, self.a[1])

        if other.is_horizontal:
            ydist = other.a[1] - self.a[1]
            return (self.a[0] + ydist * 1 / self.gradient, other.a[1])

        convergence = self.gradient - other.gradient
        ydist = other.get_x_intercept(self.a[0]) - self.a[1]
        x = self.a[0] + ydist / convergence
        return (x, self.get_x_intercept(x))

    def __neg__(self):
        """Return the negation of the line.

        The result is a line with the same points, but travelling in the
        opposite direction (a and b are reversed).
        """
        return Line(self.b, self.a)


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


def intersects_h(a, b, y):
    """Return whether a line intersects with a horizontal.

    Return True if any point on the line between points 'a' and 'b', including
    the points themselves, lies at the given 'y' value.  Horizontal lines are
    not considered to intersect any 'y' value.
    """
    return Line(a, b).intersects_y(y)


def intersects_v(a, b, x):
    """Return whether a line intersects with a vertical.

    Return True if any point on the line between points 'a' and 'b', including
    the points themselves, lies at the given 'x' value.  Vertical lines are
    not considered to intersect any 'x' value.
    """
    return Line(a, b).intersects_x(x)


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
