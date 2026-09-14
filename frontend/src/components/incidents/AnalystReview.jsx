import { useState } from 'react'
import { CheckCircle2, ClipboardCheck, Save } from 'lucide-react'
import { useAnalystReview } from '../../hooks/useAnalystReview'

const dispositions = ['Needs Verification', 'Likely Oil', 'Likely Look-alike', 'Insufficient Evidence']

function ReviewForm({ incident, evidence, review, loading = false, saving = false, error, save }) {
  const [disposition, setDisposition] = useState(review?.disposition ?? 'Needs Verification')
  const [notes, setNotes] = useState(review?.notes ?? '')

  if (!incident) return null

  const summary = `SAR ${Math.round((evidence?.sar ?? 0) * 100)}/100 · Morphology ${Math.round(
    (evidence?.morphology ?? 0) * 100
  )}/100 · Wind ${Math.round((evidence?.wind ?? 0) * 100)}/100 · Current ${Math.round(
    (evidence?.current ?? 0) * 100
  )}/100`

  const alternativeExplanations =
    Object.entries(incident.look_alikes || {})
      .filter(([, likelihood]) => likelihood !== 'Low')
      .map(([label, likelihood]) => `${label.replaceAll('_', ' ')}: ${likelihood}`)
      .join(' · ') || 'No elevated alternative explanation in this record.'

  return (
    <section className="border-t-4 border-[#663520] bg-[#fffaf6] p-5 text-[#4d3328]">
      <div className="flex items-center justify-between">
        <div>
          <p className="flex items-center gap-2 text-xs font-bold tracking-[.14em] text-[#1d4b3b]">
            <ClipboardCheck size={16} />
            ANALYST REVIEW
          </p>
          <p className="mt-1 text-xs text-[#735247]">Analyst Decision is independent of AI Assessment.</p>
        </div>
        {review && (
          <span className="flex items-center gap-1 text-[11px] font-bold text-[#1d4b3b]">
            <CheckCircle2 size={15} />
            Analyst reviewed
          </span>
        )}
      </div>

      <div className="mt-4 grid gap-3 border-y border-[#ead2c3] py-3 text-xs">
        <div className="grid grid-cols-[140px_1fr] gap-2">
          <span className="font-bold tracking-wide text-[#846255]">CURRENT AI ASSESSMENT</span>
          <span className="font-semibold text-[#4d3328]">{incident.classification}</span>
        </div>
        <div className="grid grid-cols-[140px_1fr] gap-2">
          <span className="font-bold tracking-wide text-[#846255]">AI CONFIDENCE</span>
          <span className="font-semibold text-[#4d3328]">{Math.round((incident.confidence || 0) * 100)}%</span>
        </div>
        <div className="grid grid-cols-[140px_1fr] gap-2">
          <span className="font-bold tracking-wide text-[#846255]">EVIDENCE SUMMARY</span>
          <span className="text-[#4d3328]">{summary}</span>
        </div>
        <div className="grid grid-cols-[140px_1fr] gap-2">
          <span className="font-bold tracking-wide text-[#846255]">ALTERNATIVE EXPLANATIONS</span>
          <span className="capitalize text-[#4d3328]">{alternativeExplanations}</span>
        </div>
      </div>

      <p className="mt-4 text-xs font-bold tracking-[.14em] text-[#1d4b3b]">ANALYST DISPOSITION</p>
      <div className="mt-2 grid grid-cols-2 gap-2">
        {dispositions.map((item) => (
          <button
            type="button"
            key={item}
            onClick={() => setDisposition(item)}
            className={`rounded-lg border px-2 py-2 text-left text-xs font-bold transition ${
              disposition === item
                ? 'border-[#1d4b3b] bg-[#1d4b3b] text-[#f8eadf]'
                : 'border-[#e6c8b5] bg-white text-[#4d3328] hover:border-[#1d4b3b]'
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      <label className="mt-4 block text-xs font-bold tracking-[.12em] text-[#846255]">
        NOTES <span className="font-normal normal-case">(optional)</span>
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Add analyst observations or verification needs…"
          className="mt-2 min-h-20 w-full resize-y rounded-lg border border-[#e6c8b5] bg-white p-2.5 text-sm font-normal tracking-normal text-[#4d3328] outline-none transition focus:border-[#1d4b3b]"
        />
      </label>

      {error && <p className="mt-2 text-xs text-[#9a3412]">Unable to save review locally.</p>}

      <button
        type="button"
        onClick={() => save({ disposition, notes })}
        disabled={saving}
        className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-[#663520] px-3 py-2.5 text-sm font-bold text-[#f8eadf] transition hover:bg-[#4d2618] disabled:opacity-60"
      >
        <Save size={15} />
        {saving ? 'Saving review…' : 'Save Review'}
      </button>

      {review && (
        <p className="mt-3 text-center text-[11px] text-[#735247]">
          Analyst reviewed · {new Date(review.reviewed_at).toLocaleString('en-IN', { timeZone: 'UTC' })} UTC · Decision: <b>{review.disposition}</b>
        </p>
      )}
    </section>
  )
}

function AnalystReview({ incident, evidence }) {
  const { review, loading, saving, error, save } = useAnalystReview(incident?.id)
  if (!incident) return null
  return (
    <ReviewForm
      key={`${incident.id}:${review?.reviewed_at ?? 'new'}`}
      incident={incident}
      evidence={evidence}
      review={review}
      saving={saving}
      error={error}
      save={save}
    />
  )
}

export default AnalystReview
