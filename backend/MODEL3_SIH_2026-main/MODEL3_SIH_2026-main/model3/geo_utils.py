"""
geo_utils.py
============
Shared geographic math. Distances use the haversine great-circle formula
(never naive Euclidean lat/lon deltas) as required by the spec, since 1 degree
of longitude varies enormously with latitude.
"""

from __future__ import annotations

import math
from typing import Iterable, List, Optional, Tuple

EARTH_RADIUS_KM = 6371.0088

Coordinate = Tuple[float, float]


def haversine_km(a: Coordinate, b: Coordinate) -> float:
    """Great-circle distance in km between two (lat, lon) points."""
    lat1, lon1 = a
    lat2, lon2 = b
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    h = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    h = min(1.0, max(0.0, h))  # guard against fp error pushing outside [0,1]
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def bearing_deg(a: Coordinate, b: Coordinate) -> float:
    """Initial compass bearing (0-360, 0=N) from point a to point b."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360.0) % 360.0


def angular_diff_deg(a: float, b: float) -> float:
    """Smallest absolute difference between two compass angles, in [0, 180]."""
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def point_in_polygon(point: Coordinate, polygon: List[Coordinate]) -> bool:
    """Ray-casting point-in-polygon test. `polygon` is a list of (lat, lon)
    treated as a simple planar ring -- adequate for the small (<~1-2 deg)
    spill extents this system deals with; not valid across the antimeridian
    or poles."""
    if len(polygon) < 3:
        return False
    x, y = point[1], point[0]  # use (lon, lat) as planar (x, y)
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i][1], polygon[i][0]
        xj, yj = polygon[j][1], polygon[j][0]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def min_distance_to_polygon_km(point: Coordinate, polygon: List[Coordinate]) -> float:
    """Minimum haversine distance from `point` to any vertex/edge-sample of
    `polygon`. Uses vertex + edge-midpoint sampling, which is a lightweight
    approximation adequate for spill-scale polygons; swap in a proper
    point-to-segment geodesic routine if higher precision is later needed."""
    if not polygon:
        return math.inf
    candidates: List[Coordinate] = list(polygon)
    n = len(polygon)
    for i in range(n):
        a = polygon[i]
        b = polygon[(i + 1) % n]
        mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        candidates.append(mid)
    return min(haversine_km(point, c) for c in candidates)


def polyline_min_distance_to_point_km(points: Iterable[Coordinate], target: Coordinate) -> float:
    """Minimum haversine distance from any point on a (sampled) trajectory to
    a target point. This samples only at the given AIS ping locations (not
    interpolated great-circle segments) -- documented approximation, fine
    given typical AIS ping density."""
    dists = [haversine_km(p, target) for p in points]
    return min(dists) if dists else math.inf
