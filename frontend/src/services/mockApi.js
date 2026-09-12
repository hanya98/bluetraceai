import { environmentalData } from '../data/environmental'
import { mapReferenceLayers, reverseDriftCorridors, slickExtents } from '../data/geojson'
import { incidents } from '../data/incidents'
import { vessels } from '../data/vessels'
const respond = (value) => Promise.resolve(structuredClone(value))
const reviewStorageKey = 'oilwatch:analyst-reviews'
const readReviews = () => { try { return JSON.parse(localStorage.getItem(reviewStorageKey) ?? '{}') } catch { return {} } }
const writeReview = (incidentId, review) => { const reviews = readReviews(); reviews[incidentId] = review; localStorage.setItem(reviewStorageKey, JSON.stringify(reviews)); return review }
export const mockApi = {
  getIncidents: () => respond(incidents),
  getIncidentById: (id) => respond(incidents.find((incident) => incident.id === id) ?? null),
  getVesselsForIncident: (id) => respond(vessels.filter((vessel) => vessel.incidentId === id)),
  getEnvironmentalData: (id) => respond(environmentalData.find((data) => data.incidentId === id) ?? null),
  getEvidenceForIncident: (id) => respond(incidents.find((incident) => incident.id === id)?.evidence ?? null),
  getProvenanceForIncident: (id) => respond(incidents.find((incident) => incident.id === id)?.provenance ?? null),
  getSlickExtent: (id) => respond(slickExtents.features.find((feature) => feature.properties.incident_id === id) ?? null),
  getReverseDriftCorridor: (id) => respond(reverseDriftCorridors.features.find((feature) => feature.properties.incident_id === id) ?? null),
  getReverseDriftCorridors: () => respond(reverseDriftCorridors),
  getMapReferenceLayers: () => respond(mapReferenceLayers),
  getAnalystReview: (id) => respond(readReviews()[id] ?? null),
  submitAnalystReview: (id, review) => respond(writeReview(id, { ...review, incident_id: id, reviewed_at: new Date().toISOString(), review_state: 'Analyst reviewed' })),
}
