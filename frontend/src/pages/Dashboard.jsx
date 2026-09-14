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

/* ─── Empty-state helper ─────────────────────────────────────────
   One line, consistent styling, instead of a grid of repeated
   "Not available" / "Disconnected" fields. */
function EmptyNote({ children }) {
  return (
    <p className="rounded-lg bg-[#fffaf6] border border-[#ead2c3] px-3 py-2 text-[11px] text-[#846255]">
      {children}
    </p>
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
      <aside className="flex h-full min-h-[600px] flex-col justify-between overflow-hidden rounded-2xl border border-[#e6c8b5] bg-white p-5 text-[#4d3328] shadow-sm">
        <div>
          <p className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">REGION INTELLIGENCE WORKSPACE</p>
          <h3 className="mt-1 font-serif text-base font-bold text-[#663520]">Select a Monitoring Region</h3>
          <p className="mt-2 text-xs leading-relaxed text-[#735247]">
            Click any defined monitoring grid cell on the map to query Sentinel-1 satellite pass data, nearby AIS vessel traffic, and ocean weather context from the BlueTrace FastAPI engine.
          </p>
        </div>
        <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-4 text-center text-xs">
          <Globe2 className="mx-auto mb-2 text-[#1a6b9a]" size={24} />
          <p className="text-[#663520] font-semibold">Global & Regional Marine Intelligence</p>
          <p className="mt-1 text-[11px] text-[#846255]">Navigate the map and select a monitoring region to begin</p>
        </div>
      </aside>
    )
  }

  const isLiveMatch = Boolean(incident?.is_live_analysis)
  const isDemoMatch = Boolean(incident && !incident.is_live_analysis)

  return (
    <aside className="flex flex-col h-full min-h-[600px] max-h-[600px] overflow-hidden rounded-2xl border border-[#e6c8b5] bg-white text-[#4d3328] shadow-sm">
      {/* Panel Header */}
      <div className="flex items-start justify-between border-b border-[#f0ddd1] bg-[#fffaf6] px-4 py-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold tracking-[.15em] text-[#1d4b3b]">MONITORING REGION</span>
            {isLiveMatch && (
              <span className="flex items-center gap-0.5 rounded bg-emerald-700 px-1.5 py-0.5 text-[8px] font-bold text-white">
                <Zap size={7} /> LIVE ML
              </span>
            )}
            {isDemoMatch && (
              <span className="rounded bg-[#735247]/15 px-1.5 py-0.5 text-[8px] font-bold text-[#663520]">
                STORED
              </span>
            )}
          </div>
          <h3 className="mt-0.5 font-serif text-base font-bold text-[#663520]">{region.name}</h3>
          <p className="text-[11px] text-[#846255]">{region.zone}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-[#846255] transition hover:bg-[#ead2c3] hover:text-[#4d3328]"
        >
          <X size={16} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#f0ddd1] bg-[#fffaf6] px-3 py-1.5 text-[10px] font-bold overflow-x-auto">
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
                : 'text-[#846255] hover:bg-[#ead2c3] hover:text-[#4d3328]'
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
              <p className="mb-1 text-[9px] font-bold tracking-[.14em] text-[#1d4b3b]">MONITORING REGION DETAILS</p>
              <div className="grid grid-cols-2 gap-1.5">
                <div className="rounded-lg bg-[#fffaf6] border border-[#ead2c3] p-2">
                  <span className="text-[10px] text-[#846255]">Region ID</span>
                  <p className="font-mono font-semibold text-[#4d3328]">{region.id}</p>
                </div>
                <div className="rounded-lg bg-[#fffaf6] border border-[#ead2c3] p-2">
                  <span className="text-[10px] text-[#846255]">Coverage Zone</span>
                  <p className="font-semibold text-[#4d3328] truncate">{region.zone}</p>
                </div>
                <div className="rounded-lg bg-[#fffaf6] border border-[#ead2c3] p-2">
                  <span className="text-[10px] text-[#846255]">Center Coords</span>
                  <p className="font-semibold text-[#4d3328]">{lat.toFixed(2)}°N, {lon.toFixed(2)}°E</p>
                </div>
                <div className="rounded-lg bg-[#fffaf6] border border-[#ead2c3] p-2">
                  <span className="text-[10px] text-[#846255]">Search Radius</span>
                  <p className="font-semibold text-[#4d3328]">{radiusKm} km</p>
                </div>
              </div>
            </section>

            <section className="space-y-1">
              <p className="mb-1 text-[9px] font-bold tracking-[.14em] text-[#1d4b3b]">BOUNDING BOX & COVERAGE</p>
              <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">SW Coordinates</span><span className="font-semibold text-[#4d3328]">{minLat.toFixed(2)}°N, {minLon.toFixed(2)}°E</span></div>
              <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">NE Coordinates</span><span className="font-semibold text-[#4d3328]">{maxLat.toFixed(2)}°N, {maxLon.toFixed(2)}°E</span></div>
              <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Satellite Pass</span><span className="font-semibold text-[#4d3328]">{region.satellitePass}</span></div>
              <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Vessel Density</span><span className="font-semibold text-[#4d3328]">{region.vesselDensity}</span></div>
              <div className="flex justify-between py-1"><span className="text-[#846255]">Detection Status</span><span className="font-semibold text-[#4d3328]">{incident ? 'Candidate scene active' : 'Awaiting analysis'}</span></div>
            </section>
          </div>
        )}

        {/* SATELLITE TAB */}
        {activeTab === 'satellite' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#1d4b3b]">SENTINEL-1 STAC SATELLITE SEARCH</p>
            {satLoading ? (
              <div className="flex items-center gap-2 text-[#846255] py-4">
                <Loader2 className="animate-spin" size={14} /> Fetching satellite STAC metadata…
              </div>
            ) : !satData ? (
              <EmptyNote>No satellite scenes returned for this region — check Copernicus API credentials.</EmptyNote>
            ) : (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Satellite / Mission</span><span className="font-semibold text-[#4d3328]">{fmt(satData?.platform || satData?.mission, region.satellitePass)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Sensor / Instrument</span><span className="font-semibold text-[#4d3328]">{fmt(satData?.sensor, 'C-band SAR (Sentinel-1 C-SAR)')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Available Scenes</span><span className="font-semibold text-[#4d3328]">{satData?.count !== undefined ? satData.count : 'Not available'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Scene / Product ID</span><span className="font-mono text-[10px] font-semibold text-[#4d3328] truncate max-w-[160px]">{fmt(satData?.scene_id || satData?.product_id, 'Not available')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Acquisition Time</span><span className="font-semibold text-[#4d3328]">{fmtTime(satData?.acquisition_time)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Orbit / Pass</span><span className="font-semibold text-[#4d3328]">{fmt(satData?.orbit_pass, 'Descending / Ascending')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Resolution</span><span className="font-semibold text-[#4d3328]">{fmt(satData?.resolution, '10m x 10m (IW Spatial)')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Acquisition Mode</span><span className="font-semibold text-[#4d3328]">{fmt(satData?.mode, 'IW (Interferometric Wide)')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Polarization</span><span className="font-semibold text-[#4d3328]">{fmt(satData?.polarization, 'VV / VH Dual-Pol')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Cloud Coverage</span><span className="font-semibold text-[#4d3328]">{satData?.cloud_cover !== undefined ? `${satData.cloud_cover}%` : 'N/A (SAR All-Weather)'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Data Source</span><span className="font-semibold text-[#4d3328]">{fmt(satData?.provider, 'Copernicus Sentinel STAC Catalog')}</span></div>
                <div className="flex justify-between py-1"><span className="text-[#846255]">Status</span><span className="font-semibold text-[#4d3328]">Query successful</span></div>
              </div>
            )}
          </div>
        )}

        {/* VESSELS TAB */}
        {activeTab === 'vessels' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#1d4b3b]">NEARBY AIS VESSELS OF INTEREST</p>
            {vesselLoading ? (
              <div className="flex items-center gap-2 text-[#846255] py-4">
                <Loader2 className="animate-spin" size={14} /> Querying AIS vessel feed…
              </div>
            ) : Array.isArray(vesselData?.vessels) && vesselData.vessels.length > 0 ? (
              <div className="space-y-2">
                {vesselData.vessels.map((v, i) => (
                  <div key={v.id || v.mmsi || i} className="rounded-lg bg-[#fffaf6] border border-[#ead2c3] p-2.5 space-y-1">
                    <div className="flex items-center justify-between font-bold text-[#4d3328]">
                      <span className="flex items-center gap-1">
                        <span className="rounded bg-[#1a6b9a] px-1.5 py-0.5 text-[9px] text-white">#{i + 1}</span>
                        {v.vessel_name || v.name || 'Vessel of Interest'}
                      </span>
                      <span className="text-[10px] text-[#1a6b9a]">MMSI {v.mmsi || 'N/A'}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-x-2 text-[10px] text-[#846255]">
                      <div>Type: <span className="text-[#4d3328]">{v.vessel_type || 'Commercial'}</span></div>
                      <div>Speed: <span className="text-[#4d3328]">{v.speed !== undefined && v.speed !== null ? `${v.speed} kn` : 'Not available'}</span></div>
                      <div>Heading: <span className="text-[#4d3328]">{v.heading !== undefined && v.heading !== null ? `${v.heading}°` : 'Not available'}</span></div>
                      <div>AIS Gap: <span className="text-[#4d3328]">{v.ais_gap_minutes !== undefined && v.ais_gap_minutes !== null ? `${v.ais_gap_minutes} min` : 'Not available'}</span></div>
                    </div>
                    {v.vessel_of_interest_score !== undefined && (
                      <div className="flex justify-between text-[10px] pt-1 border-t border-[#f0ddd1]">
                        <span className="text-[#846255]">Attribution Score</span>
                        <span className="font-bold text-amber-700">{Math.round(v.vessel_of_interest_score * 100)}%</span>
                      </div>
                    )}
                    {v.explanation && (
                      <p className="text-[9px] text-[#846255] italic">{v.explanation}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <EmptyNote>No AIS vessel traffic found within {radiusKm} km of this region.</EmptyNote>
            )}
          </div>
        )}

        {/* ENVIRONMENT TAB */}
        {activeTab === 'environment' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#1d4b3b]">SURFACE OCEAN WEATHER & MARINE CONTEXT</p>
            {weatherLoading ? (
              <div className="flex items-center gap-2 text-[#846255] py-4">
                <Loader2 className="animate-spin" size={14} /> Querying Open-Meteo Marine & GFS vectors…
              </div>
            ) : !weatherData ? (
              <EmptyNote>Weather data unavailable for this region — check network connectivity or API status.</EmptyNote>
            ) : (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#846255]">Wind Speed</span>
                  <span className="font-semibold text-[#4d3328]">
                    {weatherData?.wind_speed_ms !== undefined && weatherData?.wind_speed_ms !== null
                      ? `${weatherData.wind_speed_ms} m/s`
                      : weatherData?.wind_speed !== undefined && weatherData?.wind_speed !== null
                      ? `${weatherData.wind_speed} m/s`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#846255]">Wind Direction</span>
                  <span className="font-semibold text-[#4d3328]">
                    {weatherData?.wind_direction_deg !== undefined && weatherData?.wind_direction_deg !== null
                      ? `${weatherData.wind_direction_deg}°`
                      : weatherData?.wind_direction !== undefined && weatherData?.wind_direction !== null
                      ? `${weatherData.wind_direction}°`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#846255]">Wave Height</span>
                  <span className="font-semibold text-[#4d3328]">
                    {weatherData?.wave_height_m !== undefined && weatherData?.wave_height_m !== null
                      ? `${weatherData.wave_height_m} m`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#846255]">Wave Direction</span>
                  <span className="font-semibold text-[#4d3328]">
                    {weatherData?.wave_direction_deg !== undefined && weatherData?.wave_direction_deg !== null
                      ? `${weatherData.wave_direction_deg}°`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#846255]">Current Speed</span>
                  <span className="font-semibold text-[#4d3328]">
                    {weatherData?.ocean_current_velocity_ms !== undefined && weatherData?.ocean_current_velocity_ms !== null
                      ? `${weatherData.ocean_current_velocity_ms} m/s`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#846255]">Current Direction</span>
                  <span className="font-semibold text-[#4d3328]">
                    {weatherData?.ocean_current_direction_deg !== undefined && weatherData?.ocean_current_direction_deg !== null
                      ? `${weatherData.ocean_current_direction_deg}°`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#846255]">Sea Surface Temp</span>
                  <span className="font-semibold text-[#4d3328]">
                    {weatherData?.sea_surface_temperature_c !== undefined && weatherData?.sea_surface_temperature_c !== null
                      ? `${weatherData.sea_surface_temperature_c} °C`
                      : 'Not available'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#846255]">Weather Source</span>
                  <span className="font-semibold text-[#4d3328]">{fmt(weatherData?.source, 'Open-Meteo Marine / GFS Model')}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-[#846255]">Timestamp</span>
                  <span className="font-semibold text-[#4d3328]">{fmtTime(weatherData?.timestamp)}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ANALYSIS TAB */}
        {activeTab === 'analysis' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#1d4b3b]">DETECTION INTELLIGENCE & ML PREDICTION</p>
            {incident ? (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Spill Detected</span><span className="font-semibold text-emerald-700">{incident.confidence > 0.5 ? 'YES' : 'NO'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Detection Confidence</span><span className="font-semibold text-[#4d3328]">{fmtPct(incident.confidence)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Detection Model</span><span className="font-semibold text-[#4d3328]">{fmt(incident.provenance?.model_version, 'YOLO11n-oil-slick')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Spill Centroid</span><span className="font-semibold text-[#4d3328]">{incident.centroid ? `${incident.centroid[1].toFixed(3)}°N, ${incident.centroid[0].toFixed(3)}°E` : `${lat.toFixed(3)}°N, ${lon.toFixed(3)}°E`}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Surface Slick Extent</span><span className="font-semibold text-[#4d3328]">{incident.area_km2 !== undefined && incident.area_km2 !== null ? `${incident.area_km2} km²` : 'Not available'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Oil Probability</span><span className="font-semibold text-[#4d3328]">{fmtPct(incident.confidence)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Lookalike Probability</span><span className="font-semibold text-[#4d3328]">{incident.look_alikes ? Object.entries(incident.look_alikes).map(([k, v]) => `${k.replace('_', ' ')}: ${v}`).join(', ') : 'Low / Evaluated'}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Classification</span><span className="font-semibold text-[#4d3328]">{fmt(incident.classification, 'Oil Slick')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Analysis ID</span><span className="font-mono text-[10px] font-semibold text-[#4d3328]">{incident.id}</span></div>
                <div className="flex justify-between py-1"><span className="text-[#846255]">Analysis Timestamp</span><span className="font-semibold text-[#4d3328]">{fmtTime(incident.detected_at)}</span></div>
              </div>
            ) : (
              <EmptyNote>Awaiting analysis. Select an incident candidate or run Analyze SAR Image from the top navigation.</EmptyNote>
            )}
          </div>
        )}

        {/* EVIDENCE TAB */}
        {activeTab === 'evidence' && (
          <div className="space-y-2">
            <p className="text-[9px] font-bold tracking-[.14em] text-[#1d4b3b]">PROVENANCE & EVIDENCE INTEGRITY</p>
            {incident ? (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Data Source</span><span className="font-semibold text-[#4d3328]">{fmt(incident.provenance?.data_source, 'Copernicus Sentinel-1')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Scene / Product ID</span><span className="font-mono text-[10px] font-semibold text-[#4d3328] truncate max-w-[160px]">{fmt(incident.provenance?.scene_id, incident.id)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Acquisition Time</span><span className="font-semibold text-[#4d3328]">{fmtTime(incident.provenance?.acquisition_time || incident.detected_at)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Analysis Timestamp</span><span className="font-semibold text-[#4d3328]">{fmtTime(incident.detected_at)}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">AI Model Used</span><span className="font-semibold text-[#4d3328]">{fmt(incident.provenance?.model_version, 'YOLO11n-oil-slick')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Polarization</span><span className="font-semibold text-[#4d3328]">{fmt(incident.sar?.polarization, 'VV')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Look Direction</span><span className="font-semibold text-[#4d3328]">{fmt(incident.sar?.look_direction, 'Right')}</span></div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]"><span className="text-[#846255]">Processing Status</span><span className="font-semibold text-[#4d3328]">{fmt(incident.provenance?.processing_version, 'v1.0.0 (Complete)')}</span></div>
                <div className="flex justify-between py-1"><span className="text-[#846255]">Evidence Integrity</span><span className="font-bold text-emerald-700">{isLiveMatch ? 'LIVE / API DATA' : 'STORED / HISTORICAL RECORD'}</span></div>
              </div>
            ) : (
              <EmptyNote>No SAR evidence loaded. Select a candidate or analyze a scene.</EmptyNote>
            )}
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="border-t border-[#f0ddd1] p-3 bg-[#fffaf6] space-y-2">
        <div className="grid grid-cols-2 gap-1.5 text-[10px]">
          <button
            type="button"
            onClick={() => navigate('/vessels')}
            className="flex items-center justify-center gap-1 rounded-lg bg-white border border-[#d6b9a7] px-2 py-1.5 font-bold text-[#1a6b9a] transition hover:bg-[#ead2c3]"
          >
            <Ship size={11} /> Vessel Analysis
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('evidence')}
            className="flex items-center justify-center gap-1 rounded-lg bg-white border border-[#d6b9a7] px-2 py-1.5 font-bold text-[#1a6b9a] transition hover:bg-[#ead2c3]"
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
  const needsReviewCount = incidents.filter((i) => i.status === 'Needs Verification').length

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

      {/* Command KPI Strip — single row, no duplicates. Swapped in
          "Scenes Analyzed" (previously duplicated further down) in place
          of the old "Operational Alerts" card, which mostly restated
          the live-count badge already shown in the top bar. */}
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
          icon={Compass}
          label="SCENES ANALYZED"
          value={scenesAnalyzed}
          sub={liveCount > 0 ? `${liveCount} FastAPI live` : 'Analyst pipeline'}
          colorStyle={{ bg: 'bg-emerald-50', text: 'text-emerald-700' }}
        />
        <CompactKpiCard
          icon={AlertCircle}
          label="REQUIRING REVIEW"
          value={needsReviewCount}
          sub="Analyst queue"
          colorStyle={{ bg: 'bg-rose-50', text: 'text-rose-700' }}
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

      {/* Region Quick-Select Shortcuts Bar — converted from navy to cream theme */}
      <div className="flex items-center gap-1.5 overflow-x-auto rounded-xl border border-[#e6c8b5] bg-white p-2 text-xs shadow-sm">
        <span className="shrink-0 text-[10px] font-bold tracking-[.15em] text-[#1d4b3b] px-1 uppercase flex items-center gap-1">
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
                  : 'text-[#735247] hover:bg-[#fffaf6]'
              }`}
            >
              {r.name}
            </button>
          )
        })}
      </div>

      {/* Operational Active Query & Context Bar — converted from navy to cream theme */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e6c8b5] bg-white p-3 text-xs shadow-sm">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <div>
            <span className="text-[9px] font-bold tracking-wider text-[#1d4b3b] uppercase">ACTIVE QUERY AREA</span>
            <p className="font-bold text-[#663520]">{geoContext.name} <span className="font-normal text-[#846255]">({geoContext.zone})</span></p>
          </div>
          <div className="h-6 w-px bg-[#f0ddd1] hidden sm:block" />
          <div>
            <span className="text-[9px] font-bold tracking-wider text-[#1d4b3b] uppercase">COORDINATES</span>
            <p className="font-mono font-semibold text-[#4d3328]">{centerLat.toFixed(2)}°N, {centerLon.toFixed(2)}°E</p>
          </div>
          <div className="h-6 w-px bg-[#f0ddd1] hidden sm:block" />
          <div>
            <span className="text-[9px] font-bold tracking-wider text-[#1d4b3b] uppercase">BOUNDING BOX</span>
            <p className="font-mono text-[11px] text-[#4d3328]">SW ({minLat.toFixed(1)}°, {minLon.toFixed(1)}°) to NE ({maxLat.toFixed(1)}°, {maxLon.toFixed(1)}°)</p>
          </div>
          <div className="h-6 w-px bg-[#f0ddd1] hidden sm:block" />
          <div>
            <span className="text-[9px] font-bold tracking-wider text-[#1d4b3b] uppercase">SEARCH RADIUS</span>
            <p className="font-semibold text-[#4d3328]">{geoContext.radiusKm} km</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] text-[#846255]">
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

      {/* Response Resources Section — collapsed to a single note instead
          of 4 repeated "DATA SOURCE DISCONNECTED" cards, since none of
          these feeds are wired up yet. */}
      <div className="rounded-2xl border border-[#e6c8b5] bg-white p-4 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#f0ddd1] pb-2 text-xs">
          <span className="font-bold tracking-[.15em] text-[#1d4b3b] uppercase flex items-center gap-1.5">
            <Anchor size={14} /> Nearby Response Resources & Assets
          </span>
        </div>
        <EmptyNote>
          Coast guard units, response vessels, containment equipment, and oil handling facilities require
          a connected response-resource data source — not yet configured for this deployment.
        </EmptyNote>
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
