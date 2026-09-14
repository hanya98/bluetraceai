const STORAGE_KEY = 'bluetrace:live-analyses'

export const liveAnalysisStorage = {
  getLiveAnalyses: () => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY)
      return raw ? JSON.parse(raw) : {}
    } catch (err) {
      console.error('Failed to read live analyses from sessionStorage:', err)
      return {}
    }
  },

  getLiveAnalysesList: () => {
    const map = liveAnalysisStorage.getLiveAnalyses()
    return Object.values(map)
  },

  getLiveAnalysisById: (id) => {
    if (!id) return null
    const map = liveAnalysisStorage.getLiveAnalyses()
    return map[id] || null
  },

  saveLiveAnalysis: (transformed) => {
    if (!transformed || !transformed.incident?.id) return
    try {
      const current = liveAnalysisStorage.getLiveAnalyses()
      current[transformed.incident.id] = transformed
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(current))
      window.dispatchEvent(new CustomEvent('live-analysis-updated', { detail: transformed }))
    } catch (err) {
      console.error('Failed to save live analysis to sessionStorage:', err)
    }
  },

  clearLiveAnalyses: () => {
    try {
      sessionStorage.removeItem(STORAGE_KEY)
      window.dispatchEvent(new CustomEvent('live-analysis-updated'))
    } catch (err) {
      console.error('Failed to clear live analyses from sessionStorage:', err)
    }
  },
}
