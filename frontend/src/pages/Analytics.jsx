import { useMemo } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Activity, Droplets, Eye, ScanSearch, ShieldCheck, Waves } from 'lucide-react'
import { useIncidents } from '../hooks/useIncidents'

const colors = ['#1d4b3b', '#663520', '#c16d4c', '#d9a77f']

const Card = ({ icon: Icon, label, value, note }) => (
  <article className="rounded-xl border border-[#e6c8b5] bg-white p-4 shadow-sm text-[#4d3328]">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-[10px] font-bold tracking-[.13em] text-[#846255]">{label}</p>
        <p className="mt-2 font-serif text-3xl text-[#663520]">{value}</p>
      </div>
      <span className="rounded-lg bg-[#fdf2ea] p-2 text-[#1d4b3b]">
        <Icon size={18} />
      </span>
    </div>
    <p className="mt-2 text-[11px] text-[#735247]">{note}</p>
  </article>
)

const Panel = ({ title, subtitle, children }) => (
  <section className="rounded-2xl border border-[#e6c8b5] bg-white p-4 shadow-sm text-[#4d3328]">
    <div className="mb-4">
      <h2 className="font-serif text-lg text-[#663520]">{title}</h2>
      <p className="mt-0.5 text-xs text-[#735247]">{subtitle}</p>
    </div>
    {children}
  </section>
)

const ChartTooltip = ({ active, payload, label }) =>
  active && payload?.length ? (
    <div className="rounded-lg border border-[#e6c8b5] bg-[#fffaf6] px-3 py-2 text-xs shadow text-[#4d3328]">
      <p className="font-bold text-[#663520]">{label ?? payload[0].name}</p>
      <p className="mt-1 text-[#4d3328]">{payload[0].value}</p>
    </div>
  ) : null

function Analytics() {
  const { incidents, liveIncidents, demoIncidents, loading, error } = useIncidents()

  const intelligence = useMemo(() => {
    const total = incidents.length
    const liveCount = liveIncidents?.length || 0
    const demoCount = demoIncidents?.length || 0

    const likelyOil = incidents.filter((i) => i.classification === 'Likely Oil').length
    const likelyLookAlike = incidents.filter((i) => i.classification === 'Likely Look-alike').length
    const needsVerification = incidents.filter((i) => i.status === 'Needs Verification').length

    const validConfidences = incidents.map((i) => i.confidence).filter((c) => typeof c === 'number' && !Number.isNaN(c))
    const averageConfidence = validConfidences.length
      ? validConfidences.reduce((sum, c) => sum + c, 0) / validConfidences.length
      : 0

    const totalExtent = incidents.reduce((sum, i) => sum + (Number(i.area_km2) || 0), 0)

    const byStatus = Array.from(new Set(incidents.map((i) => i.status || 'Needs Verification'))).map(
      (status) => ({
        name: status,
        value: incidents.filter((i) => (i.status || 'Needs Verification') === status).length,
      })
    )

    const confidenceDistribution = [
      { name: '0–49%', value: incidents.filter((i) => i.confidence < 0.5).length },
      { name: '50–69%', value: incidents.filter((i) => i.confidence >= 0.5 && i.confidence < 0.7).length },
      { name: '70–84%', value: incidents.filter((i) => i.confidence >= 0.7 && i.confidence < 0.85).length },
      { name: '85–100%', value: incidents.filter((i) => i.confidence >= 0.85).length },
    ]

    const overTime = [...incidents]
      .sort((a, b) => new Date(a.detected_at || 0) - new Date(b.detected_at || 0))
      .map((i) => {
        const d = new Date(i.detected_at)
        const dateStr = !Number.isNaN(d.getTime())
          ? new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', timeZone: 'UTC' }).format(d)
          : 'N/A'
        return { date: dateStr, candidates: 1 }
      })

    const extents = [...incidents]
      .sort((a, b) => (Number(b.area_km2) || 0) - (Number(a.area_km2) || 0))
      .map((i) => ({ name: i.id, extent: Number(i.area_km2) || 0 }))

    return {
      total,
      liveCount,
      demoCount,
      likelyOil,
      likelyLookAlike,
      needsVerification,
      averageConfidence,
      totalExtent,
      byStatus,
      confidenceDistribution,
      overTime,
      extents,
    }
  }, [incidents, liveIncidents, demoIncidents])

  if (loading) return <p className="p-8 text-[#663520]">Loading operational intelligence…</p>
  if (error) return <p className="p-8 text-[#663520]">Unable to load intelligence.</p>

  const isLiveActive = intelligence.liveCount > 0

  return (
    <div className="space-y-5 text-[#4d3328]">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold tracking-[.16em] text-[#1d4b3b]">OPERATIONAL INTELLIGENCE</p>
          <h1 className="mt-1 font-serif text-3xl text-[#663520]">Candidate Activity Overview</h1>
        </div>
        <p className="max-w-md rounded-lg border border-[#e6c8b5] bg-[#fffaf6] px-3 py-2 text-xs leading-relaxed text-[#735247]">
          {isLiveActive
            ? `Metrics summarize ${intelligence.total} total candidate records (${intelligence.liveCount} live FastAPI analysis predictions, ${intelligence.demoCount} historical records). Analyst verification required.`
            : `Metrics summarize ${intelligence.total} Oil Spill Candidate records for analyst triage and evidence review.`}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <Card
          icon={Activity}
          label="TOTAL INCIDENTS"
          value={intelligence.total}
          note={
            isLiveActive
              ? `${intelligence.liveCount} Live FastAPI Analyses · ${intelligence.demoCount} Historical Records`
              : 'Evaluated Oil Spill Candidate records'
          }
        />
        <Card
          icon={Droplets}
          label="LIKELY OIL"
          value={intelligence.likelyOil}
          note="AI classification; verification required"
        />
        <Card
          icon={Eye}
          label="LIKELY LOOK-ALIKE"
          value={intelligence.likelyLookAlike}
          note="Alternative explanation remains plausible"
        />
        <Card
          icon={ShieldCheck}
          label="NEEDS VERIFICATION"
          value={intelligence.needsVerification}
          note="Current workflow state"
        />
        <Card
          icon={ScanSearch}
          label="AVERAGE CONFIDENCE"
          value={`${Math.round(intelligence.averageConfidence * 100)}%`}
          note="Across active candidate records"
        />
        <Card
          icon={Waves}
          label="TOTAL SLICK EXTENT"
          value={`${intelligence.totalExtent.toFixed(2)} km²`}
          note="Predicted surface extent, not confirmed boundary"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Review status" subtitle="Current disposition queue across candidate records">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={intelligence.byStatus}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={62}
                  outerRadius={92}
                  paddingAngle={3}
                >
                  {intelligence.byStatus.map((entry, index) => (
                    <Cell key={entry.name} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 text-xs text-[#735247]">
            {intelligence.byStatus.map((item, index) => (
              <span key={item.name}>
                <i
                  className="mr-1 inline-block h-2.5 w-2.5 rounded-full"
                  style={{ background: colors[index % colors.length] }}
                />
                {item.name}: {item.value}
              </span>
            ))}
          </div>
        </Panel>

        <Panel title="Confidence distribution" subtitle="AI confidence bands for analyst prioritization">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={intelligence.confidenceDistribution} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#f0ddd1" />
                <XAxis dataKey="name" tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="value" radius={[5, 5, 0, 0]} fill="#1d4b3b" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Detection sequence" subtitle="Candidate records ordered by acquisition timestamp">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={intelligence.overTime} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="candidateGradient" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#1d4b3b" stopOpacity={0.38} />
                    <stop offset="100%" stopColor="#1d4b3b" stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#f0ddd1" />
                <XAxis dataKey="date" tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="stepAfter" dataKey="candidates" stroke="#1d4b3b" strokeWidth={3} fill="url(#candidateGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Surface slick extent" subtitle="Predicted extent by candidate record">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={intelligence.extents} layout="vertical" margin={{ top: 2, right: 18, left: 18, bottom: 0 }}>
                <CartesianGrid horizontal={false} stroke="#f0ddd1" />
                <XAxis type="number" tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} width={80} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="extent" name="km²" radius={[0, 5, 5, 0]} fill="#663520" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  )
}

export default Analytics
