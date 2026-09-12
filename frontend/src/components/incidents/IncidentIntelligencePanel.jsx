import { Database, Droplets, Gauge, Radar, ScanSearch, ShieldAlert, Wind, Zap } from 'lucide-react'
import StatusBadge from '../common/StatusBadge'
import AnalystReview from './AnalystReview'

const riskStyle = {
  Low: 'bg-[#d9ead7] text-[#1d4b3b]',
  Medium: 'bg-[#ffd4ba] text-[#663520]',
  High: 'bg-[#663520] text-[#f8eadf]',
  'Not evaluated': 'bg-stone-200 text-stone-700',
}

function formatDate(value) {
  if (!value) return 'Not available'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not available'
  return date.toLocaleString('en-IN', { timeZone: 'UTC' }) + ' UTC'
}

const Field = ({ label, value }) => (
  <div>
    <p className="text-[10px] font-bold tracking-[.12em] text-[#846255]">{label}</p>
    <p className="mt-0.5 text-sm font-semibold text-[#4d3328]">{value ?? 'Not available'}</p>
  </div>
)

const Section = ({ icon: Icon, title, children }) => (
  <section className="border-b border-[#ead2c3] py-4 last:border-0">
    <h3 className="mb-3 flex items-center gap-2 text-xs font-bold tracking-[.14em] text-[#1d4b3b]">
      <Icon size={15} />
      {title}
    </h3>
    {children}
  </section>
)

