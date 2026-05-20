import { useState } from 'react'
import { ApprovalRequest } from '../types'

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
  const [approvalId, setApprovalId] = useState<string | null>(null)
  const [decided, setDecided] = useState<'approved' | 'rejected' | null>(null)

  async function createApproval(): Promise<string> {
    const res = await fetch(`/api/incidents/${incidentId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
      body: JSON.stringify({
        action_type: 'manual_action',
        action_payload: { description: actionDescription },
      }),
    })
    if (!res.ok) throw new Error(`POST failed (${res.status})`)
    const data = (await res.json()) as ApprovalRequest
    setApprovalId(data.id)
    return data.id
  }

  async function patchApproval(aid: string, status: 'approved' | 'rejected'): Promise<void> {
    const res = await fetch(`/api/incidents/${incidentId}/approve/${aid}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
      body: JSON.stringify({ status, reviewed_by: 'on-call-engineer' }),
    })
    if (!res.ok) throw new Error(`PATCH failed (${res.status})`)
  }

  async function handleDecision(decision: 'approved' | 'rejected') {
    setBusy(true)
    setError(null)
    try {
      const aid = approvalId ?? (await createApproval())
      await patchApproval(aid, decision)
      setDecided(decision)
      if (decision === 'approved') onApproved()
      else onRejected()
    } catch {
      setError(`Could not ${decision === 'approved' ? 'approve' : 'reject'} action. Try again.`)
    } finally {
      setBusy(false)
    }
  }

  if (decided !== null) {
    return (
      <div className="mx-auto max-w-[85%] rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-900">
        {decided === 'approved' ? (
          <span className="font-medium text-emerald-700 dark:text-emerald-400">✓ Action approved and recorded.</span>
        ) : (
          <span className="font-medium text-red-700 dark:text-red-400">✗ Action rejected and recorded.</span>
        )}
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-[85%] rounded-lg border border-amber-200 bg-amber-50/90 p-4 shadow-sm dark:border-amber-900/60 dark:bg-amber-950/40">
      <div className="border-l-4 border-amber-500 pl-3">
        <div className="mb-2 flex items-center gap-2">
          <span aria-hidden className="text-lg">⚠️</span>
          <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-100">Action requires approval</h3>
        </div>
        <p className="mb-3 text-sm text-amber-900/90 dark:text-amber-100/90">{actionDescription}</p>
        {error ? <p className="mb-2 text-sm text-red-600 dark:text-red-400">{error}</p> : null}
        <div className="flex gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => void handleDecision('approved')}
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
            onClick={() => void handleDecision('rejected')}
            className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 dark:border-red-800 dark:bg-transparent dark:text-red-300 dark:hover:bg-red-950/40"
          >
            Reject
          </button>
        </div>
      </div>
    </div>
  )
}
