export type DataSourceType = 'file' | 'database'

export interface DataSource {
  id: number
  name: string
  source_type: DataSourceType
  table_name: string
  file_path: string | null
  db_url: string | null
  created_at: string
}
