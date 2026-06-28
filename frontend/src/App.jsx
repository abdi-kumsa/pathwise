import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'

function Placeholder({ title }) {
  return (
    <div className="flex items-center justify-center h-full text-slate-400 text-lg">
      {title} — coming soon
    </div>
  )
}

export default function App() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />

      <main className="ml-60 flex-1 overflow-y-auto p-8">
        <Routes>
          <Route path="/" element={<Navigate to="/market/overview" replace />} />

          {/* Module 1 — Market Demand */}
          <Route path="/market/overview"  element={<Placeholder title="Market Overview" />} />
          <Route path="/market/hiring"    element={<Placeholder title="Hiring Analytics" />} />
          <Route path="/market/skill-gap" element={<Placeholder title="Skill Gap" />} />
          <Route path="/market/forecast"  element={<Placeholder title="Forecast" />} />

          {/* Module 2 — Enrollment Intel */}
          <Route path="/enrollment/trends"     element={<Placeholder title="Enrollment Trends" />} />
          <Route path="/enrollment/risk"       element={<Placeholder title="Admission Risk" />} />
          <Route path="/enrollment/placements" element={<Placeholder title="Placements" />} />
          <Route path="/enrollment/student"    element={<Placeholder title="Student Evaluator" />} />

          <Route path="*" element={<Placeholder title="Page not found" />} />
        </Routes>
      </main>
    </div>
  )
}
