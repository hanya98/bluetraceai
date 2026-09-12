import { useState } from 'react'
import { Activity, CloudSun, Radar, Route, ShipWheel, Waves } from 'lucide-react'

const tabs = [
  { id: 'evidence', label: 'Evidence', icon: Activity },
  { id: 'sar', label: 'SAR', icon: Radar },
  { id: 'weather', label: 'Weather', icon: CloudSun },
  { id: 'current', label: 'Ocean Current', icon: Waves },
  { id: 'ais', label: 'AIS', icon: ShipWheel },
  { id: 'timeline', label: 'Timeline', icon: Route },
]

function formatDate(value) {
  if (!value) return 'Not available'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not available'
  return date.toLocaleString('en-IN', { timeZone: 'UTC' }) + ' UTC'
}

const LabelValue = ({ label, value }) => (
  <div className="rounded-lg bg-white px-3 py-2">
    <p className="text-[10px] font-bold tracking-wide text-[#846255]">{label}</p>
    <p className="mt-1 text-sm font-semibold text-[#4d3328]">{value ?? 'Not available'}</p>
  </div>
)

function EvidenceTabs({ incident, evidence, environmental, provenance, vessels }) {
  const [active, setActive] = useState('evidence')

  if (!incident) return null

  const content = {
    evidence: (
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {Object.entries(evidence ?? {}).map(([key, value]) => (
          <LabelValue
            key={key}
            label={key.replace('_', ' ').toUpperCase()}
            value={typeof value === 'number' ? `${Math.round(value * 100)} / 100` : 'Not available'}
          />
        ))}
      </div>
    ),
    sar: (
      <div className="grid gap-2 sm:grid-cols-4">
        <LabelValue label="PLATFORM" value={incident.sar?.platform} />
        <LabelValue label="POLARIZATION" value={incident.sar?.polarization} />
        <LabelValue label="LOOK DIRECTION" value={incident.sar?.look_direction} />
        <LabelValue
          label="DARK FEATURE SCORE"
          value={incident.sar?.dark_feature_score !== undefined ? `${incident.sar.dark_feature_score}` : 'Not available'}
        />
      </div>
    ),
    weather: (
      <div className="grid gap-2 sm:grid-cols-4">
        <LabelValue
          label="WIND SPEED"
          value={environmental?.wind_speed !== null && environmental?.wind_speed !== undefined ? `${environmental.wind_speed} m/s` : 'Not available'}
        />
        <LabelValue
          label="WIND DIRECTION"
          value={environmental?.wind_direction !== null && environmental?.wind_direction !== undefined ? `${environmental.wind_direction}°` : 'Not available'}
        />
        <LabelValue
          label="WAVE HEIGHT"
          value={environmental?.wave_height_m !== null && environmental?.wave_height_m !== undefined ? `${environmental.wave_height_m} m` : 'Not available'}
        />
        <LabelValue
          label="SEA SURFACE TEMP."
          value={environmental?.sea_surface_temperature_c !== null && environmental?.sea_surface_temperature_c !== undefined ? `${environmental.sea_surface_temperature_c} °C` : 'Not available'}
        />
      </div>
    ),
    current: (
      <div className="grid gap-2 sm:grid-cols-3">
        <LabelValue
          label="CURRENT SPEED"
          value={environmental?.current_speed !== null && environmental?.current_speed !== undefined ? `${environmental.current_speed} m/s` : 'Not available'}
        />
        <LabelValue
          label="CURRENT DIRECTION"
          value={environmental?.current_direction !== null && environmental?.current_direction !== undefined ? `${environmental.current_direction}°` : 'Not available'}
        />
        <LabelValue label="MODELLING SOURCE" value={environmental?.source} />
      </div>
    ),
    ais: (
      <div className="grid gap-2 sm:grid-cols-2">
        {(vessels || []).map((vessel) => (
          <LabelValue
            key={vessel.id}
            label={`${vessel.vessel_name} · ${vessel.vessel_type}`}
            value={`Interest ${Math.round((vessel.vessel_of_interest_score || 0) * 100)}% ${
              vessel.ais_gap_minutes !== null && vessel.ais_gap_minutes !== undefined ? `· AIS gap ${vessel.ais_gap_minutes} min` : ''
            }`}
          />
        ))}
      </div>
    ),
    timeline: (
      <div className="grid gap-2 sm:grid-cols-3">
        <LabelValue label="SCENE ACQUIRED" value={formatDate(provenance?.acquisition_time || incident.detected_at)} />
        <LabelValue label="PROCESSED WITH" value={provenance?.processing_version} />
        <LabelValue label="MODEL" value={provenance?.model_version} />
      </div>
    ),
  }

  return (
    <section className="rounded-2xl border border-[#e6c8b5] bg-[#fdf2ea] p-4 shadow-sm text-[#4d3328]">
      <div className="flex gap-1 overflow-x-auto border-b border-[#ead2c3] pb-3">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            type="button"
            key={id}
            onClick={() => setActive(id)}
            className={`flex shrink-0 items-center gap-1 rounded-lg px-3 py-2 text-xs font-bold transition ${
              active === id ? 'bg-[#1d4b3b] text-[#f8eadf]' : 'text-[#735247] hover:bg-[#f4ded0]'
            }`}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>
      <div className="mt-4">{content[active]}</div>
    </section>
  )
}

export default EvidenceTabs
