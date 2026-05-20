import { useCallback, useEffect, useMemo, useState } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { CitationsPanel } from './components/CitationsPanel'
import { RcaPanel } from './components/RcaPanel'
import { useChat } from './hooks/useChat'
import { Citation, Incident } from './types'

const API_KEY = import.meta.env.VITE_API_KEY ?? 'dev-secret'

type SidebarTab = 'context' | 'rca'

function truncate(s: string, max: number): string {
  return s.length <= max ? s : `${s.slice(0, max - 1)}…`
}

export default function App() {
  const { messages, isLoading, sendMessage } = useChat()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [activeIncidentId, setActiveIncidentId] = useState<string | undefined>(undefined)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>('context')

  const loadIncidents = useCallback(async () => {
    setLoadError(null)
    try {
      const res = await fetch('/api/incidents', {
        headers: { 'X-API-Key': API_KEY },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = (await res.json()) as Incident[]
      setIncidents(data)
    } catch {
      setLoadError('Could not load incidents')
    }
  }, [])

  useEffect(() => {
    void loadIncidents()
  }, [loadIncidents])

  const latestCitations: Citation[] = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const m = messages[i]
      if (m?.role === 'assistant' && m.citations && m.citations.length > 0) {
        return m.citations
      }
    }
    return []
  }, [messages])

  function tabClass(tab: SidebarTab): string {
    const active =
      'border-b-2 border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
    const inactive =
      'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
    return `flex-1 py-2 text-xs font-semibold ${sidebarTab === tab ? active : inactive}`
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <nav className="flex h-14 shrink-0 items-center border-b border-slate-200 px-4 dark:border-slate-800">
        <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">Incident Copilot</div>
        <div className="mx-auto flex max-w-xl flex-1 justify-center px-4">
          <select
            className="w-full max-w-xl rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            value={activeIncidentId ?? ''}
            onChange={e => setActiveIncidentId(e.target.value || undefined)}
          >
            <option value="">No incident selected</option>
            {incidents.map(inc => (
              <option key={inc.id} value={inc.id}>
                {truncate(`[${inc.severity}] ${inc.title}`, 60)}
              </option>
            ))}
          </select>
        </div>
        {loadError ? <span className="text-xs text-red-600">{loadError}</span> : <span className="w-24" />}
      </nav>

      <div className="flex min-h-0 flex-1 flex-row">
        <div className="min-w-0 flex-1">
          <ChatPanel
            incidentId={activeIncidentId}
            messages={messages}
            isLoading={isLoading}
            sendMessage={sendMessage}
          />
        </div>

        <aside className="flex h-full w-80 shrink-0 flex-col border-l border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/40">
          <div className="flex shrink-0 border-b border-slate-200 dark:border-slate-800">
            <button
              type="button"
              className={tabClass('context')}
              onClick={() => setSidebarTab('context')}
            >
              Context
            </button>
            <button
              type="button"
              className={tabClass('rca')}
              onClick={() => setSidebarTab('rca')}
            >
              RCA
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {sidebarTab === 'context' ? (
              <CitationsPanel citations={latestCitations} />
            ) : (
              <RcaPanel incidentId={activeIncidentId} />
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
