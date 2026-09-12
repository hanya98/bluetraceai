import axios from 'axios'
import { mockApi } from './mockApi'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const http = axios.create({
  baseURL,
})

export const api = {
  // --- Live FastAPI BlueTrace Backend Endpoints ---

  /**
   * Primary ML Pipeline Orchestration Endpoint (POST /api/v1/analyze)
   * Sends SAR scene image file and optional geospatial parameters.
   */
  analyzeScene: async (file, lat = 19.05, lon = 72.85, spillId, searchRadiusKm = 50.0) => {
    const formData = new FormData()
    formData.append('file', file)
    if (lat !== undefined && lat !== null) formData.append('lat', lat)
    if (lon !== undefined && lon !== null) formData.append('lon', lon)
    if (spillId) formData.append('spill_id', spillId)
    if (searchRadiusKm) formData.append('search_radius_km', searchRadiusKm)

    const response = await http.post('/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Ocean Surface Weather Endpoint (GET /api/v1/weather/current)
   */
  getWeather: async (lat = 19.05, lon = 72.85) => {
    const response = await http.get('/weather/current', {
      params: { lat, lon },
    })
    return response.data
  },

  /**
   * Candidate AIS Vessels Endpoint (GET /api/v1/vessels/nearby)
   */
  getNearbyVessels: async (lat = 19.05, lon = 72.85, radiusKm = 50.0, lookbackHours = 12) => {
    const response = await http.get('/vessels/nearby', {
      params: {
        lat,
        lon,
        radius_km: radiusKm,
        lookback_hours: lookbackHours,
      },
    })
    return response.data
  },

  /**
   * Sentinel-1 STAC Search Endpoint (GET /api/v1/satellite/search)
   */
  searchSatellite: async (params = {}) => {
    const response = await http.get('/satellite/search', {
      params,
    })
    return response.data
  },

  /**
   * Backend Health & ML Model Status Endpoint (GET /api/v1/health)
   */
  checkHealth: async () => {
    const response = await http.get('/health')
    return response.data
  },

  // --- Synthetic Baseline / Fallback Delegates ---

  getIncidents: () => mockApi.getIncidents(),
  getIncidentById: (id) => mockApi.getIncidentById(id),
  getVesselsForIncident: (id) => mockApi.getVesselsForIncident(id),
  getEnvironmentalData: (id) => mockApi.getEnvironmentalData(id),
  getEvidenceForIncident: (id) => mockApi.getEvidenceForIncident(id),
  getProvenanceForIncident: (id) => mockApi.getProvenanceForIncident(id),
  getSlickExtent: (id) => mockApi.getSlickExtent(id),
  getReverseDriftCorridor: (id) => mockApi.getReverseDriftCorridor(id),
  getReverseDriftCorridors: () => mockApi.getReverseDriftCorridors(),
  getMapReferenceLayers: () => mockApi.getMapReferenceLayers(),
  getAnalystReview: (id) => mockApi.getAnalystReview(id),
  submitAnalystReview: (id, review) => mockApi.submitAnalystReview(id, review),
}
