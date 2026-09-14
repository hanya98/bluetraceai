import { useState, useEffect } from 'react'
import {
  Activity,
  AlertCircle,
  Anchor,
  Compass,
  Database,
  Globe2,
  Info,
  Loader2,
  MapPin,
  Radar,
  RadioTower,
  Route,
  Search,
  ShieldAlert,
  Ship,
  Timer,
  Waves,
  Zap,
} from 'lucide-react'
import MapView from '../components/map/MapView'
import VesselIntelligence from '../components/vessels/VesselIntelligence'
import { marineRegions } from '../data/marineRegions'
import { useIncident } from '../hooks/useIncident'
import { useIncidents } from '../hooks/useIncidents'
import { useMapReferenceData } from '../hooks/useMapReferenceData'
import { api } from '../services/api'

function VesselWorkspace() {
  const { incidents, loading: incidentsLoading, error: incidentsError } = useIncidents()
  const [selectedId, setSelectedId] = useState(null)
  const [selectedVesselId, setSelectedVesselId] = useState(null)

  const [selectedRegionId, setSelectedRegionId] = useState('REGION-AS-N')
  const [geoContext, setGeoContext] = useState(marineRegions[0])
  const [vesselSearchQuery, setVesselSearchQuery] = useState('')
  const [vesselData, setVesselData] = useState(null)
  const [vesselLoading, setVesselLoading] = useState(false)

  const activeSelected = useIncident(selectedId)
  const { layers } = useMapReferenceData()

  useEffect(() => {
    if (!selectedId && incidents.length) {
      setSelectedId(incidents[0].id)
    }
  }, [incidents, selectedId])

  const lat = geoContext.center[1]
  const lon = geoContext.center[0]
  const radiusKm = geoContext.radiusKm

  useEffect(() => {
    let active = true
    setVesselLoading(true)
    api.getNearbyVessels(lat, lon, radiusKm)
      .then((res) => active && setVesselData(res))
      .catch(() => active && setVesselData(null))
      .finally(() => active && setVesselLoading(false))

    return () => {
      active = false
    }
  }, [geoContext.id, lat, lon, radiusKm])

  const selectIncident = (id) => {
    setSelectedId(id)
    setSelectedVesselId(null)
  }

  const handleRegionSelect = (id) => {
    const reg = marineRegions.find((r) => r.id === id)
    if (reg) {
      setSelectedRegionId(id)
      setGeoContext(reg)
    }
  }

  const handleMapClick = ({ lat: clickLat, lon: clickLon, bounds }) => {
    setSelectedRegionId(null)
    const minLon = bounds ? bounds[0][0] : clickLon - 1.5
    const minLat = bounds ? bounds[0][1] : clickLat - 1.5
    const maxLon = bounds ? bounds[1][0] : clickLon + 1.5
    const maxLat = bounds ? bounds[1][1] : clickLat + 1.5

    setGeoContext({
      id: `GEO-${clickLat.toFixed(2)}-${clickLon.toFixed(2)}`,
      name: `Custom Location (${clickLat.toFixed(2)}°N, ${clickLon.toFixed(2)}°E)`,
      zone: 'Global Maritime Workspace',
      center: [clickLon, clickLat],
      bounds: [[minLon, minLat], [maxLon, maxLat]],
      radiusKm: 150,
      satellitePass: 'Sentinel-1A/B',
      lastScene: 'Dynamic Query',
      vesselDensity: 'Queried AIS Corridor',
    })
  }

  if (incidentsLoading)
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-3 text-[#1d4b3b]">
        <Loader2 className="animate-spin" size={20} />
        <span className="text-sm font-medium">Loading Vessel & Port Intelligence Workspace…</span>
      </div>
    )

  if (incidentsError)
    return <p className="p-8 text-[#663520]">Unable to load workspace data.</p>

  const rawVessels = vesselData?.vessels || activeSelected.vessels || []
  const filteredVessels = rawVessels.filter((v) => {
    if (!vesselSearchQuery) return true
    const q = vesselSearchQuery.toLowerCase()
    return (
      (v.vessel_name && v.vessel_name.toLowerCase().includes(q)) ||
      (v.mmsi && String(v.mmsi).includes(q)) ||
      (v.vessel_type && v.vessel_type.toLowerCase().includes(q))
    )
  })

  return (
    <div className="space-y-4 text-[#4d3328]">
      {/* Top Banner */}
      <div className="rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">
                VESSEL & PORT INTELLIGENCE WORKSPACE
              </span>
              <span className="rounded bg-[#1a6b9a]/15 px-2 py-0.5 text-[9px] font-bold text-[#1a6b9a]">
                AIS TRACKING & ATTRIBUTION
              </span>
            </div>
            <h1 className="mt-1 font-serif text-2xl font-bold text-[#663520]">
              Maritime Vessel & Port Investigation
            </h1>
            <p className="mt-1 text-xs text-[#735247]">
              Monitor AIS vessel trajectories, investigate candidate Vessels of Interest, inspect loitering indicators and port visits near active maritime zones.
            </p>
          </div>

          {/* Search Bar */}
          <div className="flex items-center gap-2 rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2">
            <Search size={16} className="text-[#846255]" />
            <input
              type="text"
              placeholder="Search MMSI, Vessel Name, Type…"
              value={vesselSearchQuery}
              onChange={(e) => setVesselSearchQuery(e.target.value)}
              className="w-56 bg-transparent text-xs font-semibold focus:outline-none placeholder-[#a08070]"
            />
          </div>
        </div>
      </div>

      {/* Region Shortcuts Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto rounded-xl border border-[#1a3450] bg-[#071d2f] p-2 text-xs text-[#c8dcea]">
        <span className="shrink-0 text-[10px] font-bold tracking-[.15em] text-[#4db6e8] px-1 uppercase flex items-center gap-1">
          <Globe2 size={12} /> Select Maritime Zone:
        </span>
        {marineRegions.map((r) => {
          const isSelected = selectedRegionId === r.id
          return (
            <button
              type="button"
              key={r.id}
              onClick={() => handleRegionSelect(r.id)}
              className={`shrink-0 rounded-lg px-2.5 py-1 text-[11px] font-semibold transition ${
                isSelected
                  ? 'bg-[#1a6b9a] text-white shadow-sm'
                  : 'text-[#8ab8d4] hover:bg-[#122e47] hover:text-white'
              }`}
            >
              {r.name}
            </button>
          )
        })}
      </div>

      {/* Main Grid: Map + Vessel Intelligence */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-4 items-stretch">
        <div className="min-h-[600px] h-full rounded-2xl overflow-hidden shadow-sm border border-[#d6b9a7]">
          <MapView
            incidents={incidents}
            selectedIncident={activeSelected.incident}
            vessels={filteredVessels}
            selectedVesselId={selectedVesselId}
            slickExtent={activeSelected.slickExtent}
            driftCorridor={activeSelected.driftCorridor}
            referenceLayers={layers}
            onIncidentSelect={selectIncident}
            onVesselSelect={setSelectedVesselId}
            selectedRegionId={selectedRegionId}
            onRegionSelect={handleRegionSelect}
            onMapClick={handleMapClick}
          />
        </div>

        <VesselIntelligence
          vessels={filteredVessels}
          selectedVesselId={selectedVesselId}
          onSelect={setSelectedVesselId}
        />
      </div>

      {/* Port & Facilities Intelligence Section */}
      <section className="rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-[#f0ddd1] pb-3">
          <div>
            <p className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">PORT & ANCHORAGE INTELLIGENCE</p>
            <h3 className="font-serif text-xl text-[#663520]">Regional Port Proximity & Activity</h3>
          </div>
          <span className="rounded bg-[#071d2f] px-2.5 py-1 text-[10px] font-bold text-[#4db6e8]">
            AREA: {geoContext.name}
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-3 text-xs">
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-3 space-y-1">
            <div className="flex items-center gap-1.5 text-sm font-bold text-[#663520]">
              <Anchor size={16} className="text-[#1d4b3b]" /> Port Approaches
            </div>
            <p className="text-[11px] text-[#735247]">Active commercial port approaches monitored within radius.</p>
            <p className="pt-2 font-mono text-[10px] font-semibold text-[#1d4b3b]">STATUS: TRACKING ACTIVE</p>
          </div>

          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-3 space-y-1">
            <div className="flex items-center gap-1.5 text-sm font-bold text-[#663520]">
              <RadioTower size={16} className="text-[#1d4b3b]" /> Offsets & Anchorages
            </div>
            <p className="text-[11px] text-[#735247]">Monitored offshore oil terminal anchorages and STS transfer zones.</p>
            <p className="pt-2 font-mono text-[10px] font-semibold text-[#1d4b3b]">DATA FEED: CONNECTED</p>
          </div>

          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-3 space-y-1">
            <div className="flex items-center gap-1.5 text-sm font-bold text-[#663520]">
              <ShieldAlert size={16} className="text-[#1d4b3b]" /> AIS Anomaly Monitoring
            </div>
            <p className="text-[11px] text-[#735247]">Automated detection of AIS transmission gaps and speed anomalies.</p>
            <p className="pt-2 font-mono text-[10px] font-semibold text-[#1d4b3b]">ENGINE: MODEL 3 ACTIVE</p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default VesselWorkspace
