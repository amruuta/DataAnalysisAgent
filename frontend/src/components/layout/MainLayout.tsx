import { Outlet } from 'react-router-dom'

import { NavBar } from '@/components/navigation/NavBar'

export function MainLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-white to-cyan-50 text-slate-900">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-24 -left-16 h-72 w-72 rounded-full bg-amber-200/30 blur-3xl" />
        <div className="absolute top-16 right-0 h-72 w-72 rounded-full bg-cyan-200/40 blur-3xl" />
      </div>

      <div className="relative z-10">
        <NavBar />
        <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
