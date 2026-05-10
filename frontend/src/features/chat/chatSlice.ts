import { createAsyncThunk, createSlice, nanoid } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import { sendChatMessageApi } from '@/services/chatApi'
import type { ChatMessage, PlotlyChartPayload } from '@/types/chat'
import type { RootState } from '@/app/store'

interface ChatState {
  selectedDataSourceId: number | null
  threadId: string | null
  messages: ChatMessage[]
  sending: boolean
  error: string | null
}

const initialState: ChatState = {
  selectedDataSourceId: null,
  threadId: null,
  messages: [],
  sending: false,
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
    startNewConversation(state) {
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
      .addCase(sendChatMessage.pending, (state) => {
        state.sending = true
        state.error = null
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.sending = false
        state.threadId = action.payload.response.thread_id
        state.messages.push(createMessage('user', action.payload.userMessage))
        state.messages.push(
          createMessage(
            'assistant',
            action.payload.response.response,
            action.payload.response.charts ?? [],
          ),
        )
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.sending = false
        state.error =
          (action.payload as string | undefined) ||
          'Unable to process your request right now.'
      })
  },
})

export const { selectDataSource, startNewConversation, clearChatError } =
  chatSlice.actions

export default chatSlice.reducer
