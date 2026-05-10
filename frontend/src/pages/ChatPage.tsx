import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { Loader } from '@/components/common/Loader'
import { MarkdownMessage } from '@/components/common/MarkdownMessage'
import { PageHeading } from '@/components/common/PageHeading'
import { PlotlyChart } from '@/components/common/PlotlyChart'
import { StatusBadge } from '@/components/common/StatusBadge'
import {
  clearChatError,
  fetchChatSessions,
  loadChatSession,
  selectDataSource,
  sendChatMessage,
  startNewConversation,
} from '@/features/chat/chatSlice'
import { fetchDataSources } from '@/features/datasources/datasourceSlice'

export function ChatPage() {
  const dispatch = useAppDispatch()
  const [message, setMessage] = useState('')
  const [isMaximized, setIsMaximized] = useState(false)

  const { items: dataSources, status: dataSourceStatus, error: dataSourceError } =
    useAppSelector((state) => state.datasources)

  const {
    selectedDataSourceId,
    messages,
    sessions,
    sessionsStatus,
    sending,
    saving,
    error: chatError,
    threadId,
  } = useAppSelector((state) => state.chat)

  useEffect(() => {
    if (dataSourceStatus === 'idle') {
      void dispatch(fetchDataSources(undefined))
    }
  }, [dataSourceStatus, dispatch])

  useEffect(() => {
    if (sessionsStatus === 'idle') {
      void dispatch(fetchChatSessions())
    }
  }, [dispatch, sessionsStatus])

  useEffect(() => {
    if (chatError) {
      const timer = window.setTimeout(() => {
        dispatch(clearChatError())
      }, 4000)
      return () => window.clearTimeout(timer)
    }
  }, [chatError, dispatch])

  useEffect(() => {
    if (dataSources.length > 0 && !selectedDataSourceId) {
      dispatch(selectDataSource(dataSources[0].id))
    }
  }, [dataSources, dispatch, selectedDataSourceId])

  useEffect(() => {
    if (!isMaximized) {
      return
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMaximized(false)
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [isMaximized])

  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    if (isMaximized) {
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [isMaximized])

  const selectedSource = useMemo(
    () => dataSources.find((source) => source.id === selectedDataSourceId),
    [dataSources, selectedDataSourceId],
  )

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = message.trim()

    if (!trimmed) {
      return
    }

    await dispatch(sendChatMessage(trimmed))
    setMessage('')
  }

  return (
    <div>
      <PageHeading
        title="Chat Workspace"
        description="Choose a data source and start an analysis conversation. Each source keeps its own conversation context, and you can reset with one click."
      />

      {isMaximized && (
        <button
          type="button"
          aria-label="Close maximized chat"
          onClick={() => setIsMaximized(false)}
          className="fixed inset-0 z-30 bg-slate-900/25 backdrop-blur-[1px]"
        />
      )}

      <div className={`grid gap-6 ${isMaximized ? '' : 'lg:grid-cols-[320px_1fr]'}`}>
        {!isMaximized && (
          <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-4 shadow-sm animate-fade-up">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-heading text-lg font-semibold text-slate-900">
                Data Sources
              </h2>
              <button
                type="button"
                onClick={() => void dispatch(startNewConversation())}
                disabled={saving}
                className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-700"
              >
                {saving ? 'Saving...' : 'New Conversation'}
              </button>
            </div>

            {dataSourceStatus === 'loading' && <Loader label="Loading data sources" />}

            {dataSourceError && (
              <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
                {dataSourceError}
              </p>
            )}

            {dataSourceStatus !== 'loading' && dataSources.length === 0 && (
              <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                No data sources found. Go to Data Ingestion to add one.
              </p>
            )}

            <div className="mt-3 space-y-2">
              {dataSources.map((source, index) => {
                const isSelected = source.id === selectedDataSourceId
                return (
                  <button
                    key={source.id}
                    type="button"
                    onClick={() => dispatch(selectDataSource(source.id))}
                    className={`w-full rounded-xl border p-3 text-left transition duration-200 animate-fade-up ${
                      isSelected
                        ? 'border-slate-900 bg-slate-900 text-white shadow-sm'
                        : 'border-slate-200 bg-white hover:border-amber-300 hover:bg-amber-50'
                    }`}
                    style={{ animationDelay: `${index * 40}ms` }}
                  >
                    <p className="truncate text-sm font-semibold">{source.name}</p>
                    <div className="mt-2 flex items-center justify-between text-xs">
                      <span className={isSelected ? 'text-slate-200' : 'text-slate-500'}>
                        {source.table_name}
                      </span>
                      <StatusBadge type={source.source_type} />
                    </div>
                  </button>
                )
              })}
            </div>

            <div className="mt-6 border-t border-slate-100 pt-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-heading text-lg font-semibold text-slate-900">
                  Chat History
                </h2>
                {sessionsStatus === 'loading' && (
                  <span className="text-xs text-slate-400">Loading</span>
                )}
              </div>

              {sessions.length === 0 && sessionsStatus !== 'loading' ? (
                <p className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
                  Saved chats will appear here.
                </p>
              ) : (
                <div className="space-y-2">
                  {sessions.map((session) => {
                    const isActive = session.thread_id === threadId
                    return (
                      <button
                        key={session.thread_id}
                        type="button"
                        onClick={() => void dispatch(loadChatSession(session.thread_id))}
                        className={`w-full rounded-xl border p-3 text-left transition ${
                          isActive
                            ? 'border-amber-400 bg-amber-50'
                            : 'border-slate-200 bg-white hover:border-slate-300'
                        }`}
                      >
                        <p className="truncate text-sm font-semibold text-slate-900">
                          {session.title}
                        </p>
                        <p className="mt-1 truncate text-xs text-slate-500">
                          {session.data_source_name}
                        </p>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </aside>
        )}

        <section
          className={`rounded-2xl border border-slate-200 bg-white p-4 shadow-sm animate-fade-up [animation-delay:120ms] ${
            isMaximized
              ? 'fixed bottom-4 left-4 right-4 top-24 z-40 lg:left-8 lg:right-8'
              : ''
          }`}
        >
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div>
              <p className="font-heading text-lg font-semibold text-slate-900">
                {selectedSource ? selectedSource.name : 'Select a data source'}
              </p>
              <p className="text-xs text-slate-500">
                {threadId ? `Thread: ${threadId}` : 'No active thread yet'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {selectedSource && <StatusBadge type={selectedSource.source_type} />}
              <button
                type="button"
                onClick={() => void dispatch(startNewConversation())}
                disabled={saving}
                className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-700"
              >
                {saving ? 'Saving...' : 'New Conversation'}
              </button>
              <button
                type="button"
                onClick={() => setIsMaximized((previous) => !previous)}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-900 hover:text-slate-900"
              >
                {isMaximized ? 'Restore' : 'Maximize'}
              </button>
            </div>
          </div>

          <div
            className={`mb-4 overflow-y-auto rounded-2xl border border-slate-100 bg-slate-50 p-3 ${
              isMaximized ? 'h-[calc(100vh-260px)]' : 'h-[50vh]'
            }`}
          >
            {messages.length === 0 ? (
              <div className="flex h-full items-center justify-center text-center text-sm text-slate-500">
                Start by asking something like: "Show me total sales by region".
              </div>
            ) : (
              <div className="space-y-3">
                {messages.map((entry) => (
                  <div
                    key={entry.id}
                    className={`flex ${
                      entry.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                        entry.role === 'user'
                          ? 'bg-slate-900 text-white'
                          : 'bg-white text-slate-800 border border-slate-200'
                      }`}
                    >
                      {entry.role === 'assistant' ? (
                        <MarkdownMessage content={entry.content} />
                      ) : (
                        <p className="whitespace-pre-wrap">{entry.content}</p>
                      )}

                      {entry.role === 'assistant' &&
                        entry.charts &&
                        entry.charts.length > 0 && (
                          <div className="space-y-3">
                            {entry.charts.map((chart) => (
                              <PlotlyChart key={chart.chart_id} chart={chart} />
                            ))}
                          </div>
                        )}

                      <p
                        className={`mt-2 text-[11px] ${
                          entry.role === 'user' ? 'text-slate-300' : 'text-slate-400'
                        }`}
                      >
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {chatError && (
            <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {chatError}
            </p>
          )}

          <form onSubmit={onSubmit} className="flex gap-2">
            <input
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Ask about your data..."
              disabled={sending || !selectedDataSourceId}
              className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200 disabled:cursor-not-allowed disabled:bg-slate-100"
            />
            <button
              type="submit"
              disabled={sending || !selectedDataSourceId || !message.trim()}
              className="rounded-xl bg-amber-400 px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:bg-slate-200"
            >
              {sending ? 'Sending...' : 'Send'}
            </button>
          </form>
        </section>
      </div>
    </div>
  )
}
