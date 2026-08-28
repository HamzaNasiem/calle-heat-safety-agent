import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Sites from './pages/Sites'
import Workers from './pages/Workers'
import ErrorBoundary from './components/ErrorBoundary'
import ThermaShiftLogo from './components/ThermaShiftLogo'

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation()
  const active = location.pathname === to
  return (
    <Link
      to={to}
      className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all shrink-0 select-none ${
        active
          ? 'bg-[#141414] text-white shadow-sm'
          : 'text-slate-600 hover:text-[#141414] hover:bg-slate-200/60'
      }`}
    >
      {children}
    </Link>
  )
}

function Header() {
  return (
    <header className="bg-[#ffffff] border-b border-[#e5e5e5] sticky top-0 z-[1100] shadow-sm backdrop-blur-md bg-opacity-95">
      <div className="max-w-[1600px] mx-auto px-3 sm:px-6">
        {/* Main Header Bar */}
        <div className="h-13 sm:h-14 flex items-center justify-between gap-2">
          {/* Custom Brand Logo */}
          <Link to="/" className="hover:opacity-90 transition-opacity">
            <ThermaShiftLogo size="md" />
          </Link>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1 bg-[#f4f4f4] p-1 rounded-xl border border-[#e5e5e5]">
            <NavLink to="/">Mission Control</NavLink>
            <NavLink to="/sites">Work Sites</NavLink>
            <NavLink to="/workers">Field Workforce</NavLink>
          </nav>

          {/* Live System Badge */}
          <div className="flex items-center gap-1.5 text-xs text-rose-700 font-medium bg-rose-50 px-2.5 py-1.5 sm:px-3 rounded-xl border border-rose-200 shrink-0">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping shrink-0" />
            <span className="text-[10px] sm:text-[11px] text-rose-900 font-bold whitespace-nowrap">
              <span className="hidden sm:inline">CALL-E </span>Voice AI Online
            </span>
          </div>
        </div>

        {/* Mobile Navigation Sub-Bar (Scrollable Pills with No-Scrollbar) */}
        <div className="md:hidden pb-2 pt-1 border-t border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          <nav className="flex items-center gap-1 bg-[#f4f4f4] p-1 rounded-xl border border-[#e5e5e5] w-full justify-between">
            <NavLink to="/">Mission Control</NavLink>
            <NavLink to="/sites">Work Sites</NavLink>
            <NavLink to="/workers">Workforce</NavLink>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#f4f4f4] text-[#141414] flex flex-col font-sans selection:bg-emerald-100 selection:text-emerald-900 w-full max-w-full overflow-x-hidden">
        <Header />
        <main className="flex-1 max-w-[1600px] w-full mx-auto px-3 sm:px-6 py-3 sm:py-5 overflow-x-hidden">
          <ErrorBoundary fallbackTitle="System Component Error">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/sites" element={<Sites />} />
              <Route path="/workers" element={<Workers />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </BrowserRouter>
  )
}
