import { Activity, Satellite, Ship, Wind, Zap } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'
import { liveAnalysisStorage } from '../../services/liveAnalysisStorage'

const navigation = [
  { to: '/', label: 'Operations', icon: Activity },
  { to: '/vessels', label: 'Vessel Intelligence', icon: Ship },
  { to: '/environment', label: 'Environmental Response', icon: Wind },
]

function AppLayout() {
  const liveAnalyses = liveAnalysisStorage.getLiveAnalysesList()
  const liveCount = liveAnalyses.length

  return (
    <div className="min-h-screen bg-[#f0f6fb] text-[#4d3328]">
      {/* Header */}
      <header className="border-b border-[#1a3a50] bg-[#071d2f] px-5 py-3 text-[#c8dcea]">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-full border-2 border-[#4db6e8] text-[#4db6e8]">
              <Satellite size={20} />
            </div>
            <div>
              <p className="text-base font-bold tracking-wider text-[#e8f4fb]">BLUETRACE</p>
              <p className="text-[10px] tracking-widest text-[#4db6e8]">MARITIME OPERATIONS</p>
            </div>
          </div>

          {/* Nav */}
          <nav className="order-3 flex w-full gap-1 sm:order-2 sm:w-auto">
            {navigation.map(({ to, label, icon: Icon }) => (
              <NavLink
                end={to === '/'}
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold transition ${
                    isActive
                      ? 'bg-[#1a6b9a] text-white'
                      : 'text-[#8ab8d4] hover:bg-[#0f2d44] hover:text-[#e8f4fb]'
                  }`
                }
              >
                <Icon size={14} />
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Status pill */}
          <div
            className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-[10px] font-bold tracking-widest ${
              liveCount > 0
                ? 'border-emerald-600 bg-emerald-900/40 text-emerald-300'
                : 'border-[#1a3a50] bg-[#0d2538] text-[#4db6e8]'
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                liveCount > 0 ? 'bg-emerald-400' : 'bg-[#4db6e8]'
              }`}
            />
            {liveCount > 0 ? (
              <span className="flex items-center gap-1">
                <Zap size={10} /> {liveCount} LIVE RESULT{liveCount > 1 ? 'S' : ''}
              </span>
            ) : (
              'SYSTEM CONNECTED'
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-[1600px] p-4 lg:p-5">
        <Outlet />
      </main>
    </div>
  )
}

export default AppLayout
