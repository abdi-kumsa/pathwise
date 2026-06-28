export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
      <span className="mt-0.5 shrink-0">&#9888;</span>
      <div className="flex-1">
        <p className="font-medium">Something went wrong</p>
        {message && <p className="text-red-600 mt-0.5">{message}</p>}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="shrink-0 text-red-600 underline hover:text-red-800 text-xs"
        >
          Retry
        </button>
      )}
    </div>
  )
}
