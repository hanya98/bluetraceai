import { useMemo, useState } from 'react'
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
import {
  Activity,
  BarChart3,
  Calendar,
  ChevronDown,
  ChevronUp,
  Clock3,
  Database,
  Droplets,
  Eye,
  Filter,
  Globe2,
  Info,
  MapPin,
  Radar,
  Search,
  ShieldCheck,
  Ship,
  Sparkles,
  Waves,
  Zap,
} from 'lucide-react'
import StatusBadge from '../components/common/StatusBadge'
import { useIncidents } from '../hooks/useIncidents'

const CHART_COLORS = ['#1d4b3b', '#663520', '#c16d4c', '#d9a77f', '#2a4d6e']

function formatTime(value) {
  if (!value) return 'Not available'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not available'
  return (
    new Intl.DateTimeFormat('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
    }).format(date) + ' UTC'
  )
}

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
  <section className="rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm text-[#4d3328]">
    <div className="mb-4 border-b border-[#f0ddd1] pb-3">
      <h3 className="font-serif text-lg text-[#663520]">{title}</h3>
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

function EmptyTrendNotice() {
  return (
    <div className="flex h-48 w-full flex-col items-center justify-center rounded-xl border border-dashed border-[#e6c8b5] bg-[#fffaf6] p-4 text-center">
      <BarChart3 className="mb-2 text-[#b08876]" size={24} />
      <p className="text-xs font-semibold text-[#735247]">No historical data available for this trend.</p>
      <p className="mt-1 text-[11px] text-[#8a685c]">
        Execute SAR image analyses or load additional incident records to populate historical trend metrics.
      </p>
    </div>
  )
}

