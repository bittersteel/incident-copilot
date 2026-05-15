export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  isStreaming?: boolean
}

export interface Citation {
  id: string
  title: string
  severity: string
}

export interface Incident {
  id: string
  title: string
  severity: 'P1' | 'P2' | 'P3' | 'P4'
  status: 'open' | 'mitigating' | 'resolved'
  service: string
  environment: string
  description: string
  log_snapshot?: string
  metrics_summary?: string
  deployment_ref?: string
  resolution?: string
  started_at?: string
  resolved_at?: string
  created_at: string
}

export interface RcaReport {
  id: string
  incident_id: string
  timeline: string
  root_cause: string
  impacted_systems: string
  resolution_steps: string
  recommendations: string
  generated_by: string
  created_at: string
}

export interface ApprovalRequest {
  id: string
  incident_id: string
  action_type: string
  action_payload: Record<string, unknown>
  status: 'pending' | 'approved' | 'rejected'
  requested_by: string
  reviewed_by?: string
  created_at: string
  reviewed_at?: string
}
