const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:8000'

interface ErrorPayload {
  detail?: string
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers)
  const isFormData = init?.body instanceof FormData

  if (!isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let detail = 'Request failed. Please try again.'

    try {
      const payload = (await response.json()) as ErrorPayload
      if (payload.detail) {
        detail = payload.detail
      }
    } catch {
      detail = response.statusText || detail
    }

    throw new Error(detail)
  }

  return (await response.json()) as T
}
