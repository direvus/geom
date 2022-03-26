#!/usr/bin/env python3
# coding: utf-8
from decimal import Decimal


EPSILON = 0.000000001


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


def float_eq(a, b):
    """Return whether two floating point values are "nearly" equal.

    Two floats are considered equal if the difference between them is less than
    the EPSILON value.
    """
    return abs(float(a) - float(b)) < EPSILON


def float_gt(a, b):
    """Return whether one floating point value is greater than another.

    'a' is considered greater than 'b' if it exceeds 'b' by at least the
    EPSILON value.
    """
    return float(a) > float(b) + EPSILON


def float_lt(a, b):
    """Return whether one floating point value is less than another.

    'a' is considered less than 'b' if it falls below 'b' by at least the
    EPSILON value.
    """
    return float(a) < float(b) - EPSILON
