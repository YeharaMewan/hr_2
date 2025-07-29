import Cookies from 'js-cookie'

// Check if we're on the client side
const isClient = typeof window !== 'undefined'

// JWT token utilities
export function getToken() {
  if (!isClient) return null
  return Cookies.get('jwt_token')
}

export function setToken(token) {
  if (!isClient) return
  Cookies.set('jwt_token', token, { expires: 1 })
}

export function removeToken() {
  if (!isClient) return
  Cookies.remove('jwt_token')
}

export function isAuthenticated() {
  if (!isClient) return false
  return !!getToken()
}

// Decode JWT payload (client-side only, for basic info)
export function decodeToken(token) {
  if (!token) return null
  
  try {
    const base64Payload = token.split('.')[1]
    const payload = atob(base64Payload)
    return JSON.parse(payload)
  } catch (error) {
    console.error('Error decoding token:', error)
    return null
  }
}

// Get user info from token
export function getUserInfo() {
  const token = getToken()
  if (!token) return null
  
  const payload = decodeToken(token)
  if (!payload) return null
  
  return {
    userId: payload.sub,
    role: payload.role || 'Employee',
    name: payload.name || 'Unknown',
    department: payload.department || 'Unknown',
    isHR: payload.role === 'HR',
    isEmployee: payload.role === 'Employee',
  }
}

// Check if token is expired
export function isTokenExpired() {
  const token = getToken()
  if (!token) return true
  
  const payload = decodeToken(token)
  if (!payload) return true
  
  const currentTime = Date.now() / 1000
  return payload.exp < currentTime
}

// Redirect to login if not authenticated
export function requireAuth() {
  if (typeof window === 'undefined') return // Skip on server-side
  
  if (!isAuthenticated() || isTokenExpired()) {
    removeToken()
    window.location.href = '/login'
    return false
  }
  
  return true
}

// Protected route wrapper for client components
export function withAuth(Component) {
  return function AuthenticatedComponent(props) {
    const isAuth = requireAuth()
    
    if (!isAuth) {
      return null // Will redirect to login
    }
    
    return <Component {...props} />
  }
}

// Get authorization level for different features
export function getAuthLevel() {
  const userInfo = getUserInfo()
  if (!userInfo) return 'none'
  
  return userInfo.isHR ? 'hr' : 'employee'
}

// Check if user has permission for specific actions
export function hasPermission(requiredLevel) {
  const currentLevel = getAuthLevel()
  
  const levels = {
    'none': 0,
    'employee': 1,
    'hr': 2,
  }
  
  return levels[currentLevel] >= levels[requiredLevel]
}

// Format user display name
export function formatUserName(userInfo) {
  if (!userInfo) return 'Unknown User'
  
  const initials = userInfo.name
    .split(' ')
    .map(n => n.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2)
  
  return {
    full: userInfo.name,
    initials,
    display: `${userInfo.name} (${userInfo.userId})`,
  }
}