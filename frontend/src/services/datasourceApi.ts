import type { DataSource } from '@/types/datasource'
import { apiRequest } from '@/services/apiClient'

export async function fetchDataSourcesApi(
  sourceType?: 'file' | 'database',
): Promise<DataSource[]> {
  const query = sourceType ? `?source_type=${sourceType}` : ''
  return apiRequest<DataSource[]>(`/ingest/datasources${query}`)
}

export async function fetchDataSourceByIdApi(id: number): Promise<DataSource> {
  return apiRequest<DataSource>(`/ingest/datasources/${id}`)
}
