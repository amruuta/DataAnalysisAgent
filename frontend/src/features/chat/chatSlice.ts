import { createAsyncThunk, createSlice, nanoid } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { RootState } from '@/app/store'
import {
  fetchChatSessionApi,
  fetchChatSessionsApi,
  saveChatSessionApi,
  sendChatMessageApi,
} from '@/services/chatApi'
import type {
  ChatMessage,
  ChatSessionSummary,
  PlotlyChartPayload,
  ServerChatMessage,
} from '@/types/chat'

interface ChatState {
  selectedDataSourceId: number | null
  threadId: string | null
  messages: ChatMessage[]
  sessions: ChatSessionSummary[]
  sessionsStatus: 'idle' | 'loading' | 'succeeded' | 'failed'
  sending: boolean
  saving: boolean
  error: string | null
}

const initialState: ChatState = {
  selectedDataSourceId: null,
  threadId: null,
  messages: [],
  sessions: [],
  sessionsStatus: 'idle',
  sending: false,
  saving: false,
  error: null,
}

function createMessage(
  role: ChatMessage['role'],
  content: string,
  charts: PlotlyChartPayload[] = [],
): ChatMessage {
  return {
    id: nanoid(),
    role,
    content,
    timestamp: new Date().toISOString(),
    charts,
  }
}

function extractCharts(message: ServerChatMessage): PlotlyChartPayload[] {
  const charts = message.content.metadata?.charts
  return Array.isArray(charts) ? (charts as PlotlyChartPayload[]) : []
}

function fromServerMessage(message: ServerChatMessage): ChatMessage {
  const role = message.role === 'human' ? 'user' : 'assistant'
  return {
    id: message.id,
    role,
    content: message.content.message,
    timestamp: message.timestamp,
    charts: role === 'assistant' ? extractCharts(message) : [],
  }
}

export const fetchChatSessions = createAsyncThunk(
  'chat/fetchSessions',
  async (_, thunkApi) => {
    try {
      return await fetchChatSessionsApi()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to load chat history.'
      return thunkApi.rejectWithValue(message)
    }
  },
)

export const loadChatSession = createAsyncThunk(
  'chat/loadSession',
  async (threadId: string, thunkApi) => {
    try {
      return await fetchChatSessionApi(threadId)
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to load this chat.'
      return thunkApi.rejectWithValue(message)
    }
  },
)

export const startNewConversation = createAsyncThunk(
  'chat/startNewConversation',
  async (_, thunkApi) => {
    const state = thunkApi.getState() as RootState
    if (state.chat.threadId) {
      await saveChatSessionApi(state.chat.threadId)
      void thunkApi.dispatch(fetchChatSessions())
    }
  },
)

export const sendChatMessage = createAsyncThunk(
  'chat/sendMessage',
  async (message: string, thunkApi) => {
    const state = thunkApi.getState() as RootState
    const dataSourceId = state.chat.selectedDataSourceId

    if (!dataSourceId) {
      return thunkApi.rejectWithValue('Select a data source before chatting.')
    }

    try {
      const response = await sendChatMessageApi({
        data_source_id: dataSourceId,
        message,
        thread_id: state.chat.threadId || undefined,
      })

      void thunkApi.dispatch(fetchChatSessions())
      return {
        response,
        userMessage: message,
      }
    } catch (error) {
      const errMessage =
        error instanceof Error
          ? error.message
          : 'Unable to send message. Please retry.'
      return thunkApi.rejectWithValue(errMessage)
    }
  },
)

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    selectDataSource(state, action: PayloadAction<number>) {
      state.selectedDataSourceId = action.payload
      state.threadId = null
      state.messages = []
      state.error = null
    },
    clearChatError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchChatSessions.pending, (state) => {
        state.sessionsStatus = 'loading'
      })
      .addCase(fetchChatSessions.fulfilled, (state, action) => {
        state.sessionsStatus = 'succeeded'
        state.sessions = action.payload
      })
      .addCase(fetchChatSessions.rejected, (state, action) => {
        state.sessionsStatus = 'failed'
        state.error = action.payload as string
      })
      .addCase(loadChatSession.pending, (state) => {
        state.error = null
      })
      .addCase(loadChatSession.fulfilled, (state, action) => {
        state.threadId = action.payload.thread_id
        state.selectedDataSourceId = action.payload.data_source_id
        state.messages = action.payload.history.map(fromServerMessage)
      })
      .addCase(loadChatSession.rejected, (state, action) => {
        state.error = action.payload as string
      })
      .addCase(startNewConversation.pending, (state) => {
        state.saving = true
      })
      .addCase(startNewConversation.fulfilled, (state) => {
        state.saving = false
        state.threadId = null
        state.messages = []
        state.error = null
      })
      .addCase(startNewConversation.rejected, (state, action) => {
        state.saving = false
        state.error =
          (action.error.message as string | undefined) ||
          'Unable to save the current chat.'
      })
      .addCase(sendChatMessage.pending, (state) => {
        state.sending = true
        state.error = null
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.sending = false
        state.threadId = action.payload.response.thread_id
        const humanMessage = action.payload.response.human_message
          ? fromServerMessage(action.payload.response.human_message)
          : createMessage('user', action.payload.userMessage)
        const aiMessage = action.payload.response.ai_message
          ? fromServerMessage(action.payload.response.ai_message)
          : createMessage(
              'assistant',
              action.payload.response.response,
              action.payload.response.charts ?? [],
            )
        state.messages.push(humanMessage)
        state.messages.push(aiMessage)
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.sending = false
        state.error =
          (action.payload as string | undefined) ||
          'Unable to process your request right now.'
      })
  },
})

export const { selectDataSource, clearChatError } = chatSlice.actions

export default chatSlice.reducer
