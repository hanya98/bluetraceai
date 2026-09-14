import { useEffect, useState } from 'react'
import { api } from '../services/api'

export function useMapReferenceData() {
  const [state, setState] = useState({ layers: null, loading: true, error: null })
  useEffect(() => { let active = true; api.getMapReferenceLayers().then((layers) => active && setState({ layers, loading: false, error: null })).catch((error) => active && setState({ layers: null, loading: false, error })); return () => { active = false } }, [])
  return state
}
