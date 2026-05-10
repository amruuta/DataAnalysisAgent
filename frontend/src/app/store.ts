import { configureStore } from '@reduxjs/toolkit'

import chatReducer from '@/features/chat/chatSlice'
import datasourceReducer from '@/features/datasources/datasourceSlice'
import ingestionReducer from '@/features/ingestion/ingestionSlice'

export const store = configureStore({
  reducer: {
    datasources: datasourceReducer,
    chat: chatReducer,
    ingestion: ingestionReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
