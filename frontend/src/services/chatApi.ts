import { apiRequest } from '@/services/apiClient'
import type {
  ChatRequest,
  ChatResponse,
  ChatSessionDetail,
  ChatSessionSummary,
  SaveChatSessionResponse,
} from '@/types/chat'

export async function sendChatMessageApi(
  payload: ChatRequest,
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function fetchChatSessionsApi(): Promise<ChatSessionSummary[]> {
  return apiRequest<ChatSessionSummary[]>('/chat/sessions')
}

export async function fetchChatSessionApi(
  threadId: string,
): Promise<ChatSessionDetail> {
  return apiRequest<ChatSessionDetail>(`/chat/sessions/${threadId}`)
}

export async function saveChatSessionApi(
  threadId: string,
): Promise<SaveChatSessionResponse> {
  return apiRequest<SaveChatSessionResponse>(`/chat/sessions/${threadId}/save`, {
    method: 'POST',
  })
}
