import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { liveAnalysisStorage } from '../services/liveAnalysisStorage'

export function useIncidents() {
  const [state, setState] = useState({
    incidents: [],
    liveIncidents: [],
    demoIncidents: [],
    loading: true,
    error: null,
  })

  useEffect(() => {
    let active = true

    const loadData = async () => {
      try {
        const demoIncidents = await api.getIncidents()
        const liveAnalyses = liveAnalysisStorage.getLiveAnalysesList()
        const liveIncidents = liveAnalyses.map((item) => item.incident).filter(Boolean)

        if (active) {
          setState({
            incidents: [...liveIncidents, ...demoIncidents],
            liveIncidents,
            demoIncidents,
            loading: false,
            error: null,
          })
        }
      } catch (error) {
        if (active) {
          setState((prev) => ({
            ...prev,
            loading: false,
            error,
          }))
        }
      }
    }

    loadData()

    const handleStorageUpdate = () => {
      loadData()
    }

    window.addEventListener('live-analysis-updated', handleStorageUpdate)

    return () => {
      active = false
      window.removeEventListener('live-analysis-updated', handleStorageUpdate)
    }
  }, [])

  return state
}
