import { apiRequest } from '@/services/apiClient'
import type {
  DatabaseConnectionRequest,
  DatabaseConnectionResponse,
  FileUploadResponse,
} from '@/types/ingestion'

export async function uploadCsvApi(
  name: string,
  file: File,
): Promise<FileUploadResponse> {
  const formData = new FormData()
  formData.append('name', name)
  formData.append('file', file)

  return apiRequest<FileUploadResponse>('/ingest/file', {
    method: 'POST',
    body: formData,
  })
}

export async function connectDatabaseApi(
  payload: DatabaseConnectionRequest,
): Promise<DatabaseConnectionResponse> {
  return apiRequest<DatabaseConnectionResponse>('/ingest/database', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
