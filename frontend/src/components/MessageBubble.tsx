import { Message } from '../types'

function severityChipClass(sev: string): string {
  switch (sev) {
    case 'P1':
      return 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200'
    case 'P2':
      return 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-200'
    case 'P3':
      return 'bg-yellow-100 text-yellow-900 dark:bg-yellow-950 dark:text-yellow-100'
    case 'P4':
    default:
      return 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200'
  }
}

function shortId(full: string): string {
  return full.replace(/-/g, '').slice(0, 8)
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const base =
    'max-w-[85%] rounded-2xl px-4 py-2 text-sm leading-relaxed shadow-sm ' +
    (isUser
      ? 'ml-auto bg-indigo-600 text-white'
      : 'mr-auto bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100')

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={base}>
        <p className="whitespace-pre-wrap break-words">
          {message.content}
          {message.role === 'assistant' && message.isStreaming ? (
            <span className="ml-0.5 inline-block animate-pulse font-mono text-slate-500 dark:text-slate-300">
              |
            </span>
          ) : null}
        </p>
        {message.role === 'assistant' && message.citations && message.citations.length > 0 ? (
          <div className="mt-2 flex flex-wrap gap-1.5 border-t border-slate-200/60 pt-2 dark:border-slate-700/60">
            {message.citations.map(c => (
              <span
                key={c.id}
                className={`inline-flex max-w-full items-center gap-1 rounded-full px-2 py-0.5 text-xs ${severityChipClass(c.severity)}`}
              >
                <span className="font-mono">[INC-{shortId(c.id)}]</span>
                <span className="truncate">{c.title.length > 40 ? `${c.title.slice(0, 40)}…` : c.title}</span>
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  )
}
