import { useState, useEffect } from 'react'
import {
  AlertCircle,
  Compass,
  Droplets,
  Globe2,
  Info,
  Loader2,
  MapPin,
  ShieldCheck,
  Thermometer,
  Trees,
  Waves,
  Wind,
  Zap,
} from 'lucide-react'
import MapView from '../components/map/MapView'
import { marineRegions } from '../data/marineRegions'
import { useIncident } from '../hooks/useIncident'
import { useIncidents } from '../hooks/useIncidents'
import { useMapReferenceData } from '../hooks/useMapReferenceData'
import { api } from '../services/api'

function EnvironmentWorkspace() {
  const { incidents, loading: incidentsLoading, error: incidentsError } = useIncidents()
  const [selectedId, setSelectedId] = useState(null)
  const [selectedVesselId, setSelectedVesselId] = useState(null)

  const [selectedRegionId, setSelectedRegionId] = useState('REGION-AS-N')
  const [geoContext, setGeoContext] = useState(marineRegions[0])
  const [weatherData, setWeatherData] = useState(null)
  const [weatherLoading, setWeatherLoading] = useState(false)

  const activeSelected = useIncident(selectedId)
  const { layers } = useMapReferenceData()

  useEffect(() => {
    if (!selectedId && incidents.length) {
      setSelectedId(incidents[0].id)
    }
  }, [incidents, selectedId])

  const lat = geoContext.center[1]
  const lon = geoContext.center[0]

  useEffect(() => {
    let active = true
    setWeatherLoading(true)
    api.getWeather(lat, lon)
      .then((res) => active && setWeatherData(res))
      .catch(() => active && setWeatherData(null))
      .finally(() => active && setWeatherLoading(false))

    return () => {
      active = false
    }
  }, [geoContext.id, lat, lon])

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
        <span className="text-sm font-medium">Loading Environmental Response Workspace…</span>
      </div>
    )

  if (incidentsError)
    return <p className="p-8 text-[#663520]">Unable to load workspace data.</p>

  const incident = activeSelected.incident
  const env = activeSelected.environmental

  return (
    <div className="space-y-4 text-[#4d3328]">
      {/* Top Banner */}
      <div className="rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">
                ENVIRONMENTAL & REGIONAL RESPONSE WORKSPACE
              </span>
              <span className="rounded bg-teal-700/15 px-2 py-0.5 text-[9px] font-bold text-teal-800">
                MET-OCEAN & ECOSYSTEM IMPACT
              </span>
            </div>
            <h1 className="mt-1 font-serif text-2xl font-bold text-[#663520]">
              Environmental Impact & Coastal Sensitivity
            </h1>
            <p className="mt-1 text-xs text-[#735247]">
              Evaluate ocean weather conditions, surface slick extent, drift vectors, and marine ecosystem impact across active monitoring zones.
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-3 text-xs">
            <Wind size={18} className="text-[#1d4b3b]" />
            <div>
              <p className="text-[10px] font-bold text-[#846255]">ACTIVE MET-OCEAN MODEL</p>
              <p className="font-semibold text-[#4d3328]">{weatherData?.source || 'Open-Meteo Weather'}</p>
            </div>
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

      {/* Main Grid: Map + Environmental Panel */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_380px] gap-4 items-stretch">
        <div className="min-h-[600px] h-full rounded-2xl overflow-hidden shadow-sm border border-[#d6b9a7]">
          <MapView
            incidents={incidents}
            selectedIncident={incident}
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

        {/* Environmental Context Panel */}
        <aside className="rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm space-y-4 text-xs">
          <div>
            <p className="text-[10px] font-bold tracking-[.18em] text-[#1d4b3b]">ENVIRONMENTAL PARAMETERS</p>
            <h2 className="mt-0.5 font-serif text-xl text-[#663520]">{geoContext.name}</h2>
            <p className="text-[11px] text-[#735247]">{geoContext.zone}</p>
          </div>

          {/* Current Live Weather Vectors */}
          <section className="space-y-2 border-t border-[#f0ddd1] pt-3">
            <p className="text-[10px] font-bold tracking-[.14em] text-[#1d4b3b]">SURFACE OCEAN WEATHER</p>
            {weatherLoading ? (
              <div className="flex items-center gap-2 text-[#735247] py-2">
                <Loader2 className="animate-spin" size={14} /> Querying Open-Meteo model…
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
                  <span className="text-[10px] text-[#846255]">Wind Speed</span>
                  <p className="font-bold text-sm text-[#4d3328]">
                    {weatherData?.wind_speed_ms !== undefined && weatherData?.wind_speed_ms !== null
                      ? `${weatherData.wind_speed_ms} m/s`
                      : weatherData?.wind_speed !== undefined && weatherData?.wind_speed !== null
                      ? `${weatherData.wind_speed} m/s`
                      : 'Not available'}
                  </p>
                </div>
                <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
                  <span className="text-[10px] text-[#846255]">Wind Direction</span>
                  <p className="font-bold text-sm text-[#4d3328]">
                    {weatherData?.wind_direction_deg !== undefined && weatherData?.wind_direction_deg !== null
                      ? `${weatherData.wind_direction_deg}°`
                      : weatherData?.wind_direction !== undefined && weatherData?.wind_direction !== null
                      ? `${weatherData.wind_direction}°`
                      : 'Not available'}
                  </p>
                </div>
                <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
                  <span className="text-[10px] text-[#846255]">Wave Height</span>
                  <p className="font-bold text-sm text-[#4d3328]">
                    {weatherData?.wave_height_m !== undefined && weatherData?.wave_height_m !== null
                      ? `${weatherData.wave_height_m} m`
                      : 'Not available'}
                  </p>
                </div>
                <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
                  <span className="text-[10px] text-[#846255]">Wave Direction</span>
                  <p className="font-bold text-sm text-[#4d3328]">
                    {weatherData?.wave_direction_deg !== undefined && weatherData?.wave_direction_deg !== null
                      ? `${weatherData.wave_direction_deg}°`
                      : 'Not available'}
                  </p>
                </div>
                <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
                  <span className="text-[10px] text-[#846255]">Current Speed</span>
                  <p className="font-bold text-sm text-[#4d3328]">
                    {weatherData?.ocean_current_velocity_ms !== undefined && weatherData?.ocean_current_velocity_ms !== null
                      ? `${weatherData.ocean_current_velocity_ms} m/s`
                      : 'Not available'}
                  </p>
                </div>
                <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5">
                  <span className="text-[10px] text-[#846255]">Current Direction</span>
                  <p className="font-bold text-sm text-[#4d3328]">
                    {weatherData?.ocean_current_direction_deg !== undefined && weatherData?.ocean_current_direction_deg !== null
                      ? `${weatherData.ocean_current_direction_deg}°`
                      : 'Not available'}
                  </p>
                </div>
                <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-2.5 col-span-2">
                  <span className="text-[10px] text-[#846255]">Sea Surface Temp</span>
                  <p className="font-bold text-sm text-[#4d3328]">
                    {weatherData?.sea_surface_temperature_c !== undefined && weatherData?.sea_surface_temperature_c !== null
                      ? `${weatherData.sea_surface_temperature_c} °C`
                      : 'Not available'}
                  </p>
                </div>
              </div>
            )}
          </section>

          {/* Slick Extent & Impact */}
          <section className="space-y-2 border-t border-[#f0ddd1] pt-3">
            <p className="text-[10px] font-bold tracking-[.14em] text-[#1d4b3b]">SPILL IMPACT & EXTENT</p>
            {incident ? (
              <div className="space-y-1.5">
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#735247]">Selected Incident</span>
                  <span className="font-mono font-semibold text-[#663520]">{incident.id}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#735247]">Surface Slick Extent</span>
                  <span className="font-bold text-[#1d4b3b]">{incident.area_km2 !== undefined ? `${incident.area_km2} km²` : 'Not available'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#f0ddd1]">
                  <span className="text-[#735247]">Oil Probability</span>
                  <span className="font-semibold text-[#4d3328]">{incident.confidence ? `${Math.round(incident.confidence * 100)}%` : 'Not available'}</span>
                </div>
              </div>
            ) : (
              <p className="text-[#735247] py-1">Select an incident on the map to evaluate slick impact.</p>
            )}
          </section>

          {/* Environmental Risk Assessment */}
          <section className="space-y-2 border-t border-[#f0ddd1] pt-3">
            <p className="text-[10px] font-bold tracking-[.14em] text-[#1d4b3b]">ENVIRONMENTAL RISK ASSESSMENT</p>
            <p className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-3 text-[11px] text-[#735247]">
              Environmental risk assessment unavailable from active backend model. Calculated risk metrics will display when an environmental risk model is connected.
            </p>
          </section>

          {/* Response Progress */}
          <section className="space-y-2 border-t border-[#f0ddd1] pt-3">
            <p className="text-[10px] font-bold tracking-[.14em] text-[#1d4b3b]">RESPONSE PROGRESS</p>
            <p className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-3 text-[11px] text-[#735247]">
              Response progress not available. Incident disposition status: <b className="text-[#663520]">{incident?.status || 'Awaiting Review'}</b>.
            </p>
          </section>
        </aside>
      </div>
    </div>
  )
}

export default EnvironmentWorkspace
