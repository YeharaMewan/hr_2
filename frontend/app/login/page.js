'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import apiService from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [isClient, setIsClient] = useState(false)
  const [formData, setFormData] = useState({
    employee_id: '',
    password: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  // Initialize client-side only
  useEffect(() => {
    setIsClient(true)
  }, [])

  // Redirect if already authenticated (client-side only)
  useEffect(() => {
    if (!isClient) return
    
    if (isAuthenticated()) {
      router.push('/')
    }
  }, [router, isClient])

  // Don't render anything on server-side or before client hydration
  if (!isClient) {
    return (
      <div className="min-h-screen bg-[var(--color-hr-bg)] flex items-center justify-center">
        <div className="text-center">
          <div className="text-[var(--color-hr-text)] text-lg mb-4">Loading...</div>
          <div className="w-8 h-8 border-2 border-[var(--color-hr-primary)] border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
      </div>
    )
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    setError('') // Clear error on input change
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      await apiService.login(formData)
      router.push('/')
    } catch (error) {
      setError(error.message || 'Login failed. Please check your credentials.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickLogin = (employeeId) => {
    setFormData({
      employee_id: employeeId,
      password: 'pw123'
    })
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0d0d0d',
      color: '#ececf1',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: '#1e1e1e',
        padding: '2.5rem',
        borderRadius: '1rem',
        border: '1px solid #3a3a3f',
        width: '100%',
        maxWidth: '28rem',
        boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{
              width: '12rem',
              height: '5rem',
              margin: '0 auto',
              background: 'linear-gradient(to right, #6D28D9, #7C3AED)',
              borderRadius: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <span style={{ color: 'white', fontWeight: 'bold', fontSize: '1.25rem' }}>RiseHR</span>
            </div>
          </div>
          <p style={{ color: '#8e8ea0', fontSize: '0.875rem', margin: 0 }}>
            Agentic HR Solution
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <label htmlFor="employee_id" style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#8e8ea0',
              marginBottom: '0.5rem'
            }}>
              Employee ID
            </label>
            <input
              type="text"
              id="employee_id"
              name="employee_id"
              value={formData.employee_id}
              onChange={handleInputChange}
              required
              placeholder="e.g., E001"
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                backgroundColor: '#0d0d0d',
                border: '1px solid #3a3a3f',
                borderRadius: '0.5rem',
                color: '#ececf1',
                fontSize: '1rem',
                outline: 'none',
                transition: 'border-color 0.2s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#6D28D9'}
              onBlur={(e) => e.target.style.borderColor = '#3a3a3f'}
            />
          </div>

          <div>
            <label htmlFor="password" style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#8e8ea0',
              marginBottom: '0.5rem'
            }}>
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              placeholder="Default: pw123"
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                backgroundColor: '#0d0d0d',
                border: '1px solid #3a3a3f',
                borderRadius: '0.5rem',
                color: '#ececf1',
                fontSize: '1rem',
                outline: 'none',
                transition: 'border-color 0.2s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#6D28D9'}
              onBlur={(e) => e.target.style.borderColor = '#3a3a3f'}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              backgroundColor: isLoading ? '#4B5563' : '#6D28D9',
              color: 'white',
              fontWeight: '600',
              padding: '0.75rem 1rem',
              borderRadius: '0.5rem',
              border: 'none',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              transition: 'background-color 0.2s',
              opacity: isLoading ? 0.5 : 1
            }}
            onMouseOver={(e) => {
              if (!isLoading) e.target.style.backgroundColor = '#7C3AED'
            }}
            onMouseOut={(e) => {
              if (!isLoading) e.target.style.backgroundColor = '#6D28D9'
            }}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        {/* Error Message */}
        {error && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '0.5rem',
            color: '#F87171',
            fontSize: '0.875rem'
          }}>
            {error}
          </div>
        )}

        {/* Quick Login Section */}
        <div style={{
          marginTop: '2rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid #3a3a3f'
        }}>
          <p style={{
            fontSize: '0.75rem',
            color: '#8e8ea0',
            textAlign: 'center',
            marginBottom: '1rem',
            textTransform: 'uppercase',
            letterSpacing: '0.025em',
            margin: '0 0 1rem 0'
          }}>
            Quick Login (for Testing)
          </p>
          <div style={{
            display: 'flex',
            gap: '0.75rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            {[
              { id: 'E001', label: 'HR (E001)' },
              { id: 'E002', label: 'HR (E002)' },
              { id: 'E003', label: 'Emp (E003)' }
            ].map((btn) => (
              <button
                key={btn.id}
                type="button"
                onClick={() => handleQuickLogin(btn.id)}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#2a2a2e',
                  border: '1px solid #3a3a3f',
                  color: '#ececf1',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#3f3f46'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#2a2a2e'}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}