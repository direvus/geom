#!/usr/bin/env python3
# coding: utf-8
import math
from decimal import Decimal


ABS_TOL = 1e-8


def flatten_coords(*args):
    """Take arbitrarily structured coordinate pairs and flatten them.

    The arguments may be structured in a variety of forms, for example:
    - [(x0, y0), (x1, y1), ...]
    - [x0, y0, x1, y1, ...]
    - [{'x': x0, 'y': y0}, {'x': x1, 'y': y1}, ...]
    - [{'lon': x0, 'lat': y0}, {'lon': x1, 'lat': y1}, ...]

    The return is a flattened sequence of coordinate pairs, e.g.:
    [x0, y0, x1, y1, ...]

    If the inputs are sequences, their axis order will be preserved.  If the
    inputs are dicts, the axis order will be returned in X, Y order (lon, lat).
    """
    result = []
    for arg in args:
        try:
            keys = arg.keys()
            if 'x' in keys and 'y' in keys:
                result.append(arg['x'])
                result.append(arg['y'])
            elif 'lat' in keys and 'lon' in keys:
                result.append(arg['lon'])
                result.append(arg['lat'])
            else:
                raise ValueError(
                        f"Unrecognised dictionary structure with keys {keys}. "
                        "Expected x, y or lat, lon.")
            continue
        except AttributeError:
            pass

        try:
            items = (x for x in arg)
            result.extend(flatten_coords(*items))
            continue
        except TypeError:
            pass

        try:
            result.append(Decimal(arg))
        except ValueError:
            raise ValueError(f"Unable to interpret {arg} as a Decimal value.")

    if len(result) % 2 != 0:
        raise ValueError(
                f"Invalid number of coords {len(result)}. "
                "Expected an even number.")
    return result


def float_close(a, b):
    """Return whether two floating point values are "nearly" equal.

    This comparison is carried out using the Python standard library
    math.isclose() function, with the default relative tolerance, and an
    absolute tolerance from a module-level constant in this module.
    """
    return math.isclose(a, b, abs_tol=ABS_TOL)


def float_not_close(a, b):
    """Return whether two floating point values are not nearly equal."""
    return not float_close(a, b)


def float_gt(a, b):
    """Return whether one float is significantly greater than another.

    Return True if 'a' is greater than 'b' and also not nearly equal to 'b'.
    """
    return float(a) > float(b) and not float_close(a, b)


def float_lt(a, b):
    """Return whether one float is significantly less than another.

    Return True if 'a' is less than 'b' and also not nearly equal to 'b'.
    """
    return float(a) < float(b) and not float_close(a, b)


def get_bbox(*points):
    """Return the bounding box for a sequence of points.

    The return is a 4-tuple containing the minima for the coordinates in the
    input, followed by the maxima, in the same axis order as the input.

    For example, if the input points are coordinates in X, Y axis order, then
    the return tuple will be:

    (min_x, min_y, max_x, max_y)

    Likewise, if the input points are geographic coordinates in lon, lat order,
    then the return tuple will be:

    (min_lon, min_lat, max_lon, max_lat), or
    (west, south, east, north)
    """
    coords = flatten_coords(*points)
    min_x = None
    min_y = None
    max_x = None
    max_y = None
    for i in range(0, len(coords), 2):
        x, y = coords[i:i+2]
        if min_x is None or x < min_x:
            min_x = x
        if min_y is None or y < min_y:
            min_y = y
        if max_x is None or x > max_x:
            max_x = x
        if max_y is None or y > max_y:
            max_y = y
    return (min_x, min_y, max_x, max_y)


def in_bbox(box, point, exact=True):
    """Return whether a given point lies inside of a bounding box.

    Given a bounding box in (min_x, min_y, max_x, max_y) form, return whether
    the given point lies inside that bounding box.  If the 'exact' argument is
    True, then points lying exactly on the boundary will yield True.
    Otherwise, they will yield False.
    """
    if (float_lt(point[0], box[0]) or
            float_gt(point[0], box[2]) or
            float_lt(point[1], box[1]) or
            float_gt(point[1], box[3])):
        return False

    if (float_close(point[0], box[0]) or
            float_close(point[0], box[2]) or
            float_close(point[1], box[1]) or
            float_close(point[1], box[3])):
        return exact

    return True
