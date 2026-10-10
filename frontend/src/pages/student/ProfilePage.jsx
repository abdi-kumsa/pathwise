import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getStudentProfile } from '../../api/student'

export default function ProfilePage() {
  const { data, loading, error, refetch } = useFetch(getStudentProfile)
  const elig = data?.eligibility

  return (
    <div>
      <SectionHeader
        title="Your profile"
        subtitle="Programme, institution and field accessibility — used to keep recommendations realistic"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading profile…" height={240} />}
      {data && (
        <>
          <div className="kpi-grid">
            <KPICard label="Programme" value={data.program || '—'} delta={data.field} deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>} />
            <KPICard label="Department" value={data.department || '—'} delta={data.department ? data.program : 'Not on the seeded SIS record'} deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/></svg>} />
            <KPICard label="Institution" value={data.institution || '—'} delta={data.enrollment_status} deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/></svg>} />
            <KPICard label="Year of entry" value={data.enrollment_year || '—'} delta={data.display_name} deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 7V3m8 4V3M3 11h18M5 21h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2Z"/></svg>} />
            <KPICard
              label={elig?.label || 'Eligibility'}
              value={elig?.pct != null ? `${elig.pct}%` : '—'}
              delta="Field pass-rate proxy"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
          </div>
          <DataNote tone="simulated">
            {elig?.note}
            {!data.department ? ' Department is shown as — until an official SIS file carries it.' : ''}
          </DataNote>
        </>
      )}
    </div>
  )
}
