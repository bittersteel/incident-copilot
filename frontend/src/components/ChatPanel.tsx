import { useEffect, useRef, useState, KeyboardEvent } from 'react'
import { Message } from '../types'
import { ApprovalGate } from './ApprovalGate'
import { MessageBubble } from './MessageBubble'

type ChatPanelProps = {
  incidentId?: string
  messages: Message[]
  isLoading: boolean
  agentStatus: string | null
  sendMessage: (text: string, incidentId?: string) => Promise<void>
}

function approvalDescription(text: string): string {
  const marker = '[REQUIRES APPROVAL]'
  if (!text.includes(marker)) return 'This action may affect production systems.'
  const tail = text.split(marker)[1]?.trim()
  return tail && tail.length > 0 ? tail : 'This action may affect production systems.'
}

export function ChatPanel({ incidentId, messages, isLoading, agentStatus, sendMessage }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const rows = Math.min(4, Math.max(1, input.split('\n').length))

  async function handleSend() {
    const text = input.trim()
    if (!text || isLoading) return
    setInput('')
    await sendMessage(text, incidentId)
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant')
  const showGate =
    Boolean(incidentId) &&
    Boolean(lastAssistant?.content?.includes('[REQUIRES APPROVAL]')) &&
    !lastAssistant?.isStreaming

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-white dark:bg-slate-950">
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
        <div>
          <div className="text-base font-bold text-slate-900 dark:text-slate-50">Incident Copilot</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">Powered by Claude</div>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
          <span
            className={`h-2.5 w-2.5 rounded-full ${isLoading ? 'bg-amber-400' : 'bg-emerald-500'}`}
            title={isLoading ? 'Loading' : 'Ready'}
          />
        </div>
      </header>

      {/* Agent activity bar — visible while the multi-agent pipeline is running */}
      {agentStatus && (
        <div className="flex items-center gap-2 border-b border-indigo-100 bg-indigo-50 px-4 py-2 text-xs text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-300">
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-500" />
          </span>
          {agentStatus}
        </div>
      )}

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex h-full min-h-[200px] items-center justify-center text-center text-sm text-slate-500 dark:text-slate-400">
            Ask me about any production incident. I can analyze logs, find similar past incidents, suggest remediation
            steps, and generate RCA reports.
          </div>
        ) : (
          messages.map(m => (
            <div key={m.id} className="space-y-2">
              <MessageBubble message={m} />
              {showGate && m.id === lastAssistant?.id && incidentId ? (
                <ApprovalGate
                  incidentId={incidentId}
                  actionDescription={approvalDescription(m.content)}
                  onApproved={() => {}}
                  onRejected={() => {}}
                />
              ) : null}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <footer className="sticky bottom-0 border-t border-slate-200 bg-white/95 p-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
        <div className="mx-auto flex max-w-3xl flex-col gap-2">
          <textarea
            rows={rows}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Describe the incident or ask a question..."
            className="w-full resize-none rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-inner outline-none ring-indigo-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-slate-500 dark:text-slate-400">Enter to send · Shift+Enter for new line</span>
            <button
              type="button"
              disabled={isLoading || input.trim().length === 0}
              onClick={() => void handleSend()}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}
