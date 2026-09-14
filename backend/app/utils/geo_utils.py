"""
utils/geo_utils.py
==================
Geospatial processing utilities using Rasterio and Shapely:
  - Vectorize binary masks into RFC 7946 GeoJSON Polygons using Rasterio affine transforms
  - Compute spatial centroid (lat, lon) and area (km²) from vector geometries
  - Support native Sentinel-1 GeoTIFF Affine transforms & CRS reprojection
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Optional rasterio and shapely imports for environment compatibility
try:
    import rasterio
    from rasterio.affine import Affine
    from rasterio.features import shapes
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    Affine = None

try:
    from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape as shapely_shape
    from shapely.ops import transform as shapely_transform
    import pyproj
    SHAPELY_AVAILABLE = True

    WGS84_CRS = pyproj.CRS("EPSG:4326")
    WEBMERCATOR_CRS = pyproj.CRS("EPSG:3857")
    PROJECT_TO_METERS = pyproj.Transformer.from_crs(WGS84_CRS, WEBMERCATOR_CRS, always_xy=True).transform
except ImportError:
    SHAPELY_AVAILABLE = False


def create_affine_transform(
    width: int = 256,
    height: int = 256,
    center_lat: float = 19.05,
    center_lon: float = 72.85,
    pixel_scale_km: float = 0.01,
) -> Any:
    """
    Constructs an Affine transform for images lacking embedded GeoTIFF metadata.
    Maps pixel coordinates (col, row) -> (longitude, latitude) based on pixel resolution.
    NO hardcoded scene bounds.
    """
    deg_per_km_lat = 1.0 / 111.0
    deg_per_km_lon = 1.0 / (111.0 * math.cos(math.radians(center_lat)))

    pixel_deg_lat = pixel_scale_km * deg_per_km_lat
    pixel_deg_lon = pixel_scale_km * deg_per_km_lon

    top_left_lon = center_lon - (width / 2.0) * pixel_deg_lon
    top_left_lat = center_lat + (height / 2.0) * pixel_deg_lat

    if RASTERIO_AVAILABLE and Affine:
        return Affine(pixel_deg_lon, 0.0, top_left_lon, 0.0, -pixel_deg_lat, top_left_lat)

    return (pixel_deg_lon, 0.0, top_left_lon, 0.0, -pixel_deg_lat, top_left_lat)


def mask_to_geojson_polygon(
    binary_mask: np.ndarray,
    transform: Optional[Any] = None,
    center_lat: float = 19.05,
    center_lon: float = 72.85,
    pixel_scale_km: float = 0.01,
    source_crs: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Vectorize binary mask into RFC 7946 GeoJSON Polygon/MultiPolygon using Rasterio shapes.
    """
    height, width = binary_mask.shape

    if transform is None:
        transform = create_affine_transform(
            width=width,
            height=height,
            center_lat=center_lat,
            center_lon=center_lon,
            pixel_scale_km=pixel_scale_km,
        )

    if RASTERIO_AVAILABLE and SHAPELY_AVAILABLE:
        if not isinstance(transform, Affine) and Affine:
            transform = Affine(*transform)

        mask = binary_mask.astype(np.int32) == 1
        extracted_shapes = list(shapes(mask, mask=mask, transform=transform))

        if not extracted_shapes:
            return {"type": "Polygon", "coordinates": []}

        geoms = []
        for geom_dict, val in extracted_shapes:
            s = shapely_shape(geom_dict)
            if source_crs and source_crs != WGS84_CRS:
                transformer = pyproj.Transformer.from_crs(source_crs, WGS84_CRS, always_xy=True).transform
                s = shapely_transform(transformer, s)
            geoms.append(s)

        if not geoms:
            return {"type": "Polygon", "coordinates": []}

        combined = geoms[0] if len(geoms) == 1 else MultiPolygon(geoms)
        return combined.__geo_interface__

    # Pure NumPy geometry extraction fallback
    y_indices, x_indices = np.where(binary_mask > 0)
    if len(x_indices) == 0:
        return {"type": "Polygon", "coordinates": []}

    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.0 * math.cos(math.radians(center_lat))
    min_x, max_x = float(np.min(x_indices)), float(np.max(x_indices))
    min_y, max_y = float(np.min(y_indices)), float(np.max(y_indices))

    center_x, center_y = width / 2.0, height / 2.0
    px_to_lon = lambda px: center_lon + ((px - center_x) * pixel_scale_km / km_per_deg_lon)
    px_to_lat = lambda py: center_lat + ((center_y - py) * pixel_scale_km / km_per_deg_lat)

    ring = [
        [px_to_lon(min_x), px_to_lat(min_y)],
        [px_to_lon(max_x), px_to_lat(min_y)],
        [px_to_lon(max_x), px_to_lat(max_y)],
        [px_to_lon(min_x), px_to_lat(max_y)],
        [px_to_lon(min_x), px_to_lat(min_y)],
    ]
    return {"type": "Polygon", "coordinates": [ring]}


