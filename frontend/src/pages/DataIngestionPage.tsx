import { useEffect, useMemo, useRef, useState } from 'react'
import type { DragEvent, FormEvent } from 'react'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { PageHeading } from '@/components/common/PageHeading'
import { StatusBadge } from '@/components/common/StatusBadge'
import { fetchDataSources } from '@/features/datasources/datasourceSlice'
import {
  clearIngestionMessages,
  connectDatabase,
  setIngestionMode,
  uploadCsvFile,
} from '@/features/ingestion/ingestionSlice'

interface DatabaseFormState {
  name: string
  db_url: string
  table_name: string
  db_host: string
  db_port: string
  db_name: string
  db_user: string
  db_password: string
}

const initialDatabaseForm: DatabaseFormState = {
  name: '',
  db_url: '',
  table_name: '',
  db_host: '',
  db_port: '5432',
  db_name: '',
  db_user: '',
  db_password: '',
}

function isCsvFile(file: File): boolean {
  return file.name.toLowerCase().endsWith('.csv')
}

export function DataIngestionPage() {
  const dispatch = useAppDispatch()
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [uploadName, setUploadName] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [databaseForm, setDatabaseForm] =
    useState<DatabaseFormState>(initialDatabaseForm)
  const [localError, setLocalError] = useState<string | null>(null)

  const {
    mode,
    fileUploadStatus,
    fileUploadMessage,
    fileUploadError,
    dbConnectionStatus,
    dbConnectionMessage,
    dbConnectionError,
  } = useAppSelector((state) => state.ingestion)

  const dataSources = useAppSelector((state) => state.datasources.items)

  const ingestionFeedback = useMemo(
    () =>
      fileUploadError || dbConnectionError || fileUploadMessage || dbConnectionMessage,
    [dbConnectionError, dbConnectionMessage, fileUploadError, fileUploadMessage],
  )

  useEffect(() => {
    void dispatch(fetchDataSources(undefined))
  }, [dispatch])

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)

    const droppedFile = event.dataTransfer.files?.[0]
    if (!droppedFile) {
      return
    }

    if (!isCsvFile(droppedFile)) {
      setLocalError('Only CSV files are allowed for drag-and-drop upload.')
      return
    }

    setLocalError(null)
    setSelectedFile(droppedFile)
  }

  const onUploadCsv = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    dispatch(clearIngestionMessages())

    if (!uploadName.trim()) {
      setLocalError('Please provide a datasource name for the CSV upload.')
      return
    }

    if (!selectedFile) {
      setLocalError('Please select a CSV file before uploading.')
      return
    }

    if (!isCsvFile(selectedFile)) {
      setLocalError('Only CSV files are supported in this flow.')
      return
    }

    setLocalError(null)

    try {
      await dispatch(uploadCsvFile({ name: uploadName.trim(), file: selectedFile })).unwrap()
      setUploadName('')
      setSelectedFile(null)
      await dispatch(fetchDataSources(undefined)).unwrap()
    } catch {
      // handled by Redux slice state
    }
  }

  const onConnectDatabase = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    dispatch(clearIngestionMessages())

    if (!databaseForm.name.trim()) {
      setLocalError('Datasource name is required for a database connection.')
      return
    }

    const hasUrl = databaseForm.db_url.trim().length > 0
    const hasCredentialSet =
      databaseForm.db_host.trim().length > 0 &&
      databaseForm.db_name.trim().length > 0 &&
      databaseForm.db_user.trim().length > 0 &&
      databaseForm.db_password.trim().length > 0

    if (!hasUrl && !hasCredentialSet) {
      setLocalError(
        'Provide either DB URL or all required credential fields (host, db name, user, password).',
      )
      return
    }

    setLocalError(null)

    try {
      await dispatch(
        connectDatabase({
          name: databaseForm.name.trim(),
          db_url: databaseForm.db_url.trim() || undefined,
          table_name: databaseForm.table_name.trim() || undefined,
          db_host: databaseForm.db_host.trim() || undefined,
          db_port: Number(databaseForm.db_port || 5432),
          db_name: databaseForm.db_name.trim() || undefined,
          db_user: databaseForm.db_user.trim() || undefined,
          db_password: databaseForm.db_password || undefined,
        }),
      ).unwrap()

      setDatabaseForm(initialDatabaseForm)
      await dispatch(fetchDataSources(undefined)).unwrap()
    } catch {
      // handled by Redux slice state
    }
  }

  return (
    <div>
      <PageHeading
        title="Data Ingestion"
        description="Ingest data either by uploading CSV files or connecting a database. The two ingestion paths are intentionally separated so one method is active at a time."
      />

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm animate-fade-up">
          <div className="mb-5 inline-flex rounded-xl border border-slate-200 p-1">
            <button
              type="button"
              onClick={() => {
                dispatch(setIngestionMode('file'))
                setLocalError(null)
              }}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                mode === 'file'
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-amber-50'
              }`}
            >
              CSV Upload
            </button>
            <button
              type="button"
              onClick={() => {
                dispatch(setIngestionMode('database'))
                setLocalError(null)
              }}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                mode === 'database'
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-amber-50'
              }`}
            >
              Database Connection
            </button>
          </div>

          {mode === 'file' ? (
            <form onSubmit={onUploadCsv} className="space-y-4">
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">
                  Datasource Name
                </span>
                <input
                  value={uploadName}
                  onChange={(event) => setUploadName(event.target.value)}
                  placeholder="e.g. superstore-sales"
                  className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                />
              </label>

              <div
                role="presentation"
                onDragOver={(event) => {
                  event.preventDefault()
                  setDragging(true)
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition ${
                  dragging
                    ? 'border-slate-900 bg-amber-50'
                    : 'border-slate-300 bg-slate-50 hover:border-amber-400 hover:bg-amber-50'
                }`}
              >
                <p className="font-heading text-lg font-semibold text-slate-800">
                  Drag & drop your CSV file here
                </p>
                <p className="mt-2 text-sm text-slate-500">
                  or click to browse from your machine
                </p>
                <p className="mt-4 text-xs text-slate-400">Accepted format: .csv</p>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={(event) => {
                  const file = event.target.files?.[0] || null
                  if (file && !isCsvFile(file)) {
                    setLocalError('Only CSV files are allowed.')
                    setSelectedFile(null)
                    return
                  }
                  setLocalError(null)
                  setSelectedFile(file)
                }}
              />

              {selectedFile && (
                <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                  Selected: {selectedFile.name}
                </p>
              )}

              <button
                type="submit"
                disabled={fileUploadStatus === 'loading'}
                className="rounded-xl bg-amber-400 px-4 py-2.5 text-sm font-semibold text-slate-900 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:bg-slate-200"
              >
                {fileUploadStatus === 'loading' ? 'Uploading...' : 'Upload CSV'}
              </button>
            </form>
          ) : (
            <form onSubmit={onConnectDatabase} className="space-y-3">
              <div className="grid gap-3 md:grid-cols-2">
                <input
                  value={databaseForm.name}
                  onChange={(event) =>
                    setDatabaseForm((prev) => ({ ...prev, name: event.target.value }))
                  }
                  placeholder="Datasource name"
                  className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200 md:col-span-2"
                />
                <input
                  value={databaseForm.db_url}
                  onChange={(event) =>
                    setDatabaseForm((prev) => ({ ...prev, db_url: event.target.value }))
                  }
                  placeholder="DB URL (optional alternative)"
                  className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200 md:col-span-2"
                />
                <input
                  value={databaseForm.db_host}
                  onChange={(event) =>
                    setDatabaseForm((prev) => ({ ...prev, db_host: event.target.value }))
                  }
                  placeholder="Host"
                  className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                />
                <input
                  value={databaseForm.db_port}
                  onChange={(event) =>
                    setDatabaseForm((prev) => ({ ...prev, db_port: event.target.value }))
                  }
                  placeholder="Port"
                  className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                />
                <input
                  value={databaseForm.db_name}
                  onChange={(event) =>
                    setDatabaseForm((prev) => ({ ...prev, db_name: event.target.value }))
                  }
                  placeholder="Database name"
                  className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                />
                <input
                  value={databaseForm.db_user}
                  onChange={(event) =>
                    setDatabaseForm((prev) => ({ ...prev, db_user: event.target.value }))
                  }
                  placeholder="Database user"
                  className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                />
                <input
                  type="password"
                  value={databaseForm.db_password}
                  onChange={(event) =>
                    setDatabaseForm((prev) => ({ ...prev, db_password: event.target.value }))
                  }
                  placeholder="Database password"
                  className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                />
                <input
                  value={databaseForm.table_name}
                  onChange={(event) =>
                    setDatabaseForm((prev) => ({ ...prev, table_name: event.target.value }))
                  }
                  placeholder="Table name (optional)"
                  className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                />
              </div>

              <p className="text-xs text-slate-500">
                Provide either DB URL, or host + db name + user + password.
              </p>

              <button
                type="submit"
                disabled={dbConnectionStatus === 'loading'}
                className="rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-600 disabled:cursor-not-allowed disabled:bg-slate-200"
              >
                {dbConnectionStatus === 'loading' ? 'Connecting...' : 'Connect Database'}
              </button>
            </form>
          )}

          {(localError || ingestionFeedback) && (
            <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
              <span
                className={
                  localError || fileUploadError || dbConnectionError
                    ? 'text-red-700'
                    : 'text-emerald-700'
                }
              >
                {localError || ingestionFeedback}
              </span>
            </div>
          )}
        </section>

        <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm animate-fade-up [animation-delay:120ms]">
          <h2 className="font-heading text-lg font-semibold text-slate-900">
            Registered Data Sources
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            These are available immediately in the Chat page.
          </p>

          <div className="mt-4 space-y-3">
            {dataSources.length === 0 ? (
              <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                No data sources yet. Ingest one using the form on the left.
              </p>
            ) : (
              dataSources.map((source, index) => (
                <div
                  key={source.id}
                  className="animate-fade-up rounded-xl border border-slate-200 bg-slate-50 p-3"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="truncate text-sm font-semibold text-slate-800">{source.name}</p>
                    <StatusBadge type={source.source_type} />
                  </div>
                  <p className="mt-2 truncate text-xs text-slate-500">Table: {source.table_name}</p>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
