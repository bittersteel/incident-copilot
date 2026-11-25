import { useState, useCallback } from 'react'
import { Message, Citation } from '../types'

const API_KEY = import.meta.env.VITE_API_KEY ?? 'dev-secret'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [agentStatus, setAgentStatus] = useState<string | null>(null)

  const sendMessage = useCallback(async (text: string, incidentId?: string) => {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    }
    const assistantId = crypto.randomUUID()
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      isStreaming: true,
    }

    setMessages(prev => [...prev, userMessage, assistantMessage])
    setIsLoading(true)
    setAgentStatus(null)

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }))

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify({
          message: text,
          incident_id: incidentId ?? null,
          conversation_history: history,
        }),
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let citations: Citation[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6).trim()
          if (!jsonStr) continue

          try {
            const event = JSON.parse(jsonStr) as {
              delta?: string
              done?: boolean
              citations?: Citation[]
              agent?: string
              status?: 'running' | 'done'
              label?: string
            }

            // ── Multi-agent status events ──────────────────────────────────
            if (event.agent && event.status === 'running' && event.label) {
              setAgentStatus(event.label)
            }
            if (event.agent && event.status === 'done' && event.agent === 'responder') {
              setAgentStatus(null)
            }

            // ── Streaming text delta ───────────────────────────────────────
            if (event.delta) {
              setMessages(prev =>
                prev.map(m =>
                  m.id === assistantId
                    ? { ...m, content: m.content + event.delta }
                    : m
                )
              )
            }

            // ── Final done event ───────────────────────────────────────────
            if (event.done) {
              citations = event.citations ?? []
            }
          } catch {
            // malformed chunk — skip
          }
        }
      }

      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId
            ? { ...m, isStreaming: false, citations }
            : m
        )
      )
    } catch {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId
            ? {
                ...m,
                content: 'Error: failed to get response. Check API key and backend.',
                isStreaming: false,
              }
            : m
        )
      )
    } finally {
      setIsLoading(false)
      setAgentStatus(null)
    }
  }, [messages])

  return { messages, isLoading, agentStatus, sendMessage }
}
