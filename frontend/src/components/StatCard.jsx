export default function StatCard({ label, value, sub, trend }) {
  const trendColor =
    trend === 'up' ? 'text-emerald-500' :
    trend === 'down' ? 'text-red-500' :
    'text-slate-400'

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
      <p className="text-sm text-slate-500 font-medium mb-1">{label}</p>
      <p className="text-3xl font-bold text-slate-800">{value}</p>
      {sub && (
        <p className={`text-xs mt-1 ${trendColor}`}>{sub}</p>
      )}
    </div>
  )
}
