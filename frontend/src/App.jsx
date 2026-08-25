import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'

import MarketOverviewPage from './pages/MarketOverviewPage'
import HiringAnalyticsPage from './pages/HiringAnalyticsPage'
import SkillGapPage from './pages/SkillGapPage'
import RegionalOpportunityPage from './pages/RegionalOpportunityPage'
import ForecastPage from './pages/ForecastPage'

import EnrollmentForecastPage from './pages/EnrollmentForecastPage'
import AdmissionRiskPage from './pages/AdmissionRiskPage'
import PlacementByStreamPage from './pages/PlacementByStreamPage'
import StudentEvaluatorPage from './pages/StudentEvaluatorPage'

import SalaryForecastPage from './pages/SalaryForecastPage'
import EscapeRoutePage from './pages/EscapeRoutePage'
import SkillRoadmapPage from './pages/SkillRoadmapPage'

export default function App() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page)' }}>
      <Sidebar />

      <main style={{ marginLeft: '264px', flex: '1', minWidth: '0', padding: '32px 40px 56px' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/market/overview" replace />} />

          <Route path="/market/overview"  element={<MarketOverviewPage />} />
          <Route path="/market/hiring"    element={<HiringAnalyticsPage />} />
          <Route path="/market/skill-gap" element={<SkillGapPage />} />
          <Route path="/market/regional" element={<RegionalOpportunityPage />} />
          <Route path="/market/forecast"  element={<ForecastPage />} />

          <Route path="/enrollment/trends"     element={<EnrollmentForecastPage />} />
          <Route path="/enrollment/risk"       element={<AdmissionRiskPage />} />
          <Route path="/enrollment/placements" element={<PlacementByStreamPage />} />
          <Route path="/enrollment/student"    element={<StudentEvaluatorPage />} />

          <Route path="/recommendations/salary"  element={<SalaryForecastPage />} />
          <Route path="/recommendations/escape"  element={<EscapeRoutePage />} />
          <Route path="/enrollment/skill-roadmap" element={<SkillRoadmapPage />} />

          <Route path="*" element={
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: 'var(--text-muted)',
              fontSize: '16px'
            }}>
              Page not found
            </div>
          } />
        </Routes>
      </main>
    </div>
  )
}