function History() {
  const { incidents, liveIncidents, demoIncidents, loading, error } = useIncidents()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [expandedId, setExpandedId] = useState(null)

  // Filtered incidents for the historical records list
  const filteredIncidents = useMemo(() => {
    return incidents.filter((item) => {
      const matchesSearch =
        !searchTerm ||
        item.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.location_name && item.location_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.provenance?.scene_id && item.provenance.scene_id.toLowerCase().includes(searchTerm.toLowerCase()))

      const matchesStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'LIKELY_OIL' && item.classification === 'Likely Oil') ||
        (statusFilter === 'LOOKALIKE' && item.classification === 'Likely Look-alike') ||
        (statusFilter === 'NEEDS_VERIFICATION' && item.status === 'Needs Verification') ||
        (statusFilter === 'LIVE_ONLY' && item.is_live_analysis)

      return matchesSearch && matchesStatus
    })
  }, [incidents, searchTerm, statusFilter])

  // Intelligence and metrics derived purely from actual historical records
  const metrics = useMemo(() => {
    const total = incidents.length
    const liveCount = liveIncidents?.length || 0
    const demoCount = demoIncidents?.length || 0

    const likelyOilCount = incidents.filter((i) => i.classification === 'Likely Oil').length
    const likelyLookAlikeCount = incidents.filter((i) => i.classification === 'Likely Look-alike').length
    const needsVerificationCount = incidents.filter((i) => i.status === 'Needs Verification').length

    const validConfidences = incidents
      .map((i) => i.confidence)
      .filter((c) => typeof c === 'number' && !Number.isNaN(c))
    const averageConfidence = validConfidences.length
      ? validConfidences.reduce((sum, c) => sum + c, 0) / validConfidences.length
      : 0

    const totalExtent = incidents.reduce((sum, i) => sum + (Number(i.area_km2) || 0), 0)
    const avgExtent = total > 0 ? totalExtent / total : 0

    // Classification distribution
    const byClassification = [
      { name: 'Likely Oil', value: likelyOilCount },
      { name: 'Likely Look-alike', value: likelyLookAlikeCount },
      { name: 'Insufficient Evidence', value: total - (likelyOilCount + likelyLookAlikeCount) },
    ].filter((item) => item.value > 0)

    // Review status breakdown
    const byStatus = Array.from(new Set(incidents.map((i) => i.status || 'Needs Verification'))).map(
      (status) => ({
        name: status,
        value: incidents.filter((i) => (i.status || 'Needs Verification') === status).length,
      })
    )

    // Confidence distribution bands
    const confidenceDistribution = [
      { name: '0–49%', value: incidents.filter((i) => i.confidence < 0.5).length },
      { name: '50–69%', value: incidents.filter((i) => i.confidence >= 0.5 && i.confidence < 0.7).length },
      { name: '70–84%', value: incidents.filter((i) => i.confidence >= 0.7 && i.confidence < 0.85).length },
      { name: '85–100%', value: incidents.filter((i) => i.confidence >= 0.85).length },
    ]

    // Time-series sequence grouped by date
    const dateMap = new Map()
    incidents.forEach((inc) => {
      const d = new Date(inc.detected_at || inc.provenance?.acquisition_time || 0)
      if (!Number.isNaN(d.getTime())) {
        const dateKey = new Intl.DateTimeFormat('en-US', { day: '2-digit', month: 'short', timeZone: 'UTC' }).format(d)
        dateMap.set(dateKey, (dateMap.get(dateKey) || 0) + 1)
      }
    })

    const overTime = Array.from(dateMap.entries()).map(([date, count]) => ({
      date,
      detections: count,
    }))

    // Extents per incident
    const extents = incidents
      .filter((i) => Boolean(i.area_km2))
      .map((i) => ({
        name: i.id,
        extent: Number(i.area_km2) || 0,
      }))

    // Insights statements computed dynamically from actual records
    const insightsList = []
    if (total > 0) {
      const oilPct = Math.round((likelyOilCount / total) * 100)
      insightsList.push({
        id: 1,
        title: 'Classification Distribution',
        text: `${oilPct}% of analyzed historical records (${likelyOilCount} of ${total}) were classified as oil-like features by the ML pipeline.`,
        metric: `${oilPct}% Oil-Positive`,
      })
      insightsList.push({
        id: 2,
        title: 'Surface Slick Extent Analysis',
        text: `Average detected slick extent is ${avgExtent.toFixed(2)} km² across ${total} analyzed incidents (total cumulative surface extent: ${totalExtent.toFixed(2)} km²).`,
        metric: `${totalExtent.toFixed(1)} km² Total`,
      })
      insightsList.push({
        id: 3,
        title: 'AI Model Detection Confidence',
        text: `Mean AI detection confidence across active historical observations is ${Math.round(averageConfidence * 100)}%.`,
        metric: `${Math.round(averageConfidence * 100)}% Avg Confidence`,
      })
      if (needsVerificationCount > 0) {
        insightsList.push({
          id: 4,
          title: 'Analyst Disposition Queue',
          text: `${needsVerificationCount} incident candidate record${needsVerificationCount > 1 ? 's' : ''} currently await analyst verification in the operational queue.`,
          metric: `${needsVerificationCount} Pending`,
        })
      }
      if (liveCount > 0) {
        insightsList.push({
          id: 5,
          title: 'Live Analysis Pipeline Activity',
          text: `${liveCount} live SAR image analysis result${liveCount > 1 ? 's' : ''} processed via FastAPI during this session.`,
          metric: `${liveCount} Live Executions`,
        })
      }
    }

    return {
      total,
      liveCount,
      demoCount,
      likelyOilCount,
      likelyLookAlikeCount,
      needsVerificationCount,
      averageConfidence,
      totalExtent,
      avgExtent,
      byClassification,
      byStatus,
      confidenceDistribution,
      overTime,
      extents,
      insightsList,
    }
  }, [incidents, liveIncidents, demoIncidents])

  if (loading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-[#1d4b3b]">
        <Clock3 className="animate-spin" size={24} />
        <p className="text-sm font-medium">Loading historical operational records…</p>
      </div>
    )
  }

  if (error) {
    return <p className="p-8 text-rose-600 font-semibold">Unable to load historical operational records.</p>
  }

  const hasTrendData = metrics.total > 0

  return (
    <div className="space-y-8 text-[#4d3328]">
      {/* Header Banner */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[#e6c8b5] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold tracking-[.18em] text-[#1d4b3b]">
              HISTORICAL OPERATIONAL DATA & INTELLIGENCE
            </span>
            {metrics.liveCount > 0 && (
              <span className="flex items-center gap-1 rounded-full bg-emerald-700 px-2.5 py-0.5 text-[10px] font-bold text-white">
                <Zap size={10} /> {metrics.liveCount} LIVE STORED
              </span>
            )}
          </div>
          <h1 className="mt-1 font-serif text-3xl font-bold text-[#663520]">Incident & Analysis History</h1>
          <p className="mt-1 text-xs text-[#735247]">
            Central repository of previous SAR scene analyses, spill detection records, vessel investigations, historical trends, and evidence-derived analytics.
          </p>
        </div>

        {/* Filter / Search Bar */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-[#8a685c]" size={14} />
            <input
              type="text"
              placeholder="Search ID, location, or scene…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="rounded-xl border border-[#d6b9a7] bg-white pl-9 pr-3 py-1.5 text-xs text-[#4d3328] placeholder-[#a68678] focus:border-[#1d4b3b] focus:outline-none shadow-sm"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-xl border border-[#d6b9a7] bg-white px-3 py-1.5 text-xs font-medium text-[#4d3328] focus:border-[#1d4b3b] focus:outline-none shadow-sm"
          >
            <option value="ALL">All Classifications ({metrics.total})</option>
            <option value="LIKELY_OIL">Likely Oil ({metrics.likelyOilCount})</option>
            <option value="LOOKALIKE">Likely Look-alike ({metrics.likelyLookAlikeCount})</option>
            <option value="NEEDS_VERIFICATION">Needs Verification ({metrics.needsVerificationCount})</option>
            {metrics.liveCount > 0 && <option value="LIVE_ONLY">Live FastAPI Records ({metrics.liveCount})</option>}
          </select>
        </div>
      </div>

      {/* =========================================================================
          SECTION 1: HISTORICAL INCIDENTS & PAST SAR ANALYSES
          ========================================================================= */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="text-[#1d4b3b]" size={20} />
            <h2 className="font-serif text-xl font-bold text-[#663520]">
              Historical Incidents & Analyses ({filteredIncidents.length})
            </h2>
          </div>
          <span className="text-xs text-[#735247]">
            Showing {filteredIncidents.length} of {metrics.total} recorded incidents
          </span>
        </div>

        {filteredIncidents.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#e6c8b5] bg-white p-8 text-center text-[#735247]">
            <Info className="mx-auto mb-2 text-[#8a685c]" size={24} />
            <p className="font-semibold text-sm text-[#663520]">No historical records match the selected search criteria.</p>
            <p className="mt-1 text-xs text-[#735247]">Try adjusting your search terms or status filter.</p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filteredIncidents.map((incident) => {
              const isExpanded = expandedId === incident.id
              const isLive = Boolean(incident.is_live_analysis)

              return (
                <article
                  key={incident.id}
                  className={`rounded-2xl border transition shadow-sm ${
                    isLive ? 'border-emerald-300 bg-emerald-50/40' : 'border-[#e6c8b5] bg-white'
                  }`}
                >
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-[#663520]">{incident.id}</span>
                      <span
                        className={`rounded px-2 py-0.5 text-[9px] font-bold ${
                          isLive
                            ? 'bg-emerald-700 text-white'
                            : 'bg-[#735247]/15 text-[#663520]'
                        }`}
                      >
                        {isLive ? 'LIVE ML ANALYSIS' : 'HISTORICAL STORED'}
                      </span>
                    </div>

                    <h4 className="mt-2 flex items-center gap-1.5 font-bold text-[#4d3328]">
                      <MapPin size={15} className="shrink-0 text-[#1d4b3b]" />
                      <span className="truncate">{incident.location_name || 'Geospatial Coordinates'}</span>
                    </h4>

                    <p className="mt-1 flex items-center gap-1 text-xs text-[#735247]">
                      <Clock3 size={13} className="shrink-0 text-[#8a685c]" />
                      {formatTime(incident.detected_at || incident.provenance?.acquisition_time)}
                    </p>

                    <div className="mt-3 grid grid-cols-2 gap-2 rounded-xl bg-[#fffaf6] p-2.5 text-[11px] border border-[#f0ddd1]">
                      <div>
                        <span className="text-[#8a685c]">Classification</span>
                        <p className="font-bold text-[#1d4b3b]">{incident.classification || 'Unclassified'}</p>
                      </div>
                      <div>
                        <span className="text-[#8a685c]">AI Confidence</span>
                        <p className="font-bold text-[#663520]">
                          {typeof incident.confidence === 'number'
                            ? `${Math.round(incident.confidence * 100)}%`
                            : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <span className="text-[#8a685c]">Slick Area</span>
                        <p className="font-semibold text-[#4d3328]">
                          {incident.area_km2 ? `${incident.area_km2} km²` : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <span className="text-[#8a685c]">Status</span>
                        <p className="font-semibold text-[#4d3328]">{incident.status || 'Needs Verification'}</p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setExpandedId(isExpanded ? null : incident.id)}
                      className="mt-3 flex w-full items-center justify-between rounded-lg border border-[#e6c8b5] bg-white px-3 py-1.5 text-xs font-semibold text-[#663520] transition hover:bg-[#fffaf6]"
                    >
                      <span>{isExpanded ? 'Hide Details' : 'View Full Record & Provenance'}</span>
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </div>

                  {/* Expanded Record Details */}
                  {isExpanded && (
                    <div className="border-t border-[#f0ddd1] bg-[#fffaf6] p-4 text-xs space-y-2 rounded-b-2xl">
                      <p className="font-bold text-[10px] tracking-wider text-[#1d4b3b]">SATELLITE & PROVENANCE METADATA</p>
                      <div className="space-y-1 text-[11px]">
                        <div className="flex justify-between">
                          <span className="text-[#735247]">Scene ID:</span>
                          <span className="font-mono text-[#4d3328] truncate max-w-[180px]">
                            {incident.provenance?.scene_id || 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#735247]">SAR Platform:</span>
                          <span className="text-[#4d3328]">{incident.sar?.platform || 'Sentinel-1 SAR'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#735247]">Polarization:</span>
                          <span className="text-[#4d3328]">{incident.sar?.polarization || 'VV/VH'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#735247]">Model Version:</span>
                          <span className="text-[#4d3328]">{incident.provenance?.model_version || 'YOLO11n-oil-slick'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#735247]">Attributed Vessels:</span>
                          <span className="font-semibold text-[#1d4b3b]">
                            {incident.vessels?.length || 0} candidate vessel(s)
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </article>
              )
            })}
          </div>
        )}
      </section>

      {/* =========================================================================
          SECTION 2: HISTORICAL TRENDS
          ========================================================================= */}
      <section className="space-y-4 pt-4 border-t border-[#e6c8b5]">
        <div className="flex items-center gap-2">
          <Activity className="text-[#1d4b3b]" size={20} />
          <div>
            <h2 className="font-serif text-xl font-bold text-[#663520]">Historical Trends</h2>
            <p className="text-xs text-[#735247]">Visualizations derived from stored incident observations</p>
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          {/* Trend 1: Detection Sequence over Time */}
          <Panel
            title="Detections Over Time"
            subtitle="Historical candidate acquisition volume grouped by acquisition date"
          >
            {hasTrendData && metrics.overTime.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={metrics.overTime} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="histGradient" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="#1d4b3b" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#1d4b3b" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid vertical={false} stroke="#f0ddd1" />
                    <XAxis dataKey="date" tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area type="monotone" dataKey="detections" stroke="#1d4b3b" strokeWidth={2.5} fill="url(#histGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyTrendNotice />
            )}
          </Panel>

          {/* Trend 2: Classification Breakdown */}
          <Panel
            title="Oil-Positive vs Lookalike Breakdown"
            subtitle="Distribution of AI ML classifications across historical records"
          >
            {hasTrendData && metrics.byClassification.length > 0 ? (
              <div className="space-y-3">
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={metrics.byClassification}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={55}
                        outerRadius={85}
                        paddingAngle={4}
                      >
                        {metrics.byClassification.map((entry, index) => (
                          <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<ChartTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-wrap justify-center gap-4 text-xs text-[#735247]">
                  {metrics.byClassification.map((item, index) => (
                    <span key={item.name} className="flex items-center gap-1.5">
                      <i
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ background: CHART_COLORS[index % CHART_COLORS.length] }}
                      />
                      {item.name}: <strong className="text-[#4d3328]">{item.value}</strong>
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyTrendNotice />
            )}
          </Panel>

          {/* Trend 3: Detection Confidence Distribution */}
          <Panel
            title="Detection Confidence Bands"
            subtitle="Distribution of AI detection confidence scores"
          >
            {hasTrendData ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics.confidenceDistribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid vertical={false} stroke="#f0ddd1" />
                    <XAxis dataKey="name" tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="value" name="Candidates" radius={[6, 6, 0, 0]} fill="#1d4b3b" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyTrendNotice />
            )}
          </Panel>

          {/* Trend 4: Surface Slick Extent Distribution */}
          <Panel
            title="Surface Slick Area Distribution (km²)"
            subtitle="Surface extent by historical incident candidate"
          >
            {hasTrendData && metrics.extents.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics.extents} layout="vertical" margin={{ top: 5, right: 15, left: 15, bottom: 0 }}>
                    <CartesianGrid horizontal={false} stroke="#f0ddd1" />
                    <XAxis type="number" tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis dataKey="name" type="category" tick={{ fill: '#735247', fontSize: 11 }} axisLine={false} tickLine={false} width={70} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="extent" name="km²" radius={[0, 6, 6, 0]} fill="#663520" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyTrendNotice />
            )}
          </Panel>
        </div>
      </section>

      {/* =========================================================================
          SECTION 3: ANALYTICS SUMMARY
          ========================================================================= */}
      <section className="space-y-4 pt-4 border-t border-[#e6c8b5]">
        <div className="flex items-center gap-2">
          <BarChart3 className="text-[#1d4b3b]" size={20} />
          <div>
            <h2 className="font-serif text-xl font-bold text-[#663520]">Analytics Metrics</h2>
            <p className="text-xs text-[#735247]">Quantitative summary derived from actual recorded backend incidents</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <Card
            icon={Activity}
            label="TOTAL INCIDENTS"
            value={metrics.total}
            note={`${metrics.liveCount} Live FastAPI · ${metrics.demoCount} Historical`}
          />
          <Card
            icon={Droplets}
            label="LIKELY OIL"
            value={metrics.likelyOilCount}
            note="ML classified oil-like features"
          />
          <Card
            icon={Eye}
            label="LOOK-ALIKES"
            value={metrics.likelyLookAlikeCount}
            note="Natural / biogenic features"
          />
          <Card
            icon={ShieldCheck}
            label="DISPOSITION QUEUE"
            value={metrics.needsVerificationCount}
            note="Awaiting analyst verification"
          />
          <Card
            icon={Sparkles}
            label="AVG CONFIDENCE"
            value={`${Math.round(metrics.averageConfidence * 100)}%`}
            note="Across evaluated scenes"
          />
          <Card
            icon={Waves}
            label="TOTAL SLICK AREA"
            value={`${metrics.totalExtent.toFixed(1)} km²`}
            note="Cumulative detected area"
          />
        </div>
      </section>

      {/* =========================================================================
          SECTION 4: EVIDENCE-DERIVED INSIGHTS
          ========================================================================= */}
      <section className="space-y-4 pt-4 border-t border-[#e6c8b5]">
        <div className="flex items-center gap-2">
          <Sparkles className="text-[#1d4b3b]" size={20} />
          <div>
            <h2 className="font-serif text-xl font-bold text-[#663520]">Evidence-Derived Insights</h2>
            <p className="text-xs text-[#735247]">Operational statements generated strictly from historical record evaluation</p>
          </div>
        </div>

        {metrics.insightsList.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {metrics.insightsList.map((insight) => (
              <article key={insight.id} className="rounded-2xl border border-[#e6c8b5] bg-white p-5 shadow-sm space-y-2">
                <div className="flex items-center justify-between border-b border-[#f0ddd1] pb-2">
                  <h3 className="font-serif text-sm font-bold text-[#663520]">{insight.title}</h3>
                  <span className="rounded bg-[#1d4b3b]/10 px-2 py-0.5 text-[10px] font-bold text-[#1d4b3b]">
                    {insight.metric}
                  </span>
                </div>
                <p className="text-xs leading-relaxed text-[#4d3328]">{insight.text}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-[#e6c8b5] bg-white p-6 text-center text-xs text-[#735247]">
            No historical records available to generate insights.
          </div>
        )}
      </section>
    </div>
  )
}

export default History
