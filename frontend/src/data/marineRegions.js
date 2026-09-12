/**
 * marineRegions.js
 * Pre-defined maritime monitoring regions for BlueTrace global demonstration.
 * These are DEMO / initial monitoring regions — NOT the only areas the system
 * can query. The backend accepts arbitrary global lat/lon/bbox.
 *
 * Each region exposes:
 *   center:   [lon, lat]                          — for vessels/nearby + weather/current
 *   bounds:   [[minLon, minLat], [maxLon, maxLat]] — for satellite/search bbox
 *   radiusKm: number                              — for vessel search radius
 */

function makeRegionPolygon(minLon, minLat, maxLon, maxLat) {
  return {
    type: 'Polygon',
    coordinates: [[
      [minLon, minLat],
      [maxLon, minLat],
      [maxLon, maxLat],
      [minLon, maxLat],
      [minLon, minLat],
    ]],
  }
}

/**
 * @type {Array<{
 *   id: string,
 *   name: string,
 *   zone: string,
 *   center: [number, number],
 *   bounds: [[number, number], [number, number]],
 *   radiusKm: number,
 *   geometry: object,
 *   satellitePass: string,
 *   lastScene: string,
 *   vesselDensity: string,
 * }>}
 */
export const marineRegions = [
  // ── Arabian Sea / Indian Ocean — Core Demonstration Regions ──────────────────────
  {
    id: 'REGION-AS-N',
    name: 'Northern Arabian Sea',
    zone: 'Arabian Sea',
    center: [65.0, 23.5],
    bounds: [[59.0, 20.0], [71.0, 27.0]],
    radiusKm: 350,
    geometry: makeRegionPolygon(59.0, 20.0, 71.0, 27.0),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'High — major shipping corridor',
  },
  {
    id: 'REGION-AS-W',
    name: 'West Arabian Sea / Oman Basin',
    zone: 'Arabian Sea',
    center: [61.0, 17.0],
    bounds: [[56.0, 13.0], [66.0, 21.0]],
    radiusKm: 300,
    geometry: makeRegionPolygon(56.0, 13.0, 66.0, 21.0),
    satellitePass: 'Sentinel-1A',
    lastScene: 'Not available',
    vesselDensity: 'Moderate — tanker routes',
  },
  {
    id: 'REGION-GOK',
    name: 'Gulf of Kutch',
    zone: 'Arabian Sea',
    center: [69.5, 22.5],
    bounds: [[67.5, 21.5], [71.5, 23.5]],
    radiusKm: 120,
    geometry: makeRegionPolygon(67.5, 21.5, 71.5, 23.5),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'High — petroleum port proximity',
  },
  {
    id: 'REGION-MUM',
    name: 'Mumbai Offshore / Mid-Continental Shelf',
    zone: 'Arabian Sea',
    center: [71.5, 19.5],
    bounds: [[70.0, 17.0], [73.0, 22.0]],
    radiusKm: 150,
    geometry: makeRegionPolygon(70.0, 17.0, 73.0, 22.0),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'Very high — ONGC platforms, JNPT traffic',
  },
  {
    id: 'REGION-KER',
    name: 'Kerala / Lakshadweep Sea',
    zone: 'Arabian Sea',
    center: [74.5, 10.5],
    bounds: [[72.5, 8.0], [76.5, 13.0]],
    radiusKm: 200,
    geometry: makeRegionPolygon(72.5, 8.0, 76.5, 13.0),
    satellitePass: 'Sentinel-1A',
    lastScene: 'Not available',
    vesselDensity: 'Moderate — SW monsoon fishery area',
  },
  {
    id: 'REGION-BOB-N',
    name: 'Northern Bay of Bengal',
    zone: 'Bay of Bengal',
    center: [87.0, 20.0],
    bounds: [[83.0, 16.5], [91.0, 23.5]],
    radiusKm: 250,
    geometry: makeRegionPolygon(83.0, 16.5, 91.0, 23.5),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'High — Haldia / Paradip port approaches',
  },
  {
    id: 'REGION-AND',
    name: 'Andaman Sea',
    zone: 'Bay of Bengal',
    center: [93.5, 12.0],
    bounds: [[91.0, 8.0], [96.0, 16.0]],
    radiusKm: 200,
    geometry: makeRegionPolygon(91.0, 8.0, 96.0, 16.0),
    satellitePass: 'Sentinel-1A',
    lastScene: 'Not available',
    vesselDensity: 'Low — remote maritime zone',
  },

  // ── Global Maritime Regions ──────────────────────────────────────────────────
  {
    id: 'REGION-PERSIAN-GULF',
    name: 'Persian Gulf',
    zone: 'Persian Gulf',
    center: [51.0, 26.5],
    bounds: [[48.0, 24.0], [56.5, 29.5]],
    radiusKm: 200,
    geometry: makeRegionPolygon(48.0, 24.0, 56.5, 29.5),
    satellitePass: 'Sentinel-1A',
    lastScene: 'Not available',
    vesselDensity: 'Very high — major oil export corridor',
  },
  {
    id: 'REGION-RED-SEA',
    name: 'Red Sea',
    zone: 'Red Sea',
    center: [38.0, 20.0],
    bounds: [[32.0, 12.5], [44.0, 27.5]],
    radiusKm: 250,
    geometry: makeRegionPolygon(32.0, 12.5, 44.0, 27.5),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'High — Suez Canal approach',
  },
  {
    id: 'REGION-MED-W',
    name: 'Western Mediterranean',
    zone: 'Mediterranean Sea',
    center: [5.0, 38.5],
    bounds: [[-1.0, 35.0], [11.0, 42.0]],
    radiusKm: 350,
    geometry: makeRegionPolygon(-1.0, 35.0, 11.0, 42.0),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'High — European tanker traffic',
  },
  {
    id: 'REGION-SCS-N',
    name: 'South China Sea',
    zone: 'South China Sea',
    center: [114.0, 15.0],
    bounds: [[108.0, 9.0], [120.0, 21.0]],
    radiusKm: 400,
    geometry: makeRegionPolygon(108.0, 9.0, 120.0, 21.0),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'Very high — busiest shipping lane',
  },
  {
    id: 'REGION-MALACCA',
    name: 'Strait of Malacca',
    zone: 'Indian Ocean / South China Sea',
    center: [103.5, 2.5],
    bounds: [[99.0, 0.5], [108.0, 5.5]],
    radiusKm: 200,
    geometry: makeRegionPolygon(99.0, 0.5, 108.0, 5.5),
    satellitePass: 'Sentinel-1A',
    lastScene: 'Not available',
    vesselDensity: 'Very high — critical chokepoint',
  },
  {
    id: 'REGION-GOX',
    name: 'Gulf of Mexico',
    zone: 'Gulf of Mexico',
    center: [-90.0, 25.0],
    bounds: [[-97.0, 18.0], [-82.0, 30.5]],
    radiusKm: 500,
    geometry: makeRegionPolygon(-97.0, 18.0, -82.0, 30.5),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'Very high — major oil production zone',
  },
  {
    id: 'REGION-NAT',
    name: 'North Atlantic (NW European Approaches)',
    zone: 'North Atlantic',
    center: [-10.0, 50.0],
    bounds: [[-20.0, 44.0], [0.0, 56.0]],
    radiusKm: 450,
    geometry: makeRegionPolygon(-20.0, 44.0, 0.0, 56.0),
    satellitePass: 'Sentinel-1A/B',
    lastScene: 'Not available',
    vesselDensity: 'High — transatlantic route',
  },
]

/** Build a GeoJSON FeatureCollection from all regions for map rendering. */
export function buildRegionFeatureCollection(selectedRegionId = null) {
  return {
    type: 'FeatureCollection',
    features: marineRegions.map((region) => ({
      type: 'Feature',
      id: region.id,
      properties: {
        id: region.id,
        name: region.name,
        zone: region.zone,
        selected: region.id === selectedRegionId,
      },
      geometry: region.geometry,
    })),
  }
}
