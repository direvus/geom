# geom

*Geometric primitives in Python*

![GitHub Actions status](https://github.com/direvus/geom/actions/workflows/python-app.yml/badge.svg)

This is a pure Python library that seeks to implement the
[OGC](https://www.ogc.org) spatial predicate functions as defined in the [Dimensionally
Extended 9-Intersection Model](https://en.wikipedia.org/wiki/DE-9IM) (DE-9IM):

- equals
- disjoint
- intersects
- touches
- crosses
- contains
- covers
- within
- overlaps

# Data Model

- *Geometry* (abstract)
  - Point
  - Line
  - *Shape* (abstract)
    - BoundingBox
    - Polygon
  - Collection
    - *HomogeneousCollection* (abstract)
      - MultiPoint
      - MultiLine
      - MultiPolygon (also implements *Shape*)

# Dependencies

Python 3, preferably 3.8+, standard library only.

**Optional**: If you want to generate plots, you will need `matplotlib`, but it isn't required otherwise.

# Purpose

This library was written for self-education and fun.  I don't expect it will
be novel or even really useful to anybody except me.

If you're looking for a fully-fledged implementation of the OGC spatial
relations, you will probably want to use [PostGIS](https://postgis.net).

# License

This project is licensed under the MIT license, a copy of which can be found in
the LICENSE file at the top level of the source code repository.

# Implementation Coverage

The following tables indicate which spatial functions are implemented in the code and covered by tests.

A check mark ✔ means that the feature is implemented and covered by tests.

A tilde ~ means that the feature is implemented but not tested.


|              |              | equals | disjoint | intersects | touches | crosses | contains | covers | within | overlaps |
| ------------ | ------------ | ------ | -------- | ---------- | ------- | ------- | -------- | ------ | ------ | -------- |
| Point        | Point        | ✔      | ✔        | ✔          | ✔       | ✔       | ✔        | ✔      | ✔      | ✔        |
| Point        | Line         | ✔      | ✔        | ✔          | ✔       | ✔       | ✔        | ✔      | ✔      | ✔        |
| Point        | Polygon      | ✔      | ✔        | ✔          | ✔       | ✔       | ✔        | ✔      | ✔      | ✔        |
| Point        | BoundingBox  | ✔      | ✔        | ✔          |         |         |          |        |        |          |
| Point        | MultiPoint   | ~      |          |            |         |         |          |        |        |          |
| Point        | MultiLine    | ~      |          |            |         |         |          |        |        |          |
| Point        | MultiPolygon | ~      |          |            |         |         |          |        |        |          |
| Line         | Point        | ✔      | ~        | ✔          |         |         |          |        |        |          |
| Line         | Line         | ✔      | ~        | ✔          |         |         |          |        |        |          |
| Line         | Polygon      |        | ~        | ~          |         |         |          |        |        |          |
| Line         | BoundingBox  |        | ~        | ~          |         |         |          |        |        |          |
| Line         | MultiPoint   |        |          |            |         |         |          |        |        |          |
| Line         | MultiLine    |        |          |            |         |         |          |        |        |          |
| Line         | MultiPolygon |        |          |            |         |         |          |        |        |          |
