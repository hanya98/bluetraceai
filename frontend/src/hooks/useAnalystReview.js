import { useEffect, useState } from 'react'
import { api } from '../services/api'

export function useAnalystReview(incidentId) {
  const [state, setState] = useState({ review: null, loading: Boolean(incidentId), saving: false, error: null })
  useEffect(() => { if (!incidentId) return; let active = true; api.getAnalystReview(incidentId).then((review) => active && setState({ review, loading: false, saving: false, error: null })).catch((error) => active && setState({ review: null, loading: false, saving: false, error })); return () => { active = false } }, [incidentId])
  const save = async (review) => { setState((current) => ({ ...current, saving: true, error: null })); try { const saved = await api.submitAnalystReview(incidentId, review); setState({ review: saved, loading: false, saving: false, error: null }); return saved } catch (error) { setState((current) => ({ ...current, saving: false, error })); throw error } }
  return { ...state, save }
}