def calculate_centroid_and_area(
    binary_mask: np.ndarray,
    transform: Optional[Any] = None,
    center_lat: float = 19.05,
    center_lon: float = 72.85,
    pixel_scale_km: float = 0.01,
    source_crs: Optional[Any] = None,
) -> Tuple[Optional[Tuple[float, float]], float, Dict[str, float]]:
    """
    Calculate spatial centroid (lat, lon), area in km², and bounding box (WGS84).
    """
    geojson = mask_to_geojson_polygon(
        binary_mask,
        transform=transform,
        center_lat=center_lat,
        center_lon=center_lon,
        pixel_scale_km=pixel_scale_km,
        source_crs=source_crs,
    )

    if not geojson.get("coordinates"):
        return None, 0.0, {"min_lat": center_lat, "min_lon": center_lon, "max_lat": center_lat, "max_lon": center_lon}

    if SHAPELY_AVAILABLE:
        geom = shapely_shape(geojson)
        centroid = geom.centroid

        projected_geom = shapely_transform(PROJECT_TO_METERS, geom)
        area_km2 = projected_geom.area / 1000000.0

        bounds = geom.bounds
        bbox = {
            "min_lat": round(bounds[1], 6),
            "min_lon": round(bounds[0], 6),
            "max_lat": round(bounds[3], 6),
            "max_lon": round(bounds[2], 6),
        }
        return (round(centroid.y, 6), round(centroid.x, 6)), round(area_km2, 4), bbox

    # Pure NumPy fallback
    y_indices, x_indices = np.where(binary_mask > 0)
    pixel_count = len(x_indices)
    height, width = binary_mask.shape
    center_x, center_y = width / 2.0, height / 2.0

    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.0 * math.cos(math.radians(center_lat))

    mean_x, mean_y = float(np.mean(x_indices)), float(np.mean(y_indices))
    centroid_lon = center_lon + ((mean_x - center_x) * pixel_scale_km / km_per_deg_lon)
    centroid_lat = center_lat + ((center_y - mean_y) * pixel_scale_km / km_per_deg_lat)

    area_km2 = float(pixel_count * (pixel_scale_km ** 2))
    min_x, max_x = float(np.min(x_indices)), float(np.max(x_indices))
    min_y, max_y = float(np.min(y_indices)), float(np.max(y_indices))

    bbox = {
        "min_lat": round(center_lat + ((center_y - max_y) * pixel_scale_km / km_per_deg_lat), 6),
        "min_lon": round(center_lon + ((min_x - center_x) * pixel_scale_km / km_per_deg_lon), 6),
        "max_lat": round(center_lat + ((center_y - min_y) * pixel_scale_km / km_per_deg_lat), 6),
        "max_lon": round(center_lon + ((max_x - center_x) * pixel_scale_km / km_per_deg_lon), 6),
    }

    return (round(centroid_lat, 6), round(centroid_lon, 6)), round(area_km2, 4), bbox
