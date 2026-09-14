/**
 * transformers.js
 * Adapter utility converting FastAPI FullAnalysisResponse into frontend data structures.
 */

// Helper to compute geodesic distance between two points (in km) via Haversine formula
function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371.0
  const dLat = ((lat2 - lat1) * Math.PI) / 180.0
  const dLon = ((lon2 - lon1) * Math.PI) / 180.0
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180.0) *
      Math.cos((lat2 * Math.PI) / 180.0) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

// Calculate exact perimeter in km from GeoJSON polygon coordinates [[lon, lat], ...]
function calculatePolygonPerimeterKm(coordinates) {
  if (!Array.isArray(coordinates) || coordinates.length < 3) return null
  let totalKm = 0
  for (let i = 0; i < coordinates.length; i++) {
    const nextIdx = (i + 1) % coordinates.length
    const [lon1, lat1] = coordinates[i]
    const [lon2, lat2] = coordinates[nextIdx]
    totalKm += haversineKm(lat1, lon1, lat2, lon2)
  }
  return Math.round(totalKm * 100) / 100
}

// Build downwind drift corridor polygon from centroid and wind direction
function createDriftCorridorFeature(analysisId, lat, lon, windDirDeg) {
  if (windDirDeg === undefined || windDirDeg === null || Number.isNaN(Number(windDirDeg))) {
    return null
  }
  const driftDeg = (Number(windDirDeg) + 180) % 360
  const driftRad = ((90 - driftDeg) * Math.PI) / 180.0
  const spreadRad = (25 * Math.PI) / 180.0

  const lengthDeg = 0.12 // approx 13 km
  const widthDeg = 0.05

  const p1 = [lon, lat]
  const p2 = [
    lon + lengthDeg * Math.cos(driftRad - spreadRad),
    lat + lengthDeg * Math.sin(driftRad - spreadRad),
  ]
  const p3 = [
    lon + (lengthDeg + widthDeg) * Math.cos(driftRad),
    lat + (lengthDeg + widthDeg) * Math.sin(driftRad),
  ]
  const p4 = [
    lon + lengthDeg * Math.cos(driftRad + spreadRad),
    lat + lengthDeg * Math.sin(driftRad + spreadRad),
  ]

  return {
    type: 'Feature',
    properties: {
      incident_id: analysisId,
    },
    geometry: {
      type: 'Polygon',
      coordinates: [[p1, p2, p3, p4, p1]],
    },
  }
}

