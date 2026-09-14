export function isValidCoordinate(coordinate) {
  return Array.isArray(coordinate) && coordinate.length === 2 && Number.isFinite(coordinate[0]) && Number.isFinite(coordinate[1]) && coordinate[0] >= -180 && coordinate[0] <= 180 && coordinate[1] >= -90 && coordinate[1] <= 90
}

export function toPointFeature(coordinates, properties = {}) { return isValidCoordinate(coordinates) ? { type: 'Feature', properties, geometry: { type: 'Point', coordinates } } : null }
export function toLineFeature(coordinates, properties = {}) { const validCoordinates = coordinates.filter(isValidCoordinate); return validCoordinates.length > 1 ? { type: 'Feature', properties, geometry: { type: 'LineString', coordinates: validCoordinates } } : null }
export function toFeatureCollection(features) { return { type: 'FeatureCollection', features: features.filter(Boolean) } }

export function calculateMapBounds(coordinates, padding = 0.08) {
  const validCoordinates = coordinates.filter(isValidCoordinate); if (!validCoordinates.length) return null
  const longitudes = validCoordinates.map(([longitude]) => longitude); const latitudes = validCoordinates.map(([, latitude]) => latitude); const minLongitude = Math.min(...longitudes); const maxLongitude = Math.max(...longitudes); const minLatitude = Math.min(...latitudes); const maxLatitude = Math.max(...latitudes); const longitudePadding = Math.max((maxLongitude - minLongitude) * padding, 0.12); const latitudePadding = Math.max((maxLatitude - minLatitude) * padding, 0.12)
  return [[minLongitude - longitudePadding, minLatitude - latitudePadding], [maxLongitude + longitudePadding, maxLatitude + latitudePadding]]
}

export function formatCoordinates([longitude, latitude], precision = 3) { return `${latitude.toFixed(precision)}° N, ${longitude.toFixed(precision)}° E` }
export function kilometersToNauticalMiles(kilometers) { return kilometers / 1.852 }
