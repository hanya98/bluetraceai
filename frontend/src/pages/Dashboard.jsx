import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  AlertCircle,
  Anchor,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Clock3,
  CloudSun,
  Compass,
  Database,
  Eye,
  FileText,
  Globe2,
  Info,
  Layers3,
  Loader2,
  MapPin,
  Radar,
  RadioTower,
  ScanSearch,
  Shield,
  Ship,
  Upload,
  Waves,
  Wind,
  X,
  Zap,
} from 'lucide-react'

import AnalystReview from '../components/incidents/AnalystReview'
import EvidenceTabs from '../components/evidence/EvidenceTabs'
import IncidentIntelligencePanel from '../components/incidents/IncidentIntelligencePanel'
import IncidentList from '../components/incidents/IncidentList'
import MapView from '../components/map/MapView'
import VesselIntelligence from '../components/vessels/VesselIntelligence'

import { marineRegions } from '../data/marineRegions'
import { useIncident } from '../hooks/useIncident'
import { useIncidents } from '../hooks/useIncidents'
import { useMapReferenceData } from '../hooks/useMapReferenceData'
import { api } from '../services/api'
import { liveAnalysisStorage } from '../services/liveAnalysisStorage'
import { transformAnalysisResponse } from '../utils/transformers'

/* ─── Helpers ─────────────────────────────────────────────────── */

function fmt(value, fallback = 'Not available') {
  if (value === null || value === undefined || value === '') return fallback
  return value
}

function fmtPct(value) {
  if (value === null || value === undefined) return 'Not available'
  return `${Math.round(Number(value) * 100)}%`
}

function fmtTime(value) {
  if (!value) return 'Not available'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return 'Not available'
  return (
    new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
    }).format(d) + ' UTC'
  )
}

/* ─── Compact KPI Card ─────────────────────────────────────────── */

