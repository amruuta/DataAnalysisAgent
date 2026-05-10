import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'

import {
  fetchCurrentUserApi,
  loginApi,
  logoutApi,
  registerApi,
} from '@/services/authApi'
import type { AuthCredentials, User } from '@/types/auth'

interface AuthState {
  user: User | null
  status: 'idle' | 'loading' | 'authenticated' | 'unauthenticated'
  error: string | null
}

const initialState: AuthState = {
  user: null,
  status: 'idle',
  error: null,
}

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, thunkApi) => {
    try {
      return await fetchCurrentUserApi()
    } catch {
      return thunkApi.rejectWithValue('Authentication required')
    }
  },
)

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: AuthCredentials, thunkApi) => {
    try {
      return await loginApi(credentials)
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to login right now.'
      return thunkApi.rejectWithValue(message)
    }
  },
)

export const register = createAsyncThunk(
  'auth/register',
  async (credentials: AuthCredentials, thunkApi) => {
    try {
      await registerApi(credentials)
      return await loginApi(credentials)
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to register right now.'
      return thunkApi.rejectWithValue(message)
    }
  },
)

export const logout = createAsyncThunk('auth/logout', async () => {
  await logoutApi()
})

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearAuthError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCurrentUser.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.status = 'authenticated'
        state.user = action.payload.user
        state.error = null
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        state.status = 'unauthenticated'
        state.user = null
      })
      .addCase(login.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'authenticated'
        state.user = action.payload.user
        state.error = null
      })
      .addCase(login.rejected, (state, action) => {
        state.status = 'unauthenticated'
        state.user = null
        state.error = action.payload as string
      })
      .addCase(register.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(register.fulfilled, (state, action) => {
        state.status = 'authenticated'
        state.user = action.payload.user
        state.error = null
      })
      .addCase(register.rejected, (state, action) => {
        state.status = 'unauthenticated'
        state.user = null
        state.error = action.payload as string
      })
      .addCase(logout.fulfilled, (state) => {
        state.status = 'unauthenticated'
        state.user = null
        state.error = null
      })
  },
})

export const { clearAuthError } = authSlice.actions

export default authSlice.reducer
