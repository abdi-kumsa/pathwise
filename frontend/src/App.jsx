import { useState } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'

import { AuthProvider, useAuth } from './context/AuthContext'
import RoleRoute from './components/RoleRoute'
import Sidebar from './components/Sidebar'
import CommandBar from './components/CommandBar'
import LoadingSpinner from './components/LoadingSpinner'

import LoginPage from './pages/LoginPage'
import SignUpPage from './pages/SignUpPage'
import AccountPage from './pages/AccountPage'

// Student
import CareerExplorerPage from './pages/student/CareerExplorerPage'
import StudentEvaluatorPage from './pages/StudentEvaluatorPage'
import SkillRoadmapPage from './pages/SkillRoadmapPage'
import EscapeRoutePage from './pages/EscapeRoutePage'
import SalaryForecastPage from './pages/SalaryForecastPage'
import MarketOverviewPage from './pages/MarketOverviewPage'

// Ministry of Labour
import LabourOverviewPage from './pages/mol/LabourOverviewPage'
import EmergingOccupationsPage from './pages/mol/EmergingOccupationsPage'
import SupplyDemandPage from './pages/mol/SupplyDemandPage'
import SkillsMismatchPage from './pages/mol/SkillsMismatchPage'
import RegionalDemandPage from './pages/mol/RegionalDemandPage'

// Ministry of Education
import EducationOverviewPage from './pages/moe/EducationOverviewPage'
import InvestmentQuadrantPage from './pages/moe/InvestmentQuadrantPage'
import InvestmentPriorityPage from './pages/moe/InvestmentPriorityPage'
import FieldExplorerPage from './pages/moe/FieldExplorerPage'

// University
import InstitutionOverviewPage from './pages/university/InstitutionOverviewPage'
import ProgramPortfolioPage from './pages/university/ProgramPortfolioPage'
import ExpansionPage from './pages/university/ExpansionPage'
import ResourceEfficiencyPage from './pages/university/ResourceEfficiencyPage'
import PeerBenchmarkPage from './pages/university/PeerBenchmarkPage'
import EnrollmentForecastPage from './pages/EnrollmentForecastPage'

// Admin
import AdminOverviewPage from './pages/admin/AdminOverviewPage'
import AdminMonitoringPage from './pages/admin/AdminMonitoringPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'

const STUDENT    = ['STUDENT']
const MOL        = ['MOL', 'ADMIN']
const MOE        = ['MOE', 'ADMIN']
const MOL_OR_MOE = ['MOL', 'MOE', 'ADMIN']
const UNIVERSITY = ['UNIVERSITY', 'ADMIN']
const ADMIN      = ['ADMIN']

/** Signed-in chrome: sidebar, top bar, command bar, routed page. */
function Shell({ children }) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="app-shell">
      <Sidebar open={drawerOpen} onClose={() => setDrawerOpen(false)} />

      <main className="app-main">
        <div className="topbar">
          <button
            className="topbar-burger"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                 strokeLinecap="round">
              <path d="M3 6h18M3 12h18M3 18h18" />
            </svg>
          </button>

          <CommandBar />

          <span className="provenance-chip">US benchmark dataset · 2020–2025</span>
        </div>

        {/* key on pathname so a page never shows the previous page's state */}
        <div key={location.pathname}>{children}</div>
      </main>
    </div>
  )
}

/** `/` sends each role to its own landing page, decided by the API. */
function HomeRedirect() {
  const { user, booting } = useAuth()
  if (booting) return <LoadingSpinner message="Loading…" height={320} />
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.home ?? '/student/careers'} replace />
}

