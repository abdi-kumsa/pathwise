import { lazy, Suspense, useState } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'

import { AuthProvider, useAuth } from './context/AuthContext'
import RoleRoute from './components/RoleRoute'
import Sidebar from './components/Sidebar'
import CommandBar from './components/CommandBar'
import LoadingSpinner from './components/LoadingSpinner'
import { DEFAULT_PROVENANCE } from './hooks/useProvenance'
import usePageView from './hooks/usePageView'

import LoginPage from './pages/LoginPage'
import SignUpPage from './pages/SignUpPage'
import AccountPage from './pages/AccountPage'

// Student
import CareerExplorerPage from './pages/student/CareerExplorerPage'
import SkillRoadmapPage from './pages/SkillRoadmapPage'
import EscapeRoutePage from './pages/EscapeRoutePage'
import ProfilePage from './pages/student/ProfilePage'
import LabourOutlookPage from './pages/student/LabourOutlookPage'
import DemandComparisonPage from './pages/student/DemandComparisonPage'
import FieldAlignmentPage from './pages/student/FieldAlignmentPage'
import SupplyDemandGapPage from './pages/student/SupplyDemandGapPage'
import PathwayMapPage from './pages/student/PathwayMapPage'
import OpportunitiesPage from './pages/student/OpportunitiesPage'

// Ministry of Labour
import LabourOverviewPage from './pages/mol/LabourOverviewPage'
import EmergingOccupationsPage from './pages/mol/EmergingOccupationsPage'
import SupplyDemandPage from './pages/mol/SupplyDemandPage'
import SkillsMismatchPage from './pages/mol/SkillsMismatchPage'
import RegionalDemandPage from './pages/mol/RegionalDemandPage'
import FormalInformalPage from './pages/mol/FormalInformalPage'
import SectorForecastPage from './pages/mol/SectorForecastPage'
import PublicHiringPage from './pages/mol/PublicHiringPage'
import FdiPipelinePage from './pages/mol/FdiPipelinePage'
import GraduateAbsorptionPage from './pages/mol/GraduateAbsorptionPage'
import MigrationPage from './pages/mol/MigrationPage'
import WorkforceReportPage from './pages/mol/WorkforceReportPage'

// Ministry of Education
import EducationOverviewPage from './pages/moe/EducationOverviewPage'
import InvestmentQuadrantPage from './pages/moe/InvestmentQuadrantPage'
import InvestmentPriorityPage from './pages/moe/InvestmentPriorityPage'
import FieldExplorerPage from './pages/moe/FieldExplorerPage'
import ConstraintComparisonPage from './pages/moe/ConstraintComparisonPage'
import NationalGapPage from './pages/moe/NationalGapPage'
import PolicySimulatorPage from './pages/moe/PolicySimulatorPage'
import RegionalAlignmentPage from './pages/moe/RegionalAlignmentPage'
import InstitutionComparisonPage from './pages/moe/InstitutionComparisonPage'
import PolicyImpactPage from './pages/moe/PolicyImpactPage'

// University
import InstitutionOverviewPage from './pages/university/InstitutionOverviewPage'
import ProgramPortfolioPage from './pages/university/ProgramPortfolioPage'
import ExpansionPage from './pages/university/ExpansionPage'
import ResourceEfficiencyPage from './pages/university/ResourceEfficiencyPage'
import PeerBenchmarkPage from './pages/university/PeerBenchmarkPage'
import DemandForecastPage from './pages/university/DemandForecastPage'
import ConstrainedForecastPage from './pages/university/ConstrainedForecastPage'
import ThreeWayComparisonPage from './pages/university/ThreeWayComparisonPage'
import FunnelPage from './pages/university/FunnelPage'
import CohortProgressionPage from './pages/university/CohortProgressionPage'
import GraduateOutcomesPage from './pages/university/GraduateOutcomesPage'
import CurriculumAlignmentPage from './pages/university/CurriculumAlignmentPage'

// Admin
import AdminOverviewPage from './pages/admin/AdminOverviewPage'
import AdminMonitoringPage from './pages/admin/AdminMonitoringPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import AdminPipelinePage from './pages/admin/AdminPipelinePage'
import AdminDataQualityPage from './pages/admin/AdminDataQualityPage'
import AdminMethodologyPage from './pages/admin/AdminMethodologyPage'
import AdminScenariosPage from './pages/admin/AdminScenariosPage'
import AdminAuditLogPage from './pages/admin/AdminAuditLogPage'