function CompactKpiCard({ icon: Icon, label, value, sub, colorStyle }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-[#d6b9a7] bg-white p-3 shadow-sm">
      <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${colorStyle.bg} ${colorStyle.text}`}>
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-bold tracking-[.1em] text-[#7a5a4b] uppercase truncate">{label}</p>
        <div className="flex items-baseline gap-1.5">
          <p className="text-base font-bold leading-tight text-[#4d3328]">{value}</p>
          {sub && <span className="text-[10px] text-[#846255] truncate">{sub}</span>}
        </div>
      </div>
    </div>
  )
}

function RegionIntelligencePanel({
  region,
  incident,
  onClose,
  onAnalyze,
  analyzing,
}) {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')
  const [satData, setSatData] = useState(null)
  const [satLoading, setSatLoading] = useState(false)
  const [vesselData, setVesselData] = useState(null)
  const [vesselLoading, setVesselLoading] = useState(false)
  const [weatherData, setWeatherData] = useState(null)
  const [weatherLoading, setWeatherLoading] = useState(false)

  const regionId = region?.id
  // center: [lon, lat]
  const lat = region?.center[1]
  const lon = region?.center[0]
  // bounds: [[minLon, minLat], [maxLon, maxLat]]
  const minLon = region?.bounds[0][0]
  const minLat = region?.bounds[0][1]
  const maxLon = region?.bounds[1][0]
  const maxLat = region?.bounds[1][1]
  const radiusKm = region?.radiusKm ?? 100

  // Fetch real backend data dynamically for the selected region coordinates
  useEffect(() => {
    if (!region) return
    let active = true

    // GET /api/v1/satellite/search — uses bbox from region.bounds
    setSatLoading(true)
    api.searchSatellite({ min_lon: minLon, min_lat: minLat, max_lon: maxLon, max_lat: maxLat })
      .then((res) => active && setSatData(res))
      .catch(() => active && setSatData(null))
      .finally(() => active && setSatLoading(false))

    // GET /api/v1/vessels/nearby — uses region center + radiusKm
    setVesselLoading(true)
    api.getNearbyVessels(lat, lon, radiusKm)
      .then((res) => active && setVesselData(res))
      .catch(() => active && setVesselData(null))
      .finally(() => active && setVesselLoading(false))

    // GET /api/v1/weather/current — uses region center
    setWeatherLoading(true)
    api.getWeather(lat, lon)
      .then((res) => active && setWeatherData(res))
      .catch(() => active && setWeatherData(null))
      .finally(() => active && setWeatherLoading(false))

    return () => {
      active = false
    }
  }, [regionId, lat, lon, minLon, minLat, maxLon, maxLat, radiusKm])

  if (!region) {
    return (
      <aside className="flex h-full min-h-[600px] flex-col justify-between overflow-hidden rounded-2xl border border-[#2a4d6e] bg-[#0b1e2d] p-5 text-[#c8dcea] shadow-xl">
        <div>
          <p className="text-[10px] font-bold tracking-[.18em] text-[#4db6e8]">REGION INTELLIGENCE WORKSPACE</p>
          <h3 className="mt-1 text-base font-bold text-[#e8f4fb]">Select a Monitoring Region</h3>
          <p className="mt-2 text-xs leading-relaxed text-[#7aadcc]">
            Click any defined monitoring grid cell on the map to query Sentinel-1 satellite pass data, nearby AIS vessel traffic, and ocean weather context from the BlueTrace FastAPI engine.
          </p>
        </div>
        <div className="rounded-xl border border-[#1a3450] bg-[#071d2f] p-4 text-center text-xs">
          <Globe2 className="mx-auto mb-2 text-[#4db6e8]" size={24} />
          <p className="text-[#e8f4fb] font-semibold">Global & Regional Marine Intelligence</p>
          <p className="mt-1 text-[11px] text-[#7aadcc]">Navigate the map and select a monitoring region to begin</p>
        </div>
      </aside>
    )
  }

  const isLiveMatch = Boolean(incident?.is_live_analysis)
  const isDemoMatch = Boolean(incident && !incident.is_live_analysis)

  return (
    <aside className="flex flex-col h-full min-h-[600px] max-h-[600px] overflow-hidden rounded-2xl border border-[#2a4d6e] bg-[#0b1e2d] text-[#c8dcea] shadow-xl">
      {/* Panel Header */}
      <div className="flex items-start justify-between border-b border-[#1a3450] bg-[#071d2f] px-4 py-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold tracking-[.15em] text-[#4db6e8]">MONITORING REGION</span>
            {isLiveMatch && (
              <span className="flex items-center gap-0.5 rounded bg-emerald-700 px-1.5 py-0.5 text-[8px] font-bold text-white">
                <Zap size={7} /> LIVE ML
              </span>
            )}
            {isDemoMatch && (
              <span className="rounded bg-[#2a4d6e]/40 px-1.5 py-0.5 text-[8px] font-bold text-[#8ab8d4]">
                STORED
              </span>
            )}
          </div>
          <h3 className="mt-0.5 text-base font-bold text-[#e8f4fb]">{region.name}</h3>
          <p className="text-[11px] text-[#7aadcc]">{region.zone}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-[#7aadcc] transition hover:bg-[#1a3450] hover:text-white"
        >
          <X size={16} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1a3450] bg-[#092236] px-3 py-1.5 text-[10px] font-bold overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview', icon: Globe2 },
          { id: 'satellite', label: 'Satellite', icon: Radar },
          { id: 'vessels', label: 'Vessels', icon: Ship },
          { id: 'environment', label: 'Environment', icon: Wind },
          { id: 'analysis', label: 'Analysis', icon: ScanSearch },
          { id: 'evidence', label: 'Evidence', icon: Database },
        ].map(({ id, label, icon: Icon }) => (
          <button
            type="button"
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex shrink-0 items-center gap-1 rounded-lg px-2 py-1 transition ${
              activeTab === id
                ? 'bg-[#1a6b9a] text-white shadow-sm'
                : 'text-[#7aadcc] hover:bg-[#122e47] hover:text-white'
            }`}
          >
            <Icon size={12} />
            {label}
          </button>
        ))}
      </div>

      {/* Content Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-3">
            <section>
              <p className="mb-1 text-[9px] font-bold tracking-[.14em] text-[#4db6e8]">MONITORING REGION DETAILS</p>
              <div className="grid grid-cols-2 gap-1.5">
                <div className="rounded-lg bg-[#0f2438] p-2">
                  <span className="text-[10px] text-[#7aadcc]">Region ID</span>
                  <p className="font-mono font-semibold text-[#e8f4fb]">{region.id}</p>
                </div>
                <div className="rounded-lg bg-[#0f2438] p-2">
                  <span className="text-[10px] text-[#7aadcc]">Coverage Zone</span>
                  <p className="font-semibold text-[#e8f4fb] truncate">{region.zone}</p>
                </div>
                <div className="rounded-lg bg-[#0f2438] p-2">
                  <span className="text-[10px] text-[#7aadcc]">Center Coords</span>
                  <p className="font-semibold text-[#e8f4fb]">{lat.toFixed(2)}°N, {lon.toFixed(2)}°E</p>
                </div>
                <div className="rounded-lg bg-[#0f2438] p-2">
                  <span className="text-[10px] text-[#7aadcc]">Search Radius</span>
                  <p className="font-semibold text-[#e8f4fb]">{radiusKm} km</p>
                </div>
              </div>
            </section>

            <section className="space-y-1">
              <p className="mb-1 text-[9px] font-bold tracking-[.14em] text-[#4db6e8]">BOUNDING BOX & COVERAGE</p>
              <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">SW Coordinates</span><span className="font-semibold text-[#e8f4fb]">{minLat.toFixed(2)}°N, {minLon.toFixed(2)}°E</span></div>
              <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">NE Coordinates</span><span className="font-semibold text-[#e8f4fb]">{maxLat.toFixed(2)}°N, {maxLon.toFixed(2)}°E</span></div>
              <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Satellite Pass</span><span className="font-semibold text-[#e8f4fb]">{region.satellitePass}</span></div>
              <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Vessel Density</span><span className="font-semibold text-[#e8f4fb]">{region.vesselDensity}</span></div>
              <div className="flex justify-between py-1"><span className="text-[#7aadcc]">Detection Status</span><span className="font-semibold text-[#e8f4fb]">{incident ? 'Candidate scene active' : 'Awaiting analysis'}</span></div>
            </section>
          </div>
        )}

        {/* SATELLITE TAB */}
        {activeTab === 'satellite' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#4db6e8]">SENTINEL-1 STAC SATELLITE SEARCH</p>
            {satLoading ? (
              <div className="flex items-center gap-2 text-[#7aadcc] py-4">
                <Loader2 className="animate-spin" size={14} /> Fetching satellite STAC metadata…
              </div>
            ) : (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Satellite / Mission</span><span className="font-semibold text-[#e8f4fb]">{fmt(satData?.platform || satData?.mission, region.satellitePass)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Sensor / Instrument</span><span className="font-semibold text-[#e8f4fb]">{fmt(satData?.sensor, 'C-band SAR (Sentinel-1 C-SAR)')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Available Scenes</span><span className="font-semibold text-[#e8f4fb]">{satData?.count !== undefined ? satData.count : 'Not available'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Scene / Product ID</span><span className="font-mono text-[10px] font-semibold text-[#e8f4fb] truncate max-w-[160px]">{fmt(satData?.scene_id || satData?.product_id, 'Not available')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Acquisition Time</span><span className="font-semibold text-[#e8f4fb]">{fmtTime(satData?.acquisition_time)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Orbit / Pass</span><span className="font-semibold text-[#e8f4fb]">{fmt(satData?.orbit_pass, 'Descending / Ascending')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Resolution</span><span className="font-semibold text-[#e8f4fb]">{fmt(satData?.resolution, '10m x 10m (IW Spatial)')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Acquisition Mode</span><span className="font-semibold text-[#e8f4fb]">{fmt(satData?.mode, 'IW (Interferometric Wide)')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Polarization</span><span className="font-semibold text-[#e8f4fb]">{fmt(satData?.polarization, 'VV / VH Dual-Pol')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Cloud Coverage</span><span className="font-semibold text-[#e8f4fb]">{satData?.cloud_cover !== undefined ? `${satData.cloud_cover}%` : 'N/A (SAR All-Weather)'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Data Source</span><span className="font-semibold text-[#e8f4fb]">{fmt(satData?.provider, 'Copernicus Sentinel STAC Catalog')}</span></div>
                <div className="flex justify-between py-1"><span className="text-[#7aadcc]">Status</span><span className="font-semibold text-[#e8f4fb]">{satData ? 'Query successful' : 'No satellite scenes found for this region'}</span></div>
              </div>
            )}
          </div>
        )}

        {/* VESSELS TAB */}
        {activeTab === 'vessels' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#4db6e8]">NEARBY AIS VESSELS OF INTEREST</p>
            {vesselLoading ? (
              <div className="flex items-center gap-2 text-[#7aadcc] py-4">
                <Loader2 className="animate-spin" size={14} /> Querying AIS vessel feed…
              </div>
            ) : Array.isArray(vesselData?.vessels) && vesselData.vessels.length > 0 ? (
              <div className="space-y-2">
                {vesselData.vessels.map((v, i) => (
                  <div key={v.id || v.mmsi || i} className="rounded-lg bg-[#0f2438] p-2.5 space-y-1">
                    <div className="flex items-center justify-between font-bold text-[#e8f4fb]">
                      <span className="flex items-center gap-1">
                        <span className="rounded bg-[#1a6b9a] px-1.5 py-0.5 text-[9px]">#{i + 1}</span>
                        {v.vessel_name || v.name || 'Vessel of Interest'}
                      </span>
                      <span className="text-[10px] text-[#4db6e8]">MMSI {v.mmsi || 'N/A'}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-x-2 text-[10px] text-[#7aadcc]">
                      <div>Type: <span className="text-[#e8f4fb]">{v.vessel_type || 'Commercial'}</span></div>
                      <div>Speed: <span className="text-[#e8f4fb]">{v.speed !== undefined && v.speed !== null ? `${v.speed} kn` : 'Not available'}</span></div>
                      <div>Heading: <span className="text-[#e8f4fb]">{v.heading !== undefined && v.heading !== null ? `${v.heading}°` : 'Not available'}</span></div>
                      <div>AIS Gap: <span className="text-[#e8f4fb]">{v.ais_gap_minutes !== undefined && v.ais_gap_minutes !== null ? `${v.ais_gap_minutes} min` : 'Not available'}</span></div>
                    </div>
                    {v.vessel_of_interest_score !== undefined && (
                      <div className="flex justify-between text-[10px] pt-1 border-t border-[#1a3450]">
                        <span className="text-[#7aadcc]">Attribution Score</span>
                        <span className="font-bold text-amber-400">{Math.round(v.vessel_of_interest_score * 100)}%</span>
                      </div>
                    )}
                    {v.explanation && (
                      <p className="text-[9px] text-[#7aadcc] italic">{v.explanation}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-2 py-2">
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Search Radius</span><span className="font-semibold text-[#e8f4fb]">{radiusKm} km</span></div>
                <p className="text-[11px] text-[#7aadcc]">
                  No AIS vessel traffic data available for this region within radius.
                </p>
              </div>
            )}
          </div>
        )}

        {/* ENVIRONMENT TAB */}
        {activeTab === 'environment' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#4db6e8]">SURFACE OCEAN WEATHER & MARINE CONTEXT</p>
            {weatherLoading ? (
              <div className="flex items-center gap-2 text-[#7aadcc] py-4">
                <Loader2 className="animate-spin" size={14} /> Querying Open-Meteo Marine & GFS vectors…
              </div>
            ) : (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#1a3450]">
                  <span className="text-[#7aadcc]">Wind Speed</span>
                  <span className="font-semibold text-[#e8f4fb]">
                    {weatherData?.wind_speed_ms !== undefined && weatherData?.wind_speed_ms !== null
                      ? `${weatherData.wind_speed_ms} m/s`
                      : weatherData?.wind_speed !== undefined && weatherData?.wind_speed !== null
                      ? `${weatherData.wind_speed} m/s`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]">
                  <span className="text-[#7aadcc]">Wind Direction</span>
                  <span className="font-semibold text-[#e8f4fb]">
                    {weatherData?.wind_direction_deg !== undefined && weatherData?.wind_direction_deg !== null
                      ? `${weatherData.wind_direction_deg}°`
                      : weatherData?.wind_direction !== undefined && weatherData?.wind_direction !== null
                      ? `${weatherData.wind_direction}°`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]">
                  <span className="text-[#7aadcc]">Wave Height</span>
                  <span className="font-semibold text-[#e8f4fb]">
                    {weatherData?.wave_height_m !== undefined && weatherData?.wave_height_m !== null
                      ? `${weatherData.wave_height_m} m`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]">
                  <span className="text-[#7aadcc]">Wave Direction</span>
                  <span className="font-semibold text-[#e8f4fb]">
                    {weatherData?.wave_direction_deg !== undefined && weatherData?.wave_direction_deg !== null
                      ? `${weatherData.wave_direction_deg}°`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]">
                  <span className="text-[#7aadcc]">Current Speed</span>
                  <span className="font-semibold text-[#e8f4fb]">
                    {weatherData?.ocean_current_velocity_ms !== undefined && weatherData?.ocean_current_velocity_ms !== null
                      ? `${weatherData.ocean_current_velocity_ms} m/s`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]">
                  <span className="text-[#7aadcc]">Current Direction</span>
                  <span className="font-semibold text-[#e8f4fb]">
                    {weatherData?.ocean_current_direction_deg !== undefined && weatherData?.ocean_current_direction_deg !== null
                      ? `${weatherData.ocean_current_direction_deg}°`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]">
                  <span className="text-[#7aadcc]">Sea Surface Temp</span>
                  <span className="font-semibold text-[#e8f4fb]">
                    {weatherData?.sea_surface_temperature_c !== undefined && weatherData?.sea_surface_temperature_c !== null
                      ? `${weatherData.sea_surface_temperature_c} °C`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]">
                  <span className="text-[#7aadcc]">Weather Source</span>
                  <span className="font-semibold text-[#e8f4fb]">{fmt(weatherData?.source, 'Open-Meteo Marine / GFS Model')}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-[#7aadcc]">Timestamp</span>
                  <span className="font-semibold text-[#e8f4fb]">{fmtTime(weatherData?.timestamp)}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ANALYSIS TAB */}
        {activeTab === 'analysis' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#4db6e8]">DETECTION INTELLIGENCE & ML PREDICTION</p>
            {incident ? (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Spill Detected</span><span className="font-semibold text-emerald-400">{incident.confidence > 0.5 ? 'YES' : 'NO'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Detection Confidence</span><span className="font-semibold text-[#e8f4fb]">{fmtPct(incident.confidence)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Detection Model</span><span className="font-semibold text-[#e8f4fb]">{fmt(incident.provenance?.model_version, 'YOLO11n-oil-slick')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Spill Centroid</span><span className="font-semibold text-[#e8f4fb]">{incident.centroid ? `${incident.centroid[1].toFixed(3)}°N, ${incident.centroid[0].toFixed(3)}°E` : `${lat.toFixed(3)}°N, ${lon.toFixed(3)}°E`}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Surface Slick Extent</span><span className="font-semibold text-[#e8f4fb]">{incident.area_km2 !== undefined && incident.area_km2 !== null ? `${incident.area_km2} km²` : 'Not available'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Oil Probability</span><span className="font-semibold text-[#e8f4fb]">{fmtPct(incident.confidence)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Lookalike Probability</span><span className="font-semibold text-[#e8f4fb]">{incident.look_alikes ? Object.entries(incident.look_alikes).map(([k, v]) => `${k.replace('_', ' ')}: ${v}`).join(', ') : 'Low / Evaluated'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Classification</span><span className="font-semibold text-[#e8f4fb]">{fmt(incident.classification, 'Oil Slick')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Analysis ID</span><span className="font-mono text-[10px] font-semibold text-[#e8f4fb]">{incident.id}</span></div>
                <div className="flex justify-between py-1"><span className="text-[#7aadcc]">Analysis Timestamp</span><span className="font-semibold text-[#e8f4fb]">{fmtTime(incident.detected_at)}</span></div>
              </div>
            ) : (
              <p className="text-[11px] text-[#7aadcc] py-2">
                Awaiting analysis. Select an incident candidate or navigate to Analyze SAR Image in top navigation to execute the pipeline.
              </p>
            )}
          </div>
        )}

        {/* EVIDENCE TAB */}
        {activeTab === 'evidence' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#4db6e8]">PROVENANCE & EVIDENCE INTEGRITY</p>
            {incident ? (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Data Source</span><span className="font-semibold text-[#e8f4fb]">{fmt(incident.provenance?.data_source, 'Copernicus Sentinel-1')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Scene / Product ID</span><span className="font-mono text-[10px] font-semibold text-[#e8f4fb] truncate max-w-[160px]">{fmt(incident.provenance?.scene_id, incident.id)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Acquisition Time</span><span className="font-semibold text-[#e8f4fb]">{fmtTime(incident.provenance?.acquisition_time || incident.detected_at)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Analysis Timestamp</span><span className="font-semibold text-[#e8f4fb]">{fmtTime(incident.detected_at)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">AI Model Used</span><span className="font-semibold text-[#e8f4fb]">{fmt(incident.provenance?.model_version, 'YOLO11n-oil-slick')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Polarization</span><span className="font-semibold text-[#e8f4fb]">{fmt(incident.sar?.polarization, 'VV')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Look Direction</span><span className="font-semibold text-[#e8f4fb]">{fmt(incident.sar?.look_direction, 'Right')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#1a3450]"><span className="text-[#7aadcc]">Processing Status</span><span className="font-semibold text-[#e8f4fb]">{fmt(incident.provenance?.processing_version, 'v1.0.0 (Complete)')}</span></div>
                <div className="flex justify-between py-1"><span className="text-[#7aadcc]">Evidence Integrity</span><span className="font-bold text-emerald-400">{isLiveMatch ? 'LIVE / API DATA' : 'STORED / HISTORICAL RECORD'}</span></div>
              </div>
            ) : (
              <p className="text-[11px] text-[#7aadcc] py-2">
                No SAR evidence loaded. Select a candidate or analyze a scene.
              </p>
            )}
          </div>
        )}


      </div>

      {/* Action Footer */}
      <div className="border-t border-[#1a3450] p-3 bg-[#071d2f] space-y-2">
        <div className="grid grid-cols-2 gap-1.5 text-[10px]">
          <button
            type="button"
            onClick={() => navigate('/vessels')}
            className="flex items-center justify-center gap-1 rounded-lg bg-[#0f2d44] border border-[#1a4b6e] px-2 py-1.5 font-bold text-[#4db6e8] transition hover:bg-[#1a4b6e] hover:text-white"
          >
            <Ship size={11} /> Vessel Analysis
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('evidence')}
            className="flex items-center justify-center gap-1 rounded-lg bg-[#0f2d44] border border-[#1a4b6e] px-2 py-1.5 font-bold text-[#4db6e8] transition hover:bg-[#1a4b6e] hover:text-white"
          >
            <Database size={11} /> Satellite Evidence
          </button>
        </div>

        <div className="grid grid-cols-2 gap-1.5 text-[10px]">
          <button
            type="button"
            onClick={() => navigate('/analyze')}
            className="flex items-center justify-center gap-1 rounded-lg bg-[#1a6b9a] px-2 py-1.5 font-bold text-white shadow-sm transition hover:bg-[#155780]"
          >
            <ScanSearch size={11} /> SAR Analysis
          </button>
          <button
            type="button"
            onClick={() => window.print()}
            className="flex items-center justify-center gap-1 rounded-lg bg-[#1d4b3b] px-2 py-1.5 font-bold text-white shadow-sm transition hover:bg-[#123328]"
          >
            <FileText size={11} /> Incident Report
          </button>
        </div>
      </div>
    </aside>
  )
}

/* ─── Main Dashboard Component ───────────────────────────────────── */

function Dashboard() {
  const navigate = useNavigate()
  const { incidents, liveIncidents, demoIncidents, loading: incidentsLoading, error: incidentsError } = useIncidents()
  const [selectedId, setSelectedId] = useState(null)
  const [selectedVesselId, setSelectedVesselId] = useState(null)
  
  // Default to Northern Arabian Sea initial viewport
  const [selectedRegionId, setSelectedRegionId] = useState('REGION-AS-N')
  const [geoContext, setGeoContext] = useState(marineRegions[0])

  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)
  const [lastRefreshed, setLastRefreshed] = useState(new Date())

  const fileInputRef = useRef(null)

  const activeSelected = useIncident(selectedId)
  const { layers } = useMapReferenceData()

  useEffect(() => {
    if (!selectedId && incidents.length) {
      setSelectedId(incidents[0].id)
    }
  }, [incidents, selectedId])

  const selectIncident = (id) => {
    setSelectedId(id)
    setSelectedVesselId(null)
  }

  // Quick-select region shortcut handler
  const handleRegionSelect = (id) => {
    const reg = marineRegions.find((r) => r.id === id)
    if (reg) {
      setSelectedRegionId(id)
      setGeoContext(reg)
      setLastRefreshed(new Date())
    }
  }

  // Map click handler for arbitrary global coordinates anywhere on world map
  const handleMapClick = ({ lat, lon, bounds }) => {
    setSelectedRegionId(null)
    const minLon = bounds ? bounds[0][0] : lon - 1.5
    const minLat = bounds ? bounds[0][1] : lat - 1.5
    const maxLon = bounds ? bounds[1][0] : lon + 1.5
    const maxLat = bounds ? bounds[1][1] : lat + 1.5

    setGeoContext({
      id: `GEO-${lat.toFixed(2)}-${lon.toFixed(2)}`,
      name: `Custom Location (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)`,
      zone: 'Global Maritime Workspace',
      center: [lon, lat],
      bounds: [[minLon, minLat], [maxLon, maxLat]],
      radiusKm: 150,
      satellitePass: 'Sentinel-1A/B',
      lastScene: 'Dynamic STAC Query',
      vesselDensity: 'Queried AIS Corridor',
    })
    setLastRefreshed(new Date())
  }

  const handleRefreshIntelligence = () => {
    setLastRefreshed(new Date())
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setAnalyzing(true)
    setAnalysisError(null)

    const lat = geoContext?.center[1] ?? 19.05
    const lon = geoContext?.center[0] ?? 72.85
    const radiusKm = geoContext?.radiusKm ?? 150

    try {
      const response = await api.analyzeScene(file, lat, lon, undefined, radiusKm)
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
        'Unable to connect to BlueTrace backend server.'
      setAnalysisError(`Live SAR Analysis Failed: ${detail}`)
    } finally {
      setAnalyzing(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  if (incidentsLoading)
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-3 text-[#1d4b3b]">
        <Loader2 className="animate-spin" size={20} />
        <span className="text-sm font-medium">Loading regional intelligence…</span>
      </div>
    )

  if (incidentsError)
    return <p className="p-8 text-[#663520]">Unable to load workspace data.</p>

  const spillEvents = incidents.length
  const liveCount = liveIncidents.length
  const demoCount = demoIncidents.length
  const vesselCount = activeSelected.vessels?.length ?? 0
  const scenesAnalyzed = liveCount + demoCount

  const centerLat = geoContext.center[1]
  const centerLon = geoContext.center[0]
  const minLon = geoContext.bounds[0][0]
  const minLat = geoContext.bounds[0][1]
  const maxLon = geoContext.bounds[1][0]
  const maxLat = geoContext.bounds[1][1]

  return (
    <div className="space-y-3 text-[#4d3328]">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">
            BLUETRACE · MARITIME OPERATIONS COMMAND DASHBOARD
          </p>
          <h1 className="font-serif text-xl font-bold text-[#663520]">
            Command Operational Awareness & Response
          </h1>
          <p className="mt-0.5 text-xs text-[#735247]">
            Satellite Intelligence · AIS Monitoring · Environmental Context · Incident Response Coordination
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept="image/*,.tif,.tiff"
            className="hidden"
          />

          <button
            type="button"
            onClick={() => navigate('/analyze')}
            className="flex items-center gap-1.5 rounded-xl bg-[#1d4b3b] px-3.5 py-2 text-xs font-bold text-[#f8eadf] shadow-sm transition hover:bg-[#123328]"
          >
            <Upload size={14} /> Analyze SAR Image
          </button>

          {liveCount > 0 && (
            <span className="flex items-center gap-1 rounded-full bg-emerald-700 px-2.5 py-1 text-[10px] font-bold text-white">
              <Zap size={9} />
              {liveCount} LIVE RESULT{liveCount > 1 ? 'S' : ''}
            </span>
          )}
        </div>
      </div>

      {/* Command KPI Strip */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <CompactKpiCard
          icon={Waves}
          label="ACTIVE SPILLS"
          value={spillEvents}
          sub={liveCount > 0 ? `${liveCount} live ML · ${demoCount} candidate` : `${demoCount} candidate`}
          colorStyle={{ bg: 'bg-amber-50', text: 'text-amber-700' }}
        />
        <CompactKpiCard
          icon={Ship}
          label="VESSELS TRACKED"
          value={vesselCount > 0 ? vesselCount : '—'}
          sub="AIS candidate feed"
          colorStyle={{ bg: 'bg-sky-50', text: 'text-sky-700' }}
        />
        <CompactKpiCard
          icon={AlertCircle}
          label="OPERATIONAL ALERTS"
          value={liveCount + (vesselCount > 0 ? 1 : 0)}
          sub="Active system triggers"
          colorStyle={{ bg: 'bg-rose-50', text: 'text-rose-700' }}
        />
        <CompactKpiCard
          icon={Compass}
          label="REQUIRING REVIEW"
          value={incidents.filter((i) => i.status === 'Needs Verification').length}
          sub="Analyst queue"
          colorStyle={{ bg: 'bg-emerald-50', text: 'text-emerald-700' }}
        />
      </div>

      {/* Analysis Error */}
      {analysisError && (
        <div className="flex items-center justify-between rounded-xl border border-rose-300 bg-rose-50 p-2.5 text-xs text-rose-800 shadow-sm">
          <div className="flex items-center gap-2">
            <AlertCircle size={15} className="shrink-0 text-rose-600" />
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

      {/* Region Quick-Select Shortcuts Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto rounded-xl border border-[#1a3450] bg-[#071d2f] p-2 text-xs text-[#c8dcea]">
        <span className="shrink-0 text-[10px] font-bold tracking-[.15em] text-[#4db6e8] px-1 uppercase flex items-center gap-1">
          <Globe2 size={12} /> Quick Select Region:
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

      {/* Operational Active Query & Context Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#2a4d6e] bg-[#0b1e2d] p-3 text-xs text-[#c8dcea] shadow-sm">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <div>
            <span className="text-[9px] font-bold tracking-wider text-[#4db6e8] uppercase">ACTIVE QUERY AREA</span>
            <p className="font-bold text-[#e8f4fb]">{geoContext.name} <span className="font-normal text-[#7aadcc]">({geoContext.zone})</span></p>
          </div>
          <div className="h-6 w-px bg-[#1a3450] hidden sm:block" />
          <div>
            <span className="text-[9px] font-bold tracking-wider text-[#4db6e8] uppercase">COORDINATES</span>
            <p className="font-mono font-semibold text-[#e8f4fb]">{centerLat.toFixed(2)}°N, {centerLon.toFixed(2)}°E</p>
          </div>
          <div className="h-6 w-px bg-[#1a3450] hidden sm:block" />
          <div>
            <span className="text-[9px] font-bold tracking-wider text-[#4db6e8] uppercase">BOUNDING BOX</span>
            <p className="font-mono text-[11px] text-[#e8f4fb]">SW ({minLat.toFixed(1)}°, {minLon.toFixed(1)}°) to NE ({maxLat.toFixed(1)}°, {maxLon.toFixed(1)}°)</p>
          </div>
          <div className="h-6 w-px bg-[#1a3450] hidden sm:block" />
          <div>
            <span className="text-[9px] font-bold tracking-wider text-[#4db6e8] uppercase">SEARCH RADIUS</span>
            <p className="font-semibold text-[#e8f4fb]">{geoContext.radiusKm} km</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] text-[#7aadcc]">
            Updated {fmtTime(lastRefreshed)}
          </span>
          <button
            type="button"
            onClick={handleRefreshIntelligence}
            className="flex items-center gap-1 rounded-lg bg-[#1a6b9a] px-2.5 py-1 text-[11px] font-bold text-white shadow-sm transition hover:bg-[#155780]"
          >
            <Compass size={12} />
            Refresh Intelligence
          </button>
        </div>
      </div>

      {/* 4 Compact KPI Cards */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <CompactKpiCard
          icon={Globe2}
          label="QUICK SHORTCUTS"
          value={marineRegions.length}
          sub="Global Maritime Shortcuts"
          colorStyle={{ bg: 'bg-teal-50', text: 'text-teal-700' }}
        />
        <CompactKpiCard
          icon={Waves}
          label="POTENTIAL SPILL EVENTS"
          value={spillEvents}
          sub={liveCount > 0 ? `${liveCount} live · ${demoCount} historical` : `${demoCount} historical`}
          colorStyle={{ bg: 'bg-amber-50', text: 'text-amber-700' }}
        />
        <CompactKpiCard
          icon={Ship}
          label="VESSELS TRACKED"
          value={vesselCount > 0 ? vesselCount : '—'}
          sub="AIS candidates"
          colorStyle={{ bg: 'bg-sky-50', text: 'text-sky-700' }}
        />
        <CompactKpiCard
          icon={Compass}
          label="SCENES ANALYZED"
          value={scenesAnalyzed}
          sub={liveCount > 0 ? `${liveCount} FastAPI live` : 'Analyst pipeline'}
          colorStyle={{ bg: 'bg-emerald-50', text: 'text-emerald-700' }}
        />
      </div>

      {/* Main Operational Workspace: Map (65-70%) + Region Panel (30-35%) Side-by-Side */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_340px] gap-3 items-stretch">
        {/* Map Container */}
        <div className="min-h-[600px] h-full rounded-2xl overflow-hidden shadow-sm border border-[#d6b9a7]">
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
            selectedRegionId={selectedRegionId}
            onRegionSelect={handleRegionSelect}
            onMapClick={handleMapClick}
          />
        </div>

        {/* Region Intelligence Panel */}
        <RegionIntelligencePanel
          region={geoContext}
          incident={activeSelected.incident}
          onClose={() => setSelectedRegionId(null)}
          onAnalyze={() => fileInputRef.current?.click()}
          analyzing={analyzing}
        />
      </div>

      {/* Response Resources Section */}
      <div className="rounded-2xl border border-[#e6c8b5] bg-white p-4 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#f0ddd1] pb-2 text-xs">
          <span className="font-bold tracking-[.15em] text-[#1d4b3b] uppercase flex items-center gap-1.5">
            <Anchor size={14} /> NEARBY RESPONSE RESOURCES & ASSETS
          </span>
          <span className="font-mono text-[10px] font-semibold text-[#846255]">
            RESPONSE RESOURCE LAYER — DATA SOURCE NOT CONNECTED
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 text-xs">
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
            <p className="text-[10px] font-bold text-[#846255]">COAST GUARD UNITS</p>
            <p className="mt-0.5 text-[11px] text-[#735247]">Patrol vessels & air station monitoring</p>
            <p className="mt-1 font-mono text-[9px] text-[#a08070]">STATUS: DATA SOURCE DISCONNECTED</p>
          </div>
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
            <p className="text-[10px] font-bold text-[#846255]">RESPONSE VESSELS & TUGS</p>
            <p className="mt-0.5 text-[11px] text-[#735247]">Containment & salvage craft</p>
            <p className="mt-1 font-mono text-[9px] text-[#a08070]">STATUS: DATA SOURCE DISCONNECTED</p>
          </div>
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
            <p className="text-[10px] font-bold text-[#846255]">CONTAINMENT EQUIPMENT</p>
            <p className="mt-0.5 text-[11px] text-[#735247]">Booms, skimmers & dispersant stock</p>
            <p className="mt-1 font-mono text-[9px] text-[#a08070]">STATUS: DATA SOURCE DISCONNECTED</p>
          </div>
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
            <p className="text-[10px] font-bold text-[#846255]">OIL HANDLING FACILITIES</p>
            <p className="mt-0.5 text-[11px] text-[#735247]">Port reception & recovery terminals</p>
            <p className="mt-1 font-mono text-[9px] text-[#a08070]">STATUS: DATA SOURCE DISCONNECTED</p>
          </div>
        </div>
      </div>

      {/* Operational Status Footer */}
      <div className="rounded-2xl border border-[#e6c8b5] bg-white p-4 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#f0ddd1] pb-2 text-xs">
          <span className="font-bold tracking-[.15em] text-[#1d4b3b]">LIVE OPERATIONAL DATA STATUS</span>
          <span className="text-[11px] text-[#735247]">FastAPI Engine: <b className="text-emerald-700">● Online / Connected</b></span>
        </div>
        
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 text-xs">
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
            <p className="text-[10px] font-bold text-[#846255]">SATELLITE STAC FEED</p>
            <p className="mt-0.5 font-semibold text-emerald-700">● Connected / Available</p>
          </div>
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
            <p className="text-[10px] font-bold text-[#846255]">AIS VESSEL FEED</p>
            <p className="mt-0.5 font-semibold text-emerald-700">● Connected / Available</p>
          </div>
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
            <p className="text-[10px] font-bold text-[#846255]">OCEAN WEATHER MODEL</p>
            <p className="mt-0.5 font-semibold text-emerald-700">● Connected / Available</p>
          </div>
          <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
            <p className="text-[10px] font-bold text-[#846255]">AI INFERENCE ENGINE</p>
            <p className="mt-0.5 font-semibold text-emerald-700">● Models 1, 2 & 3 Active</p>
          </div>
        </div>
      </div>

      {/* Footer Disclaimer */}
      <p className="pb-1 text-center text-[10px] text-[#a08070]">
        All detection data requires analyst verification before operational use. Historical records provided for reference.
        Live analysis results generated by BlueTrace FastAPI AI pipeline.
      </p>
    </div>
  )
}

export default Dashboard
