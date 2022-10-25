# geom

*Geometric primitives in Python*

This is a pure Python library that seeks to implement the
[OGC](https://www.ogc.org) spatial predicates as defined in the [Dimensionally
Extended 9-Intersection Model](https://en.wikipedia.org/wiki/DE-9IM) (DE-9IM):

- equals
- disjoint
- intersects
- touches
- crosses
- within
- contains
- overlaps

# Data Model

- *Geometry* (abstract)
  - Point
  - Line
  - *Shape* (abstract)
    - BoundingBox
    - Polygon
    - Circle

# Dependencies

Python 3, standard library only.

**Optional**: If you want to generate plots, you will need `matplotlib`, but it isn't required otherwise.

# Purpose

This library was written for self-education and fun.  I don't expect it will
be novel or even really useful to anybody except me.

If you're looking for a fully-fledged implementation of the OGC spatial
relations, you will probably want to use [PostGIS](https://postgis.net).

# License

This project is licensed under the MIT license, a copy of which can be found in
the LICENSE file at the top level of the source code repository.
