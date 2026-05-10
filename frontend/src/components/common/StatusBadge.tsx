interface StatusBadgeProps {
  type: 'file' | 'database'
}

export function StatusBadge({ type }: StatusBadgeProps) {
  const classes =
    type === 'file'
      ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
      : 'bg-blue-100 text-blue-700 border-blue-200'

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium uppercase tracking-wide ${classes}`}
    >
      {type}
    </span>
  )
}