function Protected({ allow, children }) {
  return (
    <RoleRoute allow={allow}>
      <Shell>{children}</Shell>
    </RoleRoute>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignUpPage />} />
      <Route path="/" element={<HomeRedirect />} />

      {/* Own account — every signed-in role, no allow list */}
      <Route path="/account" element={<Protected><AccountPage /></Protected>} />

      {/* ── Student ──────────────────────────────────────────────────────── */}
      <Route path="/student/careers"        element={<Protected allow={STUDENT}><CareerExplorerPage /></Protected>} />
      <Route path="/student/evaluator"      element={<Protected allow={STUDENT}><StudentEvaluatorPage /></Protected>} />
      <Route path="/student/skill-roadmap"  element={<Protected allow={STUDENT}><SkillRoadmapPage /></Protected>} />
      <Route path="/student/alternatives"   element={<Protected allow={STUDENT}><EscapeRoutePage /></Protected>} />
      <Route path="/student/salary"         element={<Protected allow={STUDENT}><SalaryForecastPage /></Protected>} />
      <Route path="/student/market"         element={<Protected allow={STUDENT}><MarketOverviewPage /></Protected>} />

      {/* ── Ministry of Labour ───────────────────────────────────────────── */}
      <Route path="/mol/overview"      element={<Protected allow={MOL}><LabourOverviewPage /></Protected>} />
      <Route path="/mol/emerging"      element={<Protected allow={MOL}><EmergingOccupationsPage /></Protected>} />
      <Route path="/mol/supply-demand" element={<Protected allow={MOL_OR_MOE}><SupplyDemandPage /></Protected>} />
      <Route path="/mol/mismatch"      element={<Protected allow={MOL_OR_MOE}><SkillsMismatchPage /></Protected>} />
      <Route path="/mol/regional"      element={<Protected allow={MOL}><RegionalDemandPage /></Protected>} />
      <Route path="/mol/occupations"   element={<Protected allow={MOL}><EmergingOccupationsPage /></Protected>} />

      {/* ── Ministry of Education ────────────────────────────────────────── */}
      <Route path="/moe/overview"   element={<Protected allow={MOE}><EducationOverviewPage /></Protected>} />
      <Route path="/moe/quadrant"   element={<Protected allow={MOE}><InvestmentQuadrantPage /></Protected>} />
      <Route path="/moe/priorities" element={<Protected allow={MOE}><InvestmentPriorityPage /></Protected>} />
      <Route path="/moe/fields"     element={<Protected allow={MOE}><FieldExplorerPage /></Protected>} />
      {/* MoE reads labour demand too — it is the input to their decisions */}
      <Route path="/moe/labour"     element={<Protected allow={MOE}><SupplyDemandPage /></Protected>} />

      {/* ── University ───────────────────────────────────────────────────── */}
      <Route path="/university/overview"    element={<Protected allow={UNIVERSITY}><InstitutionOverviewPage /></Protected>} />
      <Route path="/university/portfolio"   element={<Protected allow={UNIVERSITY}><ProgramPortfolioPage /></Protected>} />
      <Route path="/university/expansion"   element={<Protected allow={UNIVERSITY}><ExpansionPage /></Protected>} />
      <Route path="/university/resources"   element={<Protected allow={UNIVERSITY}><ResourceEfficiencyPage /></Protected>} />
      <Route path="/university/benchmark"   element={<Protected allow={UNIVERSITY}><PeerBenchmarkPage /></Protected>} />
      <Route path="/university/enrollment"  element={<Protected allow={UNIVERSITY}><EnrollmentForecastPage /></Protected>} />

      {/* ── Admin ────────────────────────────────────────────────────────── */}
      <Route path="/admin/overview"   element={<Protected allow={ADMIN}><AdminOverviewPage /></Protected>} />
      <Route path="/admin/monitoring" element={<Protected allow={ADMIN}><AdminMonitoringPage /></Protected>} />
      <Route path="/admin/users"      element={<Protected allow={ADMIN}><AdminUsersPage /></Protected>} />

      <Route path="*" element={
        <Protected>
          <div style={{ padding: '64px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
            <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--navy)', marginBottom: 6 }}>
              Page not found
            </p>
            <p style={{ fontSize: '13px' }}>
              This page may belong to a different role. Use the sidebar to get back.
            </p>
          </div>
        </Protected>
      } />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
