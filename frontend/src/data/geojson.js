import { incidents } from './incidents'

export const slickExtents = {
  type: 'FeatureCollection',
  features: incidents.map((incident) => ({ type: 'Feature', properties: { incident_id: incident.id, location_name: incident.location_name, label: 'Surface Slick Extent', classification: incident.classification, area_km2: incident.area_km2, is_demonstration_data: true }, geometry: { type: 'Polygon', coordinates: [incident.polygon] } })),
}

const corridors = {
  'INC-024': [[72.815, 18.910], [72.671, 18.805], [72.657, 18.826], [72.797, 18.937], [72.815, 18.910]],
  'INC-025': [[69.671, 22.665], [69.521, 22.583], [69.509, 22.609], [69.650, 22.692], [69.671, 22.665]],
  'INC-026': [[80.446, 13.248], [80.402, 13.383], [80.376, 13.364], [80.417, 13.243], [80.446, 13.248]],
  'INC-027': [[87.124, 18.296], [87.006, 18.369], [86.982, 18.396], [87.099, 18.322], [87.124, 18.296]],
  'INC-028': [[75.753, 10.566], [75.618, 10.462], [75.595, 10.493], [75.729, 10.593], [75.753, 10.566]],
}

export const reverseDriftCorridors = {
  type: 'FeatureCollection',
  features: Object.entries(corridors).map(([incidentId, coordinates]) => ({ type: 'Feature', properties: { incident_id: incidentId, label: 'Mock reverse-drift probability corridor', is_demonstration_data: true, modeled_hours: 12, probability_note: 'Indicative uncertainty envelope, not an exact route' }, geometry: { type: 'Polygon', coordinates: [coordinates] } })),
}

export const mapReferenceLayers = {
  ports: { type: 'FeatureCollection', features: [{ type: 'Feature', properties: { name: 'Mumbai Port' }, geometry: { type: 'Point', coordinates: [72.88, 18.94] } }, { type: 'Feature', properties: { name: 'Chennai Port' }, geometry: { type: 'Point', coordinates: [80.32, 13.10] } }, { type: 'Feature', properties: { name: 'Paradip Port' }, geometry: { type: 'Point', coordinates: [86.68, 20.27] } }] },
  platforms: { type: 'FeatureCollection', features: [{ type: 'Feature', properties: { name: 'Mumbai High (demo reference)' }, geometry: { type: 'Point', coordinates: [72.21, 19.16] } }, { type: 'Feature', properties: { name: 'KG Basin (demo reference)' }, geometry: { type: 'Point', coordinates: [82.32, 16.52] } }] },
  coastline: { type: 'FeatureCollection', features: [{ type: 'Feature', properties: { label: 'Indicative coastline reference' }, geometry: { type: 'LineString', coordinates: [[72.76, 18.45], [72.83, 18.7], [72.88, 18.94], [72.94, 19.18]] } }, { type: 'Feature', properties: { label: 'Indicative coastline reference' }, geometry: { type: 'LineString', coordinates: [[80.2, 12.85], [80.28, 13.03], [80.36, 13.22], [80.44, 13.42]] } }] },
}