// Leftover US-model pages (waiver WV.US1): placement evaluator, salary,
// Prophet market demand and LSTM enrolment. Their API routes are off unless the
// backend runs with LEGACY_US_MODELS=1, so the pages are only routed when the
// build sets VITE_LEGACY_US_MODELS=true. Lazy imports keep them out of the
// default bundle entirely.
const LEGACY_US_MODELS = import.meta.env.VITE_LEGACY_US_MODELS === 'true'
// Behind the flag so the default build emits no chunk for them at all.
const legacyPage = (load) => (LEGACY_US_MODELS ? lazy(load) : null)
const StudentEvaluatorPage   = legacyPage(() => import('./pages/StudentEvaluatorPage'))
const SalaryForecastPage     = legacyPage(() => import('./pages/SalaryForecastPage'))
const MarketOverviewPage     = legacyPage(() => import('./pages/MarketOverviewPage'))
const EnrollmentForecastPage = legacyPage(() => import('./pages/EnrollmentForecastPage'))

function Legacy({ children }) {
  return <Suspense fallback={<LoadingSpinner message="Loading…" height={320} />}>{children}</Suspense>
}

// Injected by vite.config.js from VITE_BUILD_SHA, the host's git commit, or 'dev'.
const BUILD = typeof __BUILD_SHA__ === 'string' ? __BUILD_SHA__ : 'dev'

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
  usePageView()

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
        </div>

        {/* key on pathname so a page never shows the previous page's state */}
        <div key={location.pathname}>{children}</div>

        <footer className="app-footer">
          <span>
            {DEFAULT_PROVENANCE.source}, {DEFAULT_PROVENANCE.as_of}. Not official MoE, MoLS or ESS statistics.
          </span>
          <span>Build {BUILD}</span>
        </footer>
      </main>
    </div>
  )
}

