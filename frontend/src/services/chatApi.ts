import { apiRequest } from '@/services/apiClient'
import type { ChatRequest, ChatResponse } from '@/types/chat'

export async function sendChatMessageApi(
  payload: ChatRequest,
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
