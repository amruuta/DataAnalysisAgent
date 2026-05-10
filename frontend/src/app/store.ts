import { combineReducers, configureStore } from '@reduxjs/toolkit'

import authReducer from '@/features/auth/authSlice'
import { logout } from '@/features/auth/authSlice'
import chatReducer from '@/features/chat/chatSlice'
import datasourceReducer from '@/features/datasources/datasourceSlice'
import ingestionReducer from '@/features/ingestion/ingestionSlice'

const appReducer = combineReducers({
  auth: authReducer,
  datasources: datasourceReducer,
  chat: chatReducer,
  ingestion: ingestionReducer,
})

const rootReducer: typeof appReducer = (state, action) => {
  if (logout.fulfilled.match(action)) {
    return appReducer(undefined, action)
  }
  return appReducer(state, action)
}

export const store = configureStore({
  reducer: rootReducer,
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
