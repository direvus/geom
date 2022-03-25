#!/usr/bin/env python3
import math
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


def point_eq(a, b):
    """Return whether two points (coordinate pairs) are "nearly" equal.

    Two points are considered equal if the differences between their respective
    ordinates are both less than the EPSILON value.
    """
    return float_eq(a[0], b[0]) and float_eq(a[1], b[1])


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

    if (float_eq(point[0], box[0]) or
            float_eq(point[0], box[2]) or
            float_eq(point[1], box[1]) or
            float_eq(point[1], box[3])):
        return exact

    return True


def in_bound(a, b, p):
    """Return whether a given point lies within a boundary line.

    Given a line that runs from point 'a' to point 'b', and extends infinitely
    in both directions, return whether the point 'p' lies on the right-hand
    side of that line.  If the point lies exactly on the line, return None.
    """
    # If A and B are equal, that doesn't define a line
    if a == b:
        raise ValueError(
                "Boundary line must be described using two distinct points.")

    # Shortcut case: P is equal to A or B
    if point_eq(a, p) or point_eq(b, p):
        return None

    # Shortcut case: horizontal or vertical lines
    if a[1] == b[1]:
        if float_eq(p[1], a[1]):
            return None
        return p[1] < a[1] if a[0] < b[0] else p[1] > a[1]

    if a[0] == b[0]:
        if float_eq(p[0], a[0]):
            return None
        return p[0] > a[0] if a[1] < b[1] else p[0] < a[0]

    # Find the point on the line that has the same x-value as P, and then see
    # whether P lies above or below that point.
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    gradient = dy / dx

    x_dist = p[0] - a[0]
    y = a[1] + x_dist * gradient

    if float_eq(p[1], y):
        return None
    return p[1] < y if a[0] < b[0] else p[1] > y


def intersects_h(a, b, y):
    """Return whether a line intersects with a horizontal.

    Return True if any point on the line between points 'a' and 'b', including
    the points themselves, lies at the given 'y' value.  Horizontal lines are
    not considered to intersect any 'y' value.
    """
    if a[1] == b[1]:
        return False
    if a[1] > b[1]:
        a, b = b, a
    return not (float_gt(a[1], y) or float_lt(b[1], y))


def intersects_v(a, b, x):
    """Return whether a line intersects with a vertical.

    Return True if any point on the line between points 'a' and 'b', including
    the points themselves, lies at the given 'x' value.  Vertical lines are
    not considered to intersect any 'x' value.
    """
    if a[0] == b[0]:
        return False
    if a[0] > b[0]:
        a, b = b, a
    return not (float_gt(a[0], x) or float_lt(b[0], x))


def get_intercept_h(a, b, y):
    """Return the x-value where a line intersects a horizontal.

    Given a line that intersects points 'a' and 'b', and a horizontal with
    y-value 'y', return the x-value of the point where the horizontal meets the
    line.

    Return None if the line between 'a' and 'b' is itself horizontal.
    """
    if a[1] == b[1]:
        return None
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    grad = dx / dy
    return a[0] + (y - a[1]) * grad


def normalise_polygon(points):
    """Return a normalised polygon.

    The polygon must be given as a sequence of points forming a clockwise
    exterior linear ring, with the interior of the polygon on the right-hand
    side.

    The return is a sequence of coordinate pairs, after flattening out any
    structure around the input points, removing any consecutive duplicate
    points, and closing the polygon if it is not already closed.
    """
    # Normalise the coordinate structure to [(x0, y0), (x1, y1), ...]
    coords = flatten_coords(points)
    poly = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]

    # Filter out consecutive identical points from the polygon.
    poly = [x for i, x in enumerate(poly) if i == 0 or x != poly[i-1]]

    # If the polygon isn't closed, close it now.
    if poly[0] != poly[-1]:
        poly.append(poly[0])

    # TODO: disallow backtracking along the same line

    if len(poly) < 4:
        raise ValueError("Not enough valid points for a closed polygon.")
    return poly


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


def in_polygon(poly, point, exact=True):
    """Return whether the given point lies inside a polygon.

    The polygon must be given as a sequence of points forming a clockwise
    exterior linear ring, with the interior of the polygon on the right-hand
    side.

    If 'exact' is True, then points lying exactly on the boundary of the
    polygon will be treated as inside.  Otherwise they will be treated as
    outside.
    """
    poly = normalise_polygon(poly)

    # Shortcut case: if the point is outside the polygon's bounding box, then
    # it is definitely outside the polygon.
    box = get_bbox(poly)
    if not in_bbox(box, point, exact):
        return False

    # Shortcut case: if the point is equal to one of the polygon's vertices,
    # then it is on the boundary.
    for vertex in poly:
        if point_eq(vertex, point):
            return exact

    lines = get_polygon_lines(poly)
    # Edge case: check for the point lying exactly on a horizontal boundary of
    # the polygon.
    for a, b in lines:
        if (intersects_v(a, b, point[0]) and
                a[1] == b[1] and
                float_eq(a[1], point[1])):
            return exact

    # Search for the nearest line segment on either side of the point that lie
    # on the same horizontal.
    hlines = [x for x in lines if intersects_h(x[0], x[1], point[1])]
    xdiffs = [get_intercept_h(a, b, point[1]) - point[0] for a, b in hlines]

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

    return rline[0][1] > rline[1][1] and lline[0][1] < lline[1][1]
