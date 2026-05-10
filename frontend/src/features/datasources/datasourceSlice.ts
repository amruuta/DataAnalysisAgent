import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'

import { fetchDataSourcesApi } from '@/services/datasourceApi'
import type { DataSource } from '@/types/datasource'

interface DataSourceState {
  items: DataSource[]
  status: 'idle' | 'loading' | 'succeeded' | 'failed'
  error: string | null
}

const initialState: DataSourceState = {
  items: [],
  status: 'idle',
  error: null,
}

export const fetchDataSources = createAsyncThunk(
  'datasources/fetchAll',
  async (sourceType: 'file' | 'database' | undefined, thunkApi) => {
    try {
      return await fetchDataSourcesApi(sourceType)
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'Failed to fetch data sources. Please retry.'
      return thunkApi.rejectWithValue(message)
    }
  },
)

const datasourceSlice = createSlice({
  name: 'datasources',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDataSources.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchDataSources.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.items = action.payload
      })
      .addCase(fetchDataSources.rejected, (state, action) => {
        state.status = 'failed'
        state.error =
          (action.payload as string | undefined) ||
          'Failed to load data sources.'
      })
  },
})

export default datasourceSlice.reducer
