export interface User {
  id: string
  email: string
  created_at?: string
}

export interface AuthResponse {
  user: User
}

export interface AuthCredentials {
  email: string
  password: string
}
