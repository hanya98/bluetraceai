import { Clock3, MapPin, Zap } from 'lucide-react'
import StatusBadge from '../common/StatusBadge'

function formatTime(value) {
  if (!value) return 'Not available'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not available'
  return (
    new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
    }).format(date) + ' UTC'
  )
}

function IncidentList({ incidents, selectedId, onSelect }) {
  const liveCount = incidents.filter((i) => i.is_live_analysis).length
  const demoCount = incidents.length - liveCount

  return (
    <aside className="overflow-hidden rounded-2xl border border-[#e6c8b5] bg-white shadow-sm text-[#4d3328]">
      <div className="border-b border-[#f0ddd1] px-4 py-4">
        <p className="text-xs font-bold tracking-[.14em] text-[#1d4b3b]">ANALYSIS QUEUE</p>
        <h2 className="mt-1 font-serif text-xl text-[#663520]">Oil Spill Candidates</h2>
        <p className="mt-1 text-xs text-[#7a5a4b]">
          {liveCount > 0
            ? `${liveCount} Live FastAPI Analysis · ${demoCount} Stored Records`
            : 'Historical stored records'}
        </p>
      </div>

      <div className="max-h-[520px] overflow-y-auto p-2">
        {incidents.map((incident) => {
          const isSelected = selectedId === incident.id
          const isLive = Boolean(incident.is_live_analysis)

          return (
            <button
              type="button"
              key={incident.id}
              onClick={() => onSelect(incident.id)}
              className={`mb-1 w-full rounded-xl p-3 text-left transition ${
                isSelected
                  ? 'bg-[#1d4b3b] text-[#f8eadf] shadow-md'
                  : 'hover:bg-[#fdf2ea] text-[#4d3328]'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-xs font-bold">{incident.id}</span>
                  {isLive ? (
                    <span className="flex items-center gap-0.5 rounded bg-emerald-700 px-1.5 py-0.5 text-[9px] font-bold text-emerald-50">
                      <Zap size={9} /> LIVE ML
                    </span>
                  ) : (
                    <span className="rounded bg-[#2a4d6e]/20 px-1.5 py-0.5 text-[9px] font-bold text-[#5a7a94]">
                      STORED
                    </span>
                  )}
                </div>
                <span className="text-xs font-bold">{Math.round((incident.confidence || 0) * 100)}%</span>
              </div>

              <p className="mt-2 flex items-center gap-1 text-sm font-semibold">
                <MapPin size={14} className="shrink-0" />
                <span className="truncate">{incident.location_name}</span>
              </p>

              <p
                className={`mt-1 flex items-center gap-1 text-xs ${
                  isSelected ? 'text-[#ffd4ba]' : 'text-[#7a5a4b]'
                }`}
              >
                <Clock3 size={13} className="shrink-0" />
                {formatTime(incident.detected_at)}
              </p>

              <div className="mt-3 flex items-center justify-between">
                <StatusBadge status={incident.status} />
                <span
                  className={`text-[10px] font-medium ${
                    isSelected ? 'text-[#ffd4ba]' : 'text-[#846255]'
                  }`}
                >
                  {incident.area_km2 ? `${incident.area_km2} km²` : 'Extent N/A'}
                </span>
              </div>
            </button>
          )
        })}
      </div>
    </aside>
  )
}

export default IncidentList
