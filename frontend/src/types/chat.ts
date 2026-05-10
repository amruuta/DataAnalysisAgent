export interface ChatRequest {
  data_source_id: number
  message: string
  thread_id?: string
}

export interface PlotlyChartPayload {
  chart_id: string
  title: string
  chart_type: string
  figure: Record<string, unknown>
}

export interface ChatResponse {
  response: string
  thread_id: string
  charts: PlotlyChartPayload[]
  human_message?: ServerChatMessage
  ai_message?: ServerChatMessage
}

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp: string
  charts?: PlotlyChartPayload[]
}

export interface MessageContentModel {
  message: string
  metadata?: Record<string, unknown>
}

export type ServerChatRole = 'human' | 'ai'

export interface ServerChatMessage {
  id: string
  role: ServerChatRole
  timestamp: string
  content: MessageContentModel
}

export interface ChatSessionSummary {
  thread_id: string
  data_source_id: number
  data_source_name: string
  title: string
  created_at?: string
  updated_at?: string
  last_persisted_at?: string
}

export interface ChatSessionDetail {
  thread_id: string
  data_source_id: number
  data_source_name: string
  title: string
  history: ServerChatMessage[]
}

export interface SaveChatSessionResponse {
  thread_id: string
  saved: boolean
  last_persisted_at?: string
}
