import { useEffect, useRef, useState } from 'react'
import {
  Activity,
  AlertCircle,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Clock3,
  CloudSun,
  Compass,
  Database,
  Eye,
  Globe2,
  Info,
  Loader2,
  MapPin,
  Radar,
  ScanSearch,
  Shield,
  Ship,
  Upload,
  Waves,
  Zap,
} from 'lucide-react'

import AnalystReview from '../components/incidents/AnalystReview'
import EvidenceTabs from '../components/evidence/EvidenceTabs'
import IncidentIntelligencePanel from '../components/incidents/IncidentIntelligencePanel'
import IncidentList from '../components/incidents/IncidentList'
import MapView from '../components/map/MapView'
import VesselIntelligence from '../components/vessels/VesselIntelligence'
import AnalyticsOverview from './Analytics'

import { useIncident } from '../hooks/useIncident'
import { useIncidents } from '../hooks/useIncidents'
import { useMapReferenceData } from '../hooks/useMapReferenceData'
import { api } from '../services/api'
import { liveAnalysisStorage } from '../services/liveAnalysisStorage'
import { transformAnalysisResponse } from '../utils/transformers'

function SarWorkspace() {
  const { incidents, liveIncidents, demoIncidents, loading: incidentsLoading, error: incidentsError } = useIncidents()
  const [selectedId, setSelectedId] = useState(null)
  const [selectedVesselId, setSelectedVesselId] = useState(null)

  const [latInput, setLatInput] = useState('19.05')
  const [lonInput, setLonInput] = useState('72.85')
  const [radiusInput, setRadiusInput] = useState('50.0')
  const [spillIdInput, setSpillIdInput] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [filePreviewUrl, setFilePreviewUrl] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)

  const fileInputRef = useRef(null)
  const activeSelected = useIncident(selectedId)
  const { layers } = useMapReferenceData()

  // Auto select first incident if none selected
  useEffect(() => {
    if (!selectedId && incidents.length) {
      setSelectedId(incidents[0].id)
    }
  }, [incidents, selectedId])

  const selectIncident = (id) => {
    setSelectedId(id)
    setSelectedVesselId(null)
  }

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setSelectedFile(file)
    setAnalysisError(null)

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file)
      setFilePreviewUrl(url)
    } else {
      setFilePreviewUrl(null)
    }
  }

  const handleRunAnalysis = async () => {
    if (!selectedFile) {
      fileInputRef.current?.click()
      return
    }

    setAnalyzing(true)
    setAnalysisError(null)

    const lat = Number(latInput) || 19.05
    const lon = Number(lonInput) || 72.85
    const radius = Number(radiusInput) || 50.0
    const spillId = spillIdInput.trim() || undefined

    try {
      const response = await api.analyzeScene(selectedFile, lat, lon, spillId, radius)
      const transformed = transformAnalysisResponse(response, { lat, lon })

      if (transformed?.incident) {
        liveAnalysisStorage.saveLiveAnalysis(transformed)
        setSelectedId(transformed.incident.id)
        setSelectedVesselId(null)
      }
    } catch (err) {
      console.error('FastAPI SAR Analysis Error:', err)
      const detail =
        err.response?.data?.detail ||
        err.message ||
        'Unable to connect to BlueTrace backend server at http://localhost:8000/api/v1.'
      setAnalysisError(`Live SAR Analysis Failed: ${detail}`)
    } finally {
      setAnalyzing(false)
    }
  }

  if (incidentsLoading)
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-3 text-[#1d4b3b]">
        <Loader2 className="animate-spin" size={20} />
        <span className="text-sm font-medium">Loading SAR Intelligence Workspace…</span>
      </div>
    )

  if (incidentsError)
    return <p className="p-8 text-[#663520]">Unable to load demonstration workspace data.</p>

  return (
    <div className="space-y-5 text-[#4d3328]">
      {/* Header Banner */}
      <div className="rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">
                DEDICATED SAR ANALYSIS WORKSPACE
              </span>
              <span className="rounded bg-[#1a6b9a]/15 px-2 py-0.5 text-[9px] font-bold text-[#1a6b9a]">
                POST /api/v1/analyze
              </span>
            </div>
            <h1 className="mt-1 font-serif text-2xl font-bold text-[#663520]">
              Manual Sentinel-1 SAR Scene Analysis
            </h1>
            <p className="mt-1 text-xs text-[#735247]">
              Upload custom Sentinel-1 SAR imagery (PNG, JPG, TIFF) to execute the live BlueTrace FastAPI ML Pipeline for oil slick detection, look-alike classification, and AIS vessel attribution.
            </p>
          </div>

          {/* Upload & Form Box */}
          <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-3">
            {/* File Selection / Preview Thumbnail */}
            <div className="flex items-center gap-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept="image/*,.tif,.tiff"
                className="hidden"
              />

              {filePreviewUrl ? (
                <div className="relative h-10 w-10 overflow-hidden rounded-lg border border-[#1d4b3b]">
                  <img src={filePreviewUrl} alt="SAR Preview" className="h-full w-full object-cover" />
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-1.5 rounded-lg border border-dashed border-[#d6b9a7] bg-white px-2.5 py-1.5 text-xs text-[#735247] hover:border-[#1d4b3b]"
                >
                  <Upload size={13} />
                  {selectedFile ? selectedFile.name : 'Select File'}
                </button>
              )}
            </div>

            {/* Inputs */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <label className="flex items-center gap-1 text-[11px] text-[#735247]">
                Lat:
                <input
                  type="text"
                  value={latInput}
                  onChange={(e) => setLatInput(e.target.value)}
                  className="w-16 rounded border border-[#d6b9a7] bg-white px-1.5 py-1 text-xs font-mono"
                />
              </label>
              <label className="flex items-center gap-1 text-[11px] text-[#735247]">
                Lon:
                <input
                  type="text"
                  value={lonInput}
                  onChange={(e) => setLonInput(e.target.value)}
                  className="w-16 rounded border border-[#d6b9a7] bg-white px-1.5 py-1 text-xs font-mono"
                />
              </label>
              <label className="flex items-center gap-1 text-[11px] text-[#735247]">
                Radius:
                <input
                  type="text"
                  value={radiusInput}
                  onChange={(e) => setRadiusInput(e.target.value)}
                  placeholder="50"
                  className="w-12 rounded border border-[#d6b9a7] bg-white px-1 py-1 text-xs font-mono"
                />
                <span className="text-[10px]">km</span>
              </label>
              <label className="flex items-center gap-1 text-[11px] text-[#735247]">
                ID:
                <input
                  type="text"
                  value={spillIdInput}
                  onChange={(e) => setSpillIdInput(e.target.value)}
                  placeholder="Optional"
                  className="w-20 rounded border border-[#d6b9a7] bg-white px-1.5 py-1 text-xs font-mono"
                />
              </label>
            </div>

            <button
              type="button"
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="flex items-center gap-2 rounded-xl bg-[#1d4b3b] px-4 py-2 text-xs font-bold text-[#f8eadf] shadow-sm transition hover:bg-[#123328] disabled:opacity-50"
            >
              {analyzing ? <Loader2 className="animate-spin" size={15} /> : <ScanSearch size={15} />}
              {analyzing ? 'Processing ML Pipeline…' : selectedFile ? 'Run SAR Analysis' : 'Upload SAR Image & Analyze'}
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {analysisError && (
          <div className="mt-3 flex items-center justify-between rounded-xl border border-rose-300 bg-rose-50 p-3 text-xs text-rose-800">
            <div className="flex items-center gap-2">
              <AlertCircle size={16} className="shrink-0 text-rose-600" />
              <span>{analysisError}</span>
            </div>
            <button
              type="button"
              onClick={() => setAnalysisError(null)}
              className="font-bold text-rose-900 underline"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Main Grid: Interactive Map + Candidate Queue */}
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
        {/* Map */}
        <div className="min-h-[580px] rounded-2xl overflow-hidden shadow-sm border border-[#d6b9a7]">
          <MapView
            incidents={incidents}
            selectedIncident={activeSelected.incident}
            vessels={activeSelected.vessels || []}
            selectedVesselId={selectedVesselId}
            slickExtent={activeSelected.slickExtent}
            driftCorridor={activeSelected.driftCorridor}
            referenceLayers={layers}
            onIncidentSelect={selectIncident}
            onVesselSelect={setSelectedVesselId}
          />
        </div>

        {/* Candidate Repository Queue */}
        <IncidentList
          incidents={incidents}
          selectedId={selectedId}
          onSelect={selectIncident}
        />
      </div>

      {/* Full Incident Workspace (AI Assessment, SAR Evidence, Vessels, Review) */}
      {activeSelected.incident && (
        <section className="space-y-4 rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#f0ddd1] pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">
                  ANALYSIS EVIDENCE WORKSPACE
                </span>
                {activeSelected.incident.is_live_analysis ? (
                  <span className="flex items-center gap-0.5 rounded bg-emerald-700 px-2 py-0.5 text-[9px] font-bold text-white">
                    <Zap size={9} /> LIVE ML ANALYSIS
                  </span>
                ) : (
                  <span className="rounded bg-[#735247]/15 px-2 py-0.5 text-[9px] font-bold text-[#663520]">
                    STORED RECORD
                  </span>
                )}
              </div>
              <h2 className="mt-1 font-serif text-xl text-[#663520]">
                Attribution & Multi-Signal Evidence · {activeSelected.incident.id}
              </h2>
            </div>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <IncidentIntelligencePanel
              incident={activeSelected.incident}
              evidence={activeSelected.evidence}
              environmental={activeSelected.environmental}
              provenance={activeSelected.provenance}
              selectedVesselId={selectedVesselId}
              vessels={activeSelected.vessels}
            />

            <VesselIntelligence
              vessels={activeSelected.vessels || []}
              selectedVesselId={selectedVesselId}
              onSelect={setSelectedVesselId}
            />
          </div>

          <EvidenceTabs
            incident={activeSelected.incident}
            evidence={activeSelected.evidence}
            environmental={activeSelected.environmental}
            provenance={activeSelected.provenance}
            vessels={activeSelected.vessels}
          />
        </section>
      )}

      {/* Embedded Operational Analytics Overview */}
      <section className="rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm space-y-4">
        <div className="border-b border-[#f0ddd1] pb-3">
          <p className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">DERIVED METRICS & INSIGHTS</p>
          <h3 className="font-serif text-xl text-[#663520]">Operational Candidate Activity Overview</h3>
        </div>
        <AnalyticsOverview />
      </section>
    </div>
  )
}

export default SarWorkspace