export function transformAnalysisResponse(data, originalParams = {}) {
  if (!data) return null

  const analysisId = data.analysis_id || `SPILL_${Date.now()}`
  const lat = data.location?.lat ?? originalParams.lat ?? 19.05
  const lon = data.location?.lon ?? originalParams.lon ?? 72.85
  
  // Ensure valid ISO UTC string for date formatting
  let timestampUtc = data.timestamp_utc
  if (!timestampUtc || Number.isNaN(Date.parse(timestampUtc))) {
    timestampUtc = new Date().toISOString()
  }

  const detection = data.detection || {}
  const classificationObj = data.classification || {}
  const weather = data.weather || {}
  const attribution = data.attribution || {}

  // Map classification status
  let classificationLabel = 'Likely Oil'
  if (classificationObj.classification === 'lookalike') {
    classificationLabel = 'Likely Look-alike'
  } else if (classificationObj.classification === 'oil') {
    classificationLabel = 'Likely Oil'
  } else if (detection.spill_detected === false) {
    classificationLabel = 'No Spill Detected'
  }

  const confidence = classificationObj.oil_probability ?? detection.confidence ?? 0.0
  const areaKm2 = detection.area_km2 ?? 0.0

  // Polygon coordinates array from GeoJSON mask polygon: [[[lon, lat], ...]]
  const maskPolyGeom = detection.mask_polygon
  const polygonCoordinates = maskPolyGeom?.coordinates?.[0] || null

  // Geodesic perimeter calculation
  const perimeterKm = polygonCoordinates ? calculatePolygonPerimeterKm(polygonCoordinates) : null

  // Elongation calculation from bounding box if available
  let elongation = null
  if (detection.bounding_box) {
    const bbox = detection.bounding_box
    const dLat = Math.abs(bbox.max_lat - bbox.min_lat)
    const dLon = Math.abs(bbox.max_lon - bbox.min_lon)
    if (dLat > 0 && dLon > 0) {
      const ratio = Math.max(dLat, dLon) / Math.min(dLat, dLon)
      elongation = `${ratio.toFixed(1)}:1`
    }
  }

  const incident = {
    id: analysisId,
    location_name: `Lat ${lat.toFixed(2)}°, Lon ${lon.toFixed(2)}° (Live Analysis)`,
    latitude: lat,
    longitude: lon,
    detected_at: timestampUtc,
    classification: classificationLabel,
    confidence: confidence,
    status: 'Needs Verification',
    area_km2: areaKm2,
    polygon: polygonCoordinates,
    is_live_analysis: true,

    sar: {
      platform: `${detection.model || 'AttentionUNet'} (Live Pipeline)`,
      polarization: 'Single-channel grayscale (converted from input scene)',
      look_direction: 'Not available',
      dark_feature_score: Math.round(detection.confidence * 100) / 100,
      acquisition_note: data.summary || 'Live Sentinel-1 SAR scene analysis via FastAPI',
    },

    // Include actual evidence metrics returned by models; omit missing
    evidence: {
      sar: detection.confidence !== undefined ? Math.round(detection.confidence * 100) / 100 : null,
      morphology: classificationObj.oil_probability !== undefined ? Math.round(classificationObj.oil_probability * 100) / 100 : null,
      wind: weather.wind_speed_ms !== undefined ? 1.0 : null,
      current: null, // Not provided by backend
      temporal_change: null, // Single-scene analysis
    },

    provenance: {
      scene_id: analysisId,
      acquisition_time: timestampUtc,
      processing_version: 'bluetrace-backend-1.0.0',
      model_version: `${detection.model || 'AttentionUNet'} + ${classificationObj.model || 'YOLO11n'}`,
      data_source: 'Live FastAPI ML Pipeline',
    },

    morphology: {
      area_km2: areaKm2,
      perimeter_km: perimeterKm,
      elongation: elongation ?? 'Not available',
      shape_indicators: [
        `${detection.model || 'AttentionUNet'} Binary Segmentation Mask`,
        ...(classificationObj.model ? [`${classificationObj.model} Classifier Evaluation`] : []),
      ],
    },

    look_alikes: {
      low_wind_area: classificationObj.classification === 'lookalike'
        ? `${Math.round((classificationObj.lookalike_probability ?? 0.5) * 100)}% (Elevated)`
        : 'Low',
      biogenic_film: 'Not evaluated',
      internal_waves: 'Not evaluated',
      ship_wake: 'Not evaluated',
    },
  }

  // Map real backend weather fields (wind, waves, ocean currents, SST)
  const environmental = {
    incidentId: analysisId,
    wind_speed: weather.wind_speed_ms ?? weather.wind_speed ?? null,
    wind_direction: weather.wind_direction_deg ?? weather.wind_direction ?? null,
    wave_height_m: weather.wave_height_m ?? null,
    wave_direction_deg: weather.wave_direction_deg ?? null,
    current_speed: weather.ocean_current_velocity_ms ?? null,
    current_direction: weather.ocean_current_direction_deg ?? null,
    sea_surface_temperature_c: weather.sea_surface_temperature_c ?? null,
    source: weather.source || 'Open-Meteo Marine / GFS',
    timestamp: weather.timestamp || null,
  }

  // Map backend ranked vessels (Vessels of Interest)
  const rawVessels = attribution.ranked_vessels || []
  const vessels = rawVessels.map((v, idx) => {
    const vesselMmsi = String(v.mmsi || v.vessel_id || `VOI-${100 + idx}`)
    const score = v.candidate_priority_score ?? 0.5

    // Offset position for map rendering if exact coords not provided
    const vLat = v.latitude ?? (lat + (idx + 1) * 0.015)
    const vLon = v.longitude ?? (lon + (idx + 1) * 0.015)

    return {
      id: vesselMmsi,
      incidentId: analysisId,
      vessel_name: v.vessel_name || v.vessel_id || `Vessel of Interest ${vesselMmsi}`,
      mmsi: vesselMmsi,
      vessel_type: v.vessel_type || 'Vessel of Interest',
      vessel_of_interest_score: score,
      distance_km: v.distance_km ?? null,
      corridor_overlap: v.corridor_overlap ?? score,
      time_feasibility: v.time_feasibility ?? score,
      ais_gap_minutes: v.ais_gap_minutes ?? null,
      speed: v.speed ?? null,
      heading: v.heading ?? null,
      latitude: vLat,
      longitude: vLon,
      trajectory: v.trajectory || [
        [vLon + 0.02, vLat + 0.02],
        [vLon + 0.01, vLat + 0.01],
        [vLon, vLat],
      ],
      explanation: v.explanation || 'Candidate vessel spatiotemporal trajectory alignment',
    }
  })

  // GeoJSON Slick Extent Feature from backend GeoJSON mask polygon
  const slickExtent = maskPolyGeom
    ? {
        type: 'Feature',
        properties: {
          incident_id: analysisId,
          area_km2: areaKm2,
          confidence: confidence,
        },
        geometry: maskPolyGeom,
      }
    : null

  // Estimated Drift Corridor Feature derived from actual wind direction
  const driftCorridor = createDriftCorridorFeature(analysisId, lat, lon, weather.wind_direction_deg)

  return {
    incident,
    environmental,
    vessels,
    slickExtent,
    driftCorridor,
    summary: data.summary,
  }
}
