#!/usr/bin/env python3
# coding: utf-8


from line import in_bound, get_intercept_h, intersects_v, intersects_h
from util import flatten_coords, float_eq, float_lt, float_gt, point_eq


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


def point_in_polygon(poly, point, exact=True):
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
