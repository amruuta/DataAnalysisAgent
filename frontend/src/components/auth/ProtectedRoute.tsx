import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { Loader } from '@/components/common/Loader'
import { fetchCurrentUser } from '@/features/auth/authSlice'

export function ProtectedRoute() {
  const dispatch = useAppDispatch()
  const { status } = useAppSelector((state) => state.auth)

  useEffect(() => {
    if (status === 'idle') {
      void dispatch(fetchCurrentUser())
    }
  }, [dispatch, status])

  if (status === 'idle' || status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader label="Checking session" />
      </div>
    )
  }

  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export function PublicOnlyRoute() {
  const dispatch = useAppDispatch()
  const { status } = useAppSelector((state) => state.auth)

  useEffect(() => {
    if (status === 'idle') {
      void dispatch(fetchCurrentUser())
    }
  }, [dispatch, status])

  if (status === 'authenticated') {
    return <Navigate to="/chat" replace />
  }

  return <Outlet />
}
