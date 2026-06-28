export default function EmptyState({ title = 'No data', description }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-4">
        <span className="text-slate-400 text-xl">&#8709;</span>
      </div>
      <p className="text-slate-600 font-medium">{title}</p>
      {description && (
        <p className="text-sm text-slate-400 mt-1 max-w-xs">{description}</p>
      )}
    </div>
  )
}