/** `/` sends each role to its own landing page, decided by the API. */
function HomeRedirect() {
  const { user, booting } = useAuth()
  if (booting) return <LoadingSpinner message="Loading…" height={320} />
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.home ?? '/student/profile'} replace />
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
      <Route path="/student/careers"            element={<Protected allow={STUDENT}><CareerExplorerPage /></Protected>} />
      <Route path="/student/skill-roadmap"      element={<Protected allow={STUDENT}><SkillRoadmapPage /></Protected>} />
      <Route path="/student/alternatives"       element={<Protected allow={STUDENT}><EscapeRoutePage /></Protected>} />
      <Route path="/student/profile"            element={<Protected allow={STUDENT}><ProfilePage /></Protected>} />
      <Route path="/student/outlook"            element={<Protected allow={STUDENT}><LabourOutlookPage /></Protected>} />
      <Route path="/student/demand-comparison"  element={<Protected allow={STUDENT}><DemandComparisonPage /></Protected>} />
      <Route path="/student/alignment"          element={<Protected allow={STUDENT}><FieldAlignmentPage /></Protected>} />
      <Route path="/student/gap"                element={<Protected allow={STUDENT}><SupplyDemandGapPage /></Protected>} />
      <Route path="/student/pathways"           element={<Protected allow={STUDENT}><PathwayMapPage /></Protected>} />
      <Route path="/student/opportunities"      element={<Protected allow={STUDENT}><OpportunitiesPage /></Protected>} />

      {/* ── Ministry of Labour ───────────────────────────────────────────── */}
      <Route path="/mol/overview"         element={<Protected allow={MOL}><LabourOverviewPage /></Protected>} />
      <Route path="/mol/emerging"         element={<Protected allow={MOL}><EmergingOccupationsPage /></Protected>} />
      <Route path="/mol/supply-demand"    element={<Protected allow={MOL_OR_MOE}><SupplyDemandPage /></Protected>} />
      <Route path="/mol/mismatch"         element={<Protected allow={MOL_OR_MOE}><SkillsMismatchPage /></Protected>} />
      <Route path="/mol/regional"         element={<Protected allow={MOL}><RegionalDemandPage /></Protected>} />
      <Route path="/mol/occupations"      element={<Protected allow={MOL}><EmergingOccupationsPage /></Protected>} />
      <Route path="/mol/formal-informal"  element={<Protected allow={MOL}><FormalInformalPage /></Protected>} />
      <Route path="/mol/forecast"         element={<Protected allow={MOL}><SectorForecastPage /></Protected>} />
      <Route path="/mol/public"           element={<Protected allow={MOL}><PublicHiringPage /></Protected>} />
      <Route path="/mol/fdi"              element={<Protected allow={MOL}><FdiPipelinePage /></Protected>} />
      <Route path="/mol/absorption"       element={<Protected allow={MOL}><GraduateAbsorptionPage /></Protected>} />
      <Route path="/mol/migration"        element={<Protected allow={MOL}><MigrationPage /></Protected>} />
      <Route path="/mol/report"           element={<Protected allow={MOL}><WorkforceReportPage /></Protected>} />

      {/* ── Ministry of Education ────────────────────────────────────────── */}
      <Route path="/moe/overview"      element={<Protected allow={MOE}><EducationOverviewPage /></Protected>} />
      <Route path="/moe/quadrant"      element={<Protected allow={MOE}><InvestmentQuadrantPage /></Protected>} />
      <Route path="/moe/priorities"    element={<Protected allow={MOE}><InvestmentPriorityPage /></Protected>} />
      <Route path="/moe/fields"        element={<Protected allow={MOE}><FieldExplorerPage /></Protected>} />
      <Route path="/moe/labour"        element={<Protected allow={MOE}><SupplyDemandPage /></Protected>} />
      <Route path="/moe/constraints"   element={<Protected allow={MOE}><ConstraintComparisonPage /></Protected>} />
      <Route path="/moe/gap"           element={<Protected allow={MOE}><NationalGapPage /></Protected>} />
      <Route path="/moe/simulator"     element={<Protected allow={MOE}><PolicySimulatorPage /></Protected>} />
      <Route path="/moe/regions"       element={<Protected allow={MOE}><RegionalAlignmentPage /></Protected>} />
      <Route path="/moe/institutions"  element={<Protected allow={MOE}><InstitutionComparisonPage /></Protected>} />
      <Route path="/moe/impact"        element={<Protected allow={MOE}><PolicyImpactPage /></Protected>} />

      {/* ── University ───────────────────────────────────────────────────── */}
      <Route path="/university/overview"     element={<Protected allow={UNIVERSITY}><InstitutionOverviewPage /></Protected>} />
      <Route path="/university/portfolio"    element={<Protected allow={UNIVERSITY}><ProgramPortfolioPage /></Protected>} />
      <Route path="/university/expansion"    element={<Protected allow={UNIVERSITY}><ExpansionPage /></Protected>} />
      <Route path="/university/resources"    element={<Protected allow={UNIVERSITY}><ResourceEfficiencyPage /></Protected>} />
      <Route path="/university/benchmark"    element={<Protected allow={UNIVERSITY}><PeerBenchmarkPage /></Protected>} />
      <Route path="/university/demand"       element={<Protected allow={UNIVERSITY}><DemandForecastPage /></Protected>} />
      <Route path="/university/constrained"  element={<Protected allow={UNIVERSITY}><ConstrainedForecastPage /></Protected>} />
      <Route path="/university/three-way"    element={<Protected allow={UNIVERSITY}><ThreeWayComparisonPage /></Protected>} />
      <Route path="/university/funnel"       element={<Protected allow={UNIVERSITY}><FunnelPage /></Protected>} />
      <Route path="/university/cohort"       element={<Protected allow={UNIVERSITY}><CohortProgressionPage /></Protected>} />
      <Route path="/university/outcomes"     element={<Protected allow={UNIVERSITY}><GraduateOutcomesPage /></Protected>} />
      <Route path="/university/curriculum"   element={<Protected allow={UNIVERSITY}><CurriculumAlignmentPage /></Protected>} />

      {/* ── Leftover US-model tools (VITE_LEGACY_US_MODELS=true only) ────── */}
      {LEGACY_US_MODELS && (
        <>
          <Route path="/student/evaluator"      element={<Protected allow={STUDENT}><Legacy><StudentEvaluatorPage /></Legacy></Protected>} />
          <Route path="/student/salary"         element={<Protected allow={STUDENT}><Legacy><SalaryForecastPage /></Legacy></Protected>} />
          <Route path="/student/market"         element={<Protected allow={STUDENT}><Legacy><MarketOverviewPage /></Legacy></Protected>} />
          <Route path="/university/enrollment"  element={<Protected allow={UNIVERSITY}><Legacy><EnrollmentForecastPage /></Legacy></Protected>} />
        </>
      )}

      {/* ── Admin ────────────────────────────────────────────────────────── */}
      <Route path="/admin/overview"     element={<Protected allow={ADMIN}><AdminOverviewPage /></Protected>} />
      <Route path="/admin/pipeline"     element={<Protected allow={ADMIN}><AdminPipelinePage /></Protected>} />
      <Route path="/admin/quality"      element={<Protected allow={ADMIN}><AdminDataQualityPage /></Protected>} />
      <Route path="/admin/monitoring"   element={<Protected allow={ADMIN}><AdminMonitoringPage /></Protected>} />
      <Route path="/admin/methodology"  element={<Protected allow={ADMIN}><AdminMethodologyPage /></Protected>} />
      <Route path="/admin/scenarios"    element={<Protected allow={ADMIN}><AdminScenariosPage /></Protected>} />
      <Route path="/admin/audit"        element={<Protected allow={ADMIN}><AdminAuditLogPage /></Protected>} />
      <Route path="/admin/users"        element={<Protected allow={ADMIN}><AdminUsersPage /></Protected>} />

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
