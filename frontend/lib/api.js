// frontend/lib/api.js - Enhanced version
import Cookies from 'js-cookie'
import { API_CONFIG } from './config'

class APIService {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL
    this.timeout = API_CONFIG.TIMEOUT
    this.retryAttempts = API_CONFIG.RETRY_ATTEMPTS
  }

  // Connection test method
  async testConnection() {
    try {
      const response = await fetch(`${this.baseURL}/api/health`, {
        method: 'GET',
        timeout: 5000
      })
      return response.ok
    } catch (error) {
      console.error('Connection test failed:', error)
      return false
    }
  }

  // Enhanced request method with retry logic
  async request(endpoint, options = {}, retryCount = 0) {
    const url = `${this.baseURL}${endpoint}`
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options.headers,
      },
      timeout: this.timeout,
      ...options,
    }

    try {
      // Add timeout to fetch
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.timeout)
      
      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      // Handle authentication errors
      if (response.status === 401) {
        this.removeToken()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        throw new Error('Authentication failed')
      }

      // Parse response
      const contentType = response.headers.get('content-type')
      let data
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      if (!response.ok) {
        throw new Error(data.error || data.message || `HTTP ${response.status}`)
      }

      return { data, status: response.status }
      
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error)
      
      // Retry logic for network errors
      if (retryCount < this.retryAttempts && this.isRetryableError(error)) {
        console.log(`Retrying request... Attempt ${retryCount + 1}/${this.retryAttempts}`)
        await this.delay(1000 * (retryCount + 1)) // Exponential backoff
        return this.request(endpoint, options, retryCount + 1)
      }
      
      throw error
    }
  }

  // Check if error is retryable
  isRetryableError(error) {
    return error.name === 'AbortError' || 
           error.message.includes('network') ||
           error.message.includes('timeout')
  }

  // Delay utility
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // Get auth token from cookies
  getToken() {
    return Cookies.get('jwt_token')
  }

  // Set auth token in cookies
  setToken(token) {
    Cookies.set('jwt_token', token, { 
      expires: 1, // 1 day
      secure: window.location.protocol === 'https:',
      sameSite: 'strict'
    })
  }

  // Remove auth token
  removeToken() {
    Cookies.remove('jwt_token')
  }

  // Get auth headers
  getAuthHeaders() {
    const token = this.getToken()
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  // Rest of the methods remain the same...
  async login(credentials) {
    const response = await this.request('/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
    
    if (response.data.access_token) {
      this.setToken(response.data.access_token)
    }
    
    return response.data
  }

  async logout() {
    this.removeToken()
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
  }

  async healthCheck() {
    return this.request('/api/health')
  }

  async sendMessage(message) {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    })
  }

  // Direct API endpoints
  async getBalance(employeeId) {
    return this.request(`/api/tools/balance/${employeeId}`)
  }

  async getHistory(employeeId) {
    return this.request(`/api/tools/history/${employeeId}`)
  }

  async getSystemStatus() {
    return this.request('/api/system/status')
  }

  async getSwarmStatus() {
    return this.request('/api/swarm/status')
  }

  async resetSwarmConversation(threadId) {
    return this.request(`/api/swarm/reset/${threadId}`, {
      method: 'POST',
    })
  }
}

// Create singleton instance
const apiService = new APIService()

export default apiService