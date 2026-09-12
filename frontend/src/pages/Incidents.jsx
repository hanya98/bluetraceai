import { Activity, Clock3, MapPin, Zap } from 'lucide-react'
import StatusBadge from '../components/common/StatusBadge'
import { useIncidents } from '../hooks/useIncidents'

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

function Incidents() {
  const { liveIncidents, demoIncidents, loading, error } = useIncidents()

  if (loading) return <p className="p-8 text-[#663520]">Loading oil spill candidates…</p>
  if (error) return <p className="p-8 text-rose-600">Unable to load candidates.</p>

  return (
    <section className="space-y-6 text-[#4d3328]">
      <div>
        <p className="text-xs font-bold tracking-[.16em] text-[#1d4b3b]">CANDIDATE REPOSITORY</p>
        <h2 className="mt-1 font-serif text-3xl text-[#663520]">Oil Spill Candidates</h2>
        <p className="mt-1 text-xs text-[#735247]">
          Unified view of live FastAPI ML analysis predictions and synthetic demonstration records.
        </p>
      </div>

      {/* Live Analyses Section */}
      {liveIncidents.length > 0 && (
        <div className="space-y-3">
          <h3 className="flex items-center gap-2 font-serif text-xl text-[#1d4b3b]">
            <Zap size={18} className="text-emerald-700" />
            Live FastAPI ML Pipeline Analyses ({liveIncidents.length})
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {liveIncidents.map((incident) => (
              <article key={incident.id} className="rounded-xl border border-emerald-300 bg-emerald-50/40 p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-emerald-900">{incident.id}</span>
                  <span className="flex items-center gap-1 rounded bg-emerald-700 px-2 py-0.5 text-[10px] font-bold text-white">
                    <Zap size={10} /> LIVE ML
                  </span>
                </div>
                <h4 className="mt-2 flex items-center gap-1.5 font-bold text-[#4d3328]">
                  <MapPin size={15} className="text-[#1d4b3b]" />
                  {incident.location_name}
                </h4>
                <p className="mt-1 flex items-center gap-1 text-xs text-[#735247]">
                  <Clock3 size={13} /> {formatTime(incident.detected_at)}
                </p>
                <div className="mt-3 flex items-center justify-between border-t border-emerald-200/60 pt-2 text-xs">
                  <StatusBadge status={incident.status} />
                  <span className="font-semibold text-[#1d4b3b]">
                    {incident.classification} ({Math.round((incident.confidence || 0) * 100)}%)
                  </span>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      {/* Synthetic Demo Section */}
      <div className="space-y-3">
        <h3 className="flex items-center gap-2 font-serif text-xl text-[#663520]">
          <Activity size={18} />
          Stored Candidate Records ({demoIncidents.length})
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {demoIncidents.map((incident) => (
            <article key={incident.id} className="rounded-xl border border-[#e6c8b5] bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-[#663520]">{incident.id}</span>
                <span className="rounded bg-[#735247]/15 px-2 py-0.5 text-[10px] font-bold text-[#663520]">
                  STORED
                </span>
              </div>
              <h4 className="mt-2 flex items-center gap-1.5 font-bold text-[#4d3328]">
                <MapPin size={15} className="text-[#663520]" />
                {incident.location_name}
              </h4>
              <p className="mt-1 flex items-center gap-1 text-xs text-[#735247]">
                <Clock3 size={13} /> {formatTime(incident.detected_at)}
              </p>
              <div className="mt-3 flex items-center justify-between border-t border-[#f0ddd1] pt-2 text-xs">
                <StatusBadge status={incident.status} />
                <span className="font-semibold text-[#663520]">
                  {incident.classification} ({Math.round((incident.confidence || 0) * 100)}%)
                </span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

export default Incidents
