import { Citation } from '../types'

function severityBadgeClass(sev: string): string {
  switch (sev) {
    case 'P1':
      return 'bg-red-600 text-white'
    case 'P2':
      return 'bg-orange-500 text-white'
    case 'P3':
      return 'bg-yellow-400 text-yellow-950'
    case 'P4':
    default:
      return 'bg-slate-400 text-white dark:bg-slate-600'
  }
}

export function CitationsPanel({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) {
    return (
      <aside className="flex h-full w-80 flex-col border-l border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/40">
        <h2 className="mb-2 text-sm font-semibold text-slate-800 dark:text-slate-100">Retrieved context</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">No context retrieved yet</p>
      </aside>
    )
  }

  return (
    <aside className="flex h-full w-80 flex-col border-l border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/40">
      <h2 className="mb-3 text-sm font-semibold text-slate-800 dark:text-slate-100">Retrieved context</h2>
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto">
        {citations.map(c => (
          <div
            key={c.id}
            className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-slate-900"
          >
            <div className="mb-2 flex items-center gap-2">
              <span className={`rounded px-2 py-0.5 text-xs font-semibold ${severityBadgeClass(c.severity)}`}>
                {c.severity}
              </span>
            </div>
            <p className="mb-2 text-sm text-slate-800 dark:text-slate-100">{c.title}</p>
            <button
              type="button"
              className="text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
              onClick={() => {
                console.log('view details', c.id)
              }}
            >
              View details
            </button>
          </div>
        ))}
      </div>
    </aside>
  )
}
