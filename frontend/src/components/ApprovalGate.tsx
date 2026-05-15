import { useState } from 'react'

const API_KEY = import.meta.env.VITE_API_KEY ?? 'dev-secret'

export function ApprovalGate({
  incidentId,
  actionDescription,
  onApproved,
  onRejected,
}: {
  incidentId: string
  actionDescription: string
  onApproved: () => void
  onRejected: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function approve() {
    setBusy(true)
    setError(null)
    try {
      const res = await fetch(`/api/incidents/${incidentId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify({
          action_type: 'manual_action',
          action_payload: { description: actionDescription },
        }),
      })
      if (!res.ok) throw new Error(`Request failed (${res.status})`)
      onApproved()
    } catch {
      setError('Could not submit approval. Try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-[85%] rounded-lg border border-amber-200 bg-amber-50/90 p-4 shadow-sm dark:border-amber-900/60 dark:bg-amber-950/40">
      <div className="border-l-4 border-amber-500 pl-3">
        <div className="mb-2 flex items-center gap-2">
          <span aria-hidden className="text-lg">
            ⚠️
          </span>
          <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-100">Action requires approval</h3>
        </div>
        <p className="mb-3 text-sm text-amber-900/90 dark:text-amber-100/90">{actionDescription}</p>
        {error ? <p className="mb-2 text-sm text-red-600 dark:text-red-400">{error}</p> : null}
        <div className="flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={approve}
              className="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {busy ? (
                <span
                  className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                  aria-hidden
                />
              ) : null}
              {busy ? 'Submitting…' : 'Approve'}
            </button>
          <button
            type="button"
            disabled={busy}
            onClick={onRejected}
            className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 dark:border-red-800 dark:bg-transparent dark:text-red-300 dark:hover:bg-red-950/40"
          >
            Reject
          </button>
        </div>
      </div>
    </div>
  )
}
