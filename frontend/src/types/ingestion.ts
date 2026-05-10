export interface FileUploadResponse {
  id: number
  name: string
  table_name: string
  file_path: string
  message: string
}

export interface DatabaseConnectionRequest {
  name: string
  db_host?: string
  db_port?: number
  db_name?: string
  db_user?: string
  db_password?: string
  db_url?: string
  table_name?: string
}

export interface DatabaseConnectionResponse {
  id: number
  name: string
  db_url: string
  table_name?: string | null
  message: string
}
