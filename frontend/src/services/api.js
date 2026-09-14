import axios from 'axios'
import { mockApi } from './mockApi'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const http = axios.create({
  baseURL,
})

/**
 * FastAPI returns validation errors (HTTP 422) as:
 *   { detail: [{ loc: [...], msg: "...", type: "..." }, ...] }
 * rather than a plain string. Left as-is, interpolating err.response.data.detail
 * into a template string prints "[object Object]" and hides the real problem.
 * This interceptor flattens it into a single readable string, in place, so
 * every caller of `api.*` can keep doing `err.response?.data?.detail` and get
 * something a user can actually read.
 */
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail
    if (Array.isArray(detail)) {
      error.response.data.detail = detail
        .map((d) => (d?.msg ? `${d.loc?.join('.') ?? 'field'}: ${d.msg}` : JSON.stringify(d)))
        .join('; ')
    }
    return Promise.reject(error)
  }
)

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
    if (searchRadiusKm !== undefined && searchRadiusKm !== null) {
      formData.append('search_radius_km', searchRadiusKm)
    }

    // IMPORTANT: do NOT set a Content-Type header here. FormData needs a
    // multipart boundary (e.g. "multipart/form-data; boundary=----XYZ")
    // that only the browser can generate. Setting the header manually to
    // just 'multipart/form-data' strips that boundary and the backend's
    // multipart parser silently fails to extract the file, usually
    // surfacing as a 422 on the `file` field. Let axios/the browser set
    // this header automatically instead.
    const response = await http.post('/analyze', formData)
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