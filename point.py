#!/usr/bin/env python3
# coding: utf-8
from util import float_eq


class Point():
    def __init__(self, value):
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

        raise ValueError("Unknown input type for Point: {type(value)}.")

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

    def __str__(self):
        return f"({self.x},{self.y})"


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
