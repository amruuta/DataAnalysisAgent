import { Navigate, Route, Routes } from 'react-router-dom'

import { MainLayout } from '@/components/layout/MainLayout'
import { ChatPage } from '@/pages/ChatPage'
import { DataIngestionPage } from '@/pages/DataIngestionPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/data-ingestion" element={<DataIngestionPage />} />
        <Route path="/" element={<Navigate to="/chat" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  )
}
