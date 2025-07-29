'use client'

import { useState, useEffect } from 'react'
import { User, LogOut, Settings } from 'lucide-react'
import { getUserInfo, formatUserName } from '@/lib/auth'
import apiService from '@/lib/api'

export default function ChatHeader() {
  const [isClient, setIsClient] = useState(false)
  const [userInfo, setUserInfo] = useState(null)
  const [showProfile, setShowProfile] = useState(false)
  const [userDetails, setUserDetails] = useState(null)

  // Initialize client-side only
  useEffect(() => {
    setIsClient(true)
  }, [])

  useEffect(() => {
    if (!isClient) return
    
    const info = getUserInfo()
    setUserInfo(info)

    // Fetch additional user details
    if (info?.userId) {
      fetchUserDetails(info.userId)
    }
  }, [isClient])

  const fetchUserDetails = async (userId) => {
    try {
      const response = await apiService.getBalance(userId)
      if (response.data.success) {
        setUserDetails(response.data.data)
      }
    } catch (error) {
      console.error('Error fetching user details:', error)
    }
  }

  const handleLogout = async () => {
    await apiService.logout()
  }

  const toggleProfile = () => {
    setShowProfile(!showProfile)
  }

  // Close profile when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showProfile && !event.target.closest('.profile-popup') && !event.target.closest('.profile-button')) {
        setShowProfile(false)
      }
    }

    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [showProfile])

  if (!isClient || !userInfo) return null

  const userName = formatUserName(userInfo)

  return (
    <header style={{
      backgroundColor: '#1e1e1e',
      borderBottom: '1px solid #3a3a3f',
      padding: '1rem 1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'relative'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <h1 style={{
          fontSize: '1.25rem',
          fontWeight: '600',
          color: '#ececf1',
          margin: 0
        }}>
          HR Assistant
        </h1>
        <span style={{
          padding: '0.25rem 0.5rem',
          backgroundColor: 'rgba(109, 40, 217, 0.2)',
          color: '#6D28D9',
          fontSize: '0.75rem',
          borderRadius: '9999px'
        }}>
          Swarm Mode
        </span>
      </div>

      <div style={{ position: 'relative' }}>
        <button
          onClick={toggleProfile}
          style={{
            width: '2.5rem',
            height: '2.5rem',
            backgroundColor: '#6D28D9',
            borderRadius: '50%',
            border: 'none',
            color: 'white',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background-color 0.2s'
          }}
          onMouseOver={(e) => e.target.style.backgroundColor = '#7C3AED'}
          onMouseOut={(e) => e.target.style.backgroundColor = '#6D28D9'}
        >
          {userName.initials}
        </button>

        {/* Profile Popup */}
        {showProfile && (
          <div style={{
            position: 'absolute',
            right: 0,
            top: '3rem',
            width: '18rem',
            backgroundColor: '#2f2f33',
            border: '1px solid #3a3a3f',
            borderRadius: '0.75rem',
            boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
            zIndex: 50,
            animation: 'fadeIn 0.2s ease-out'
          }}>
            <div style={{ padding: '1rem' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                marginBottom: '1rem'
              }}>
                <div style={{
                  width: '3rem',
                  height: '3rem',
                  backgroundColor: '#6D28D9',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: '1.125rem'
                }}>
                  {userName.initials}
                </div>
                <div>
                  <h3 style={{
                    fontWeight: '600',
                    color: '#ececf1',
                    margin: '0 0 0.25rem 0',
                    fontSize: '1rem'
                  }}>
                    {userInfo.name}
                  </h3>
                  <p style={{
                    fontSize: '0.875rem',
                    color: '#8e8ea0',
                    margin: 0
                  }}>
                    {userInfo.userId} • {userInfo.role}
                  </p>
                </div>
              </div>

              {userDetails && (
                <div style={{
                  marginBottom: '1rem',
                  padding: '0.75rem',
                  backgroundColor: '#0d0d0d',
                  borderRadius: '0.5rem'
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.875rem',
                    marginBottom: '0.5rem'
                  }}>
                    <span style={{ color: '#8e8ea0' }}>Department:</span>
                    <span style={{ color: '#ececf1' }}>{userInfo.department}</span>
                  </div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.875rem',
                    marginBottom: '0.5rem'
                  }}>
                    <span style={{ color: '#8e8ea0' }}>Leave Balance:</span>
                    <span style={{ color: '#ececf1', fontWeight: '600' }}>{userDetails.balance} days</span>
                  </div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.875rem'
                  }}>
                    <span style={{ color: '#8e8ea0' }}>Leaves Taken:</span>
                    <span style={{ color: '#ececf1' }}>{userDetails.history?.length || 0} days</span>
                  </div>
                </div>
              )}

              <div style={{
                borderTop: '1px solid #3a3a3f',
                paddingTop: '1rem'
              }}>
                <button
                  onClick={handleLogout}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 1rem',
                    backgroundColor: '#6D28D9',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => e.target.style.backgroundColor = '#7C3AED'}
                  onMouseOut={(e) => e.target.style.backgroundColor = '#6D28D9'}
                >
                  <LogOut size={16} />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}