function IncidentIntelligencePanel({
  incident,
  evidence,
  environmental,
  provenance,
  selectedVesselId,
  vessels,
}) {
  if (!incident)
    return <aside className="rounded-2xl border border-[#e6c8b5] bg-white p-5 text-sm text-[#735247]">Select an incident to view intelligence evidence…</aside>

  const isLive = Boolean(incident.is_live_analysis)
  const profile = incident.morphology || {}
  const lookAlikes = incident.look_alikes || {}
  const selectedVessel = (vessels || []).find((vessel) => vessel.id === selectedVesselId)

  const evidenceParts = []
  if (evidence?.sar !== null && evidence?.sar !== undefined) {
    evidenceParts.push(`SAR ${Math.round(evidence.sar * 100)}/100`)
  }
  if (evidence?.morphology !== null && evidence?.morphology !== undefined) {
    evidenceParts.push(`morphology ${Math.round(evidence.morphology * 100)}/100`)
  }
  if (evidence?.wind !== null && evidence?.wind !== undefined) {
    evidenceParts.push(`wind data available`)
  }
  const summaryPrefix = evidenceParts.length ? `Evidence signals: ${evidenceParts.join(', ')}.` : 'AI assessment in progress.'
  const summary = `${summaryPrefix} Classification is ${incident.classification}; status is ${incident.status}.`

  return (
    <aside className="max-h-[570px] overflow-y-auto rounded-2xl border border-[#e6c8b5] bg-white text-[#4d3328] shadow-sm">
      <div className="sticky top-0 z-10 border-b border-[#f0ddd1] bg-white/95 p-5 backdrop-blur">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <p className="text-xs font-bold tracking-[.14em] text-[#1d4b3b]">INCIDENT EVIDENCE</p>
              {isLive ? (
                <span className="flex items-center gap-0.5 rounded bg-emerald-700 px-1.5 py-0.5 text-[9px] font-bold text-white">
                  <Zap size={9} /> LIVE ML
                </span>
              ) : (
                <span className="rounded bg-[#735247]/15 px-1.5 py-0.5 text-[9px] font-bold text-[#663520]">
                  STORED
                </span>
              )}
            </div>
            <h2 className="mt-1 font-serif text-xl text-[#663520]">{incident.id}</h2>
          </div>
          <StatusBadge status={incident.status} />
        </div>
        <p className="mt-2 text-xs text-[#735247]">
          {isLive
            ? 'Live FastAPI pipeline prediction · analyst verification required'
            : 'Stored historical record · analyst verification required'}
        </p>
      </div>

      <div className="px-5">
        <Section icon={Gauge} title="AI ASSESSMENT">
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Field label="CLASSIFICATION" value={incident.classification} />
            <Field
              label="OVERALL CONFIDENCE"
              value={incident.confidence !== undefined ? `${Math.round(incident.confidence * 100)}%` : 'Not available'}
            />
            <Field
              label="SURFACE SLICK EXTENT"
              value={incident.area_km2 !== undefined && incident.area_km2 !== null ? `${incident.area_km2} km²` : 'Not available'}
            />
            <Field label="CURRENT STATUS" value={incident.status} />
          </div>
        </Section>

        <Section icon={Radar} title="SAR EVIDENCE">
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Field label="SAR SCENE ID" value={provenance?.scene_id} />
            <Field label="ACQUISITION TIME" value={formatDate(provenance?.acquisition_time || incident.detected_at)} />
            <Field label="POLARIZATION" value={incident.sar?.polarization} />
            <Field
              label="MODEL CONFIDENCE"
              value={incident.confidence !== undefined ? `${Math.round(incident.confidence * 100)}%` : 'Not available'}
            />
            <Field label="PROCESSING VERSION" value={provenance?.processing_version} />
          </div>
        </Section>

        <Section icon={ScanSearch} title="MORPHOLOGY">
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Field
              label="AREA"
              value={profile.area_km2 !== undefined && profile.area_km2 !== null ? `${profile.area_km2} km²` : 'Not available'}
            />
            <Field
              label="PERIMETER"
              value={profile.perimeter_km !== undefined && profile.perimeter_km !== null ? `${profile.perimeter_km} km` : 'Not available'}
            />
            <Field label="ELONGATION" value={profile.elongation ? `${profile.elongation}` : 'Not available'} />
            <Field
              label="SHAPE INDICATORS"
              value={Array.isArray(profile.shape_indicators) && profile.shape_indicators.length ? profile.shape_indicators.join(', ') : 'Not available'}
            />
          </div>
        </Section>

        <Section icon={Wind} title="ENVIRONMENTAL CONTEXT">
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Field
              label="WIND SPEED"
              value={environmental?.wind_speed !== null && environmental?.wind_speed !== undefined ? `${environmental.wind_speed} m/s` : 'Not available'}
            />
            <Field
              label="WIND DIRECTION"
              value={environmental?.wind_direction !== null && environmental?.wind_direction !== undefined ? `${environmental.wind_direction}°` : 'Not available'}
            />
            <Field
              label="CURRENT SPEED"
              value={environmental?.current_speed !== null && environmental?.current_speed !== undefined ? `${environmental.current_speed} m/s` : 'Not available'}
            />
            <Field
              label="CURRENT DIRECTION"
              value={environmental?.current_direction !== null && environmental?.current_direction !== undefined ? `${environmental.current_direction}°` : 'Not available'}
            />
          </div>
        </Section>

        <Section icon={ShieldAlert} title="LOOK-ALIKE ANALYSIS">
          <p className="mb-3 text-xs text-[#735247]">
            {isLive ? 'Look-alike classification evaluation from Model 2 (YOLO11n).' : 'Alternative Explanation likelihoods from the mock analysis record.'}
          </p>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(lookAlikes).map(([label, risk]) => {
              const displayRisk = typeof risk === 'string' ? risk : 'Not evaluated'
              const badgeClass = riskStyle[displayRisk] || riskStyle['Not evaluated']
              return (
                <div key={label} className="flex items-center justify-between rounded-lg bg-[#fdf2ea] px-2.5 py-2">
                  <span className="text-xs capitalize text-[#4d3328]">{label.replaceAll('_', ' ')}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${badgeClass}`}>{displayRisk}</span>
                </div>
              )
            })}
          </div>
        </Section>

        <Section icon={Droplets} title="EVIDENCE SUMMARY">
          <p className="rounded-lg border-l-4 border-[#1d4b3b] bg-[#fdf2ea] p-3 text-xs leading-relaxed text-[#4d3328]">
            {summary}
          </p>
        </Section>

        <Section icon={Database} title="PROVENANCE">
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Field label="SCENE ID" value={provenance?.scene_id} />
            <Field label="ACQUISITION TIMESTAMP" value={formatDate(provenance?.acquisition_time || incident.detected_at)} />
            <Field label="PROCESSING VERSION" value={provenance?.processing_version} />
            <Field label="MODEL VERSION" value={provenance?.model_version} />
            <Field label="DATA SOURCE" value={provenance?.data_source ?? incident.sar?.platform} />
          </div>
        </Section>

        {selectedVessel && (
          <Section icon={Radar} title="SELECTED VESSEL OF INTEREST">
            <p className="text-sm font-bold text-[#663520]">{selectedVessel.vessel_name}</p>
            <p className="mt-1 text-xs text-[#735247]">
              {selectedVessel.vessel_type} · MMSI {selectedVessel.mmsi} · Interest score{' '}
              {Math.round((selectedVessel.vessel_of_interest_score || 0) * 100)}%
            </p>
          </Section>
        )}
      </div>

      <AnalystReview incident={incident} evidence={evidence} />
    </aside>
  )
}

export default IncidentIntelligencePanel
