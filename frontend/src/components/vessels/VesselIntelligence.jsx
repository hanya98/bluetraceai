import { ChevronRight, CircleAlert, Route, Ship, Timer, Waves } from 'lucide-react'

const band = (score) => {
  if (score === null || score === undefined || Number.isNaN(Number(score))) return 'Not evaluated'
  const num = Number(score)
  return num >= 0.7 ? 'High' : num >= 0.45 ? 'Medium' : 'Low'
}

const Factor = ({ label, value, detail }) => (
  <div className="rounded-lg bg-[#fdf2ea] p-2.5">
    <p className="text-[10px] font-bold tracking-wide text-[#846255]">{label}</p>
    <p className="mt-1 text-sm font-bold text-[#4d3328]">{value}</p>
    {detail && <p className="mt-0.5 text-[10px] text-[#735247]">{detail}</p>}
  </div>
)

function VesselIntelligence({ vessels, selectedVesselId, onSelect }) {
  const ranked = [...(vessels || [])].sort(
    (a, b) => (b.vessel_of_interest_score || 0) - (a.vessel_of_interest_score || 0)
  )
  const selected = ranked.find((vessel) => vessel.id === selectedVesselId)

  if (!ranked.length) {
    return (
      <section className="rounded-2xl border border-[#e6c8b5] bg-white p-4 text-sm text-[#735247]">
        No Vessel of Interest candidate records are returned by attribution analysis for this scene.
      </section>
    )
  }

  return (
    <section className="rounded-2xl border border-[#e6c8b5] bg-white p-4 shadow-sm text-[#4d3328]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold tracking-[.14em] text-[#1d4b3b]">AIS VESSEL INTELLIGENCE</p>
          <h2 className="mt-1 font-serif text-xl text-[#663520]">Vessels of Interest</h2>
        </div>
        <div className="flex max-w-56 gap-1.5 text-right text-[10px] leading-relaxed text-[#735247]">
          <CircleAlert className="shrink-0 text-[#663520]" size={15} />
          Ranking score represents candidate priority for verification; it is not a legal attribution.
        </div>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(280px,.8fr)]">
        <div className="space-y-2">
          {ranked.map((vessel, index) => {
            const selectedItem = vessel.id === selectedVesselId
            const overlap = band(vessel.corridor_overlap)
            const feasibility = band(vessel.time_feasibility)

            return (
              <button
                type="button"
                key={vessel.id}
                onClick={() => onSelect(vessel.id)}
                className={`w-full rounded-xl border p-3 text-left transition ${
                  selectedItem
                    ? 'border-[#1d4b3b] bg-[#1d4b3b] text-[#f8eadf] shadow-md'
                    : 'border-[#ead2c3] hover:border-[#1d4b3b] hover:bg-[#fdf2ea] text-[#4d3328]'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex gap-2">
                    <span
                      className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold ${
                        selectedItem ? 'bg-[#ffd4ba] text-[#663520]' : 'bg-[#f2d8c8] text-[#663520]'
                      }`}
                    >
                      #{index + 1}
                    </span>
                    <div>
                      <p className="text-xs font-bold tracking-[.1em] opacity-75">VESSEL OF INTEREST</p>
                      <p className="mt-0.5 flex items-center gap-1 text-sm font-bold">
                        <Ship size={14} />
                        {vessel.vessel_name}
                      </p>
                      <p className={`mt-0.5 text-xs ${selectedItem ? 'text-[#ffd4ba]' : 'text-[#735247]'}`}>
                        MMSI {vessel.mmsi} · {vessel.vessel_type}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-lg font-bold">
                    {Math.round((vessel.vessel_of_interest_score || 0) * 100)}%
                    <ChevronRight size={16} />
                  </div>
                </div>

                <div
                  className={`mt-3 grid grid-cols-4 gap-2 border-t pt-2 text-xs ${
                    selectedItem ? 'border-[#70a18d]' : 'border-[#f0ddd1]'
                  }`}
                >
                  <span>
                    Overlap <b>{overlap}</b>
                  </span>
                  <span>
                    Timing <b>{feasibility}</b>
                  </span>
                  <span>
                    Gap <b>{vessel.ais_gap_minutes !== null ? `${vessel.ais_gap_minutes} min` : 'N/A'}</b>
                  </span>
                  <span>
                    Distance <b>{vessel.distance_km !== null ? `${vessel.distance_km} km` : 'N/A'}</b>
                  </span>
                </div>
              </button>
            )
          })}
        </div>

        <div className="rounded-xl border border-[#ead2c3] bg-[#fffaf6] p-4">
          {selected ? (
            <>
              <p className="text-xs font-bold tracking-[.12em] text-[#1d4b3b]">RANKING FACTORS & EXPLANATION</p>
              <h3 className="mt-1 text-lg font-bold text-[#663520]">{selected.vessel_name}</h3>
              <p className="mt-1 text-xs text-[#735247]">
                Score is an evidence-weighted candidate priority indicator, not a finding of responsibility.
              </p>

              <div className="mt-4 grid grid-cols-2 gap-2">
                <Factor
                  label="VESSEL OF INTEREST SCORE"
                  value={`${Math.round((selected.vessel_of_interest_score || 0) * 100)}%`}
                />
                <Factor
                  label="DISTANCE FROM CENTROID"
                  value={selected.distance_km !== null ? `${selected.distance_km} km` : 'Not available'}
                />
                <Factor
                  label="SPATIAL / CORRIDOR OVERLAP"
                  value={band(selected.corridor_overlap)}
                  detail={selected.corridor_overlap !== null ? `${Math.round(selected.corridor_overlap * 100)} / 100` : null}
                />
                <Factor
                  label="TIME FEASIBILITY"
                  value={band(selected.time_feasibility)}
                  detail={selected.time_feasibility !== null ? `${Math.round(selected.time_feasibility * 100)} / 100` : null}
                />
                <Factor
                  label="AIS DATA GAP"
                  value={selected.ais_gap_minutes !== null ? `${selected.ais_gap_minutes} min` : 'Not available'}
                  detail={selected.ais_gap_minutes ? 'Missing AIS ping coverage' : 'Continuous AIS ping track'}
                />
                <Factor
                  label="MOVEMENT / SPEED"
                  value={
                    selected.speed !== null && selected.heading !== null
                      ? `${selected.speed} kn · ${selected.heading}°`
                      : 'Not available'
                  }
                />
              </div>

              {selected.explanation && (
                <div className="mt-3 rounded-lg border-l-4 border-[#1d4b3b] bg-[#fdf2ea] p-3 text-xs leading-relaxed text-[#4d3328]">
                  <p className="font-bold text-[#1d4b3b]">Model 3 Non-Causal Explanation:</p>
                  <p className="mt-0.5">{selected.explanation}</p>
                </div>
              )}

              <div className="mt-3 flex items-start gap-2 rounded-lg bg-[#fdf2ea] p-2.5 text-[11px] leading-relaxed text-[#735247]">
                <Waves size={15} className="mt-0.5 shrink-0 text-[#1d4b3b]" />
                Candidate vessel trajectory rendered on map interface.
              </div>
            </>
          ) : (
            <div className="grid h-full place-items-center text-center text-sm text-[#735247]">
              <div>
                <Route className="mx-auto mb-2 text-[#1d4b3b]" />
                <p>Select a Vessel of Interest to inspect ranking factors and trajectory.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-3 flex items-center gap-2 border-t border-[#f0ddd1] pt-3 text-[11px] text-[#735247]">
        <Timer size={14} className="text-[#663520]" />
        Priority ranking incorporates spatio-temporal trajectory alignment, AIS gap analysis, and ocean drift parameters for analyst decision support.
      </div>
    </section>
  )
}

export default VesselIntelligence
