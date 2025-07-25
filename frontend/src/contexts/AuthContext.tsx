import React, { createContext, useContext, useState, useEffect } from 'react'

interface User {
  id: string
  email: string
  fullName: string
  userType: 'customer' | 'driver' | 'admin'
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for stored token on app start
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      setToken(storedToken)
      // TODO: Validate token and fetch user data
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    setIsLoading(true)
    try {
      // TODO: Implement actual login API call
      console.log('Login attempt:', { email, password })
      // Placeholder implementation
      const mockToken = 'mock-jwt-token'
      const mockUser: User = {
        id: '1',
        email,
        fullName: 'Test User',
        userType: 'customer'
      }
      
      setToken(mockToken)
      setUser(mockUser)
      localStorage.setItem('token', mockToken)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
  }

  const value = {
    user,
    token,
    login,
    logout,
    isLoading
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}