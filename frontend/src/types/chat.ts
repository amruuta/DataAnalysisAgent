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
}

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp: string
  charts?: PlotlyChartPayload[]
}
