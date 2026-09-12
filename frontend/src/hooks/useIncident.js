import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { liveAnalysisStorage } from '../services/liveAnalysisStorage'

export function useIncident(id) {
  const [state, setState] = useState({
    incident: null,
    vessels: [],
    environmental: null,
    evidence: null,
    provenance: null,
    slickExtent: null,
    driftCorridor: null,
    loading: Boolean(id),
    error: null,
  })

  useEffect(() => {
    if (!id) return

    let active = true

    const loadIncident = async () => {
      // Check session live analysis storage first
      const live = liveAnalysisStorage.getLiveAnalysisById(id)
      if (live) {
        if (active) {
          setState({
            incident: live.incident,
            vessels: live.vessels || [],
            environmental: live.environmental || null,
            evidence: live.incident.evidence || null,
            provenance: live.incident.provenance || null,
            slickExtent: live.slickExtent || null,
            driftCorridor: live.driftCorridor || null,
            loading: false,
            error: null,
          })
        }
        return
      }

      // Fallback to synthetic demo API / mockApi
      try {
        const [
          incident,
          vessels,
          environmental,
          evidence,
          provenance,
          slickExtent,
          driftCorridor,
        ] = await Promise.all([
          api.getIncidentById(id),
          api.getVesselsForIncident(id),
          api.getEnvironmentalData(id),
          api.getEvidenceForIncident(id),
          api.getProvenanceForIncident(id),
          api.getSlickExtent(id),
          api.getReverseDriftCorridor(id),
        ])

        if (active) {
          setState({
            incident,
            vessels,
            environmental,
            evidence,
            provenance,
            slickExtent,
            driftCorridor,
            loading: false,
            error: null,
          })
        }
      } catch (error) {
        if (active) {
          setState((current) => ({ ...current, loading: false, error }))
        }
      }
    }

    loadIncident()

    const handleStorageUpdate = () => {
      loadIncident()
    }

    window.addEventListener('live-analysis-updated', handleStorageUpdate)

    return () => {
      active = false
      window.removeEventListener('live-analysis-updated', handleStorageUpdate)
    }
  }, [id])

  return state
}
