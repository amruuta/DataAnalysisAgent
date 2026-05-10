import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import { connectDatabaseApi, uploadCsvApi } from '@/services/ingestionApi'
import type { DatabaseConnectionRequest } from '@/types/ingestion'

interface IngestionState {
  mode: 'file' | 'database'
  fileUploadStatus: 'idle' | 'loading' | 'succeeded' | 'failed'
  fileUploadMessage: string | null
  fileUploadError: string | null
  dbConnectionStatus: 'idle' | 'loading' | 'succeeded' | 'failed'
  dbConnectionMessage: string | null
  dbConnectionError: string | null
}

const initialState: IngestionState = {
  mode: 'file',
  fileUploadStatus: 'idle',
  fileUploadMessage: null,
  fileUploadError: null,
  dbConnectionStatus: 'idle',
  dbConnectionMessage: null,
  dbConnectionError: null,
}

export const uploadCsvFile = createAsyncThunk(
  'ingestion/uploadCsv',
  async (
    payload: {
      name: string
      file: File
    },
    thunkApi,
  ) => {
    try {
      return await uploadCsvApi(payload.name, payload.file)
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'CSV upload failed. Please retry.'
      return thunkApi.rejectWithValue(message)
    }
  },
)

export const connectDatabase = createAsyncThunk(
  'ingestion/connectDatabase',
  async (payload: DatabaseConnectionRequest, thunkApi) => {
    try {
      return await connectDatabaseApi(payload)
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'Database connection failed. Please retry.'
      return thunkApi.rejectWithValue(message)
    }
  },
)

const ingestionSlice = createSlice({
  name: 'ingestion',
  initialState,
  reducers: {
    setIngestionMode(state, action: PayloadAction<'file' | 'database'>) {
      state.mode = action.payload
      state.fileUploadError = null
      state.dbConnectionError = null
      state.fileUploadMessage = null
      state.dbConnectionMessage = null
    },
    clearIngestionMessages(state) {
      state.fileUploadError = null
      state.dbConnectionError = null
      state.fileUploadMessage = null
      state.dbConnectionMessage = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadCsvFile.pending, (state) => {
        state.fileUploadStatus = 'loading'
        state.fileUploadError = null
        state.fileUploadMessage = null
      })
      .addCase(uploadCsvFile.fulfilled, (state, action) => {
        state.fileUploadStatus = 'succeeded'
        state.fileUploadMessage = action.payload.message
      })
      .addCase(uploadCsvFile.rejected, (state, action) => {
        state.fileUploadStatus = 'failed'
        state.fileUploadError =
          (action.payload as string | undefined) || 'CSV upload failed.'
      })
      .addCase(connectDatabase.pending, (state) => {
        state.dbConnectionStatus = 'loading'
        state.dbConnectionError = null
        state.dbConnectionMessage = null
      })
      .addCase(connectDatabase.fulfilled, (state, action) => {
        state.dbConnectionStatus = 'succeeded'
        state.dbConnectionMessage = action.payload.message
      })
      .addCase(connectDatabase.rejected, (state, action) => {
        state.dbConnectionStatus = 'failed'
        state.dbConnectionError =
          (action.payload as string | undefined) ||
          'Database connection failed.'
      })
  },
})

export const { setIngestionMode, clearIngestionMessages } = ingestionSlice.actions

export default ingestionSlice.reducer
