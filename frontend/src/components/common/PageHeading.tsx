interface PageHeadingProps {
  title: string
  description: string
}

export function PageHeading({ title, description }: PageHeadingProps) {
  return (
    <div className="mb-6 animate-fade-up">
      <h1 className="font-heading text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
        {title}
      </h1>
      <p className="mt-2 max-w-3xl text-sm text-slate-600 sm:text-base">{description}</p>
    </div>
  )
}
