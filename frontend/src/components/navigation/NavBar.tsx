import { NavLink } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { logout } from '@/features/auth/authSlice'

const navItems = [
  { to: '/chat', label: 'Chat' },
  { to: '/data-ingestion', label: 'Data Ingestion' },
]

export function NavBar() {
  const dispatch = useAppDispatch()
  const user = useAppSelector((state) => state.auth.user)

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/85 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div>
          <p className="font-heading text-xl font-bold tracking-tight text-slate-900">
            Data Analysis Agent
          </p>
          <p className="text-xs uppercase tracking-[0.25em] text-slate-500">
            workspace console
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-3">
          <nav className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white p-1 shadow-sm">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-amber-100 hover:text-slate-900'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
            <span className="max-w-48 truncate text-xs font-semibold text-slate-600">
              {user?.email}
            </span>
            <button
              type="button"
              onClick={() => void dispatch(logout())}
              className="rounded-xl bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-700"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
