'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { isAuthenticated, getUserInfo } from '@/lib/auth'
import apiService from '@/lib/api'
import ChatHeader from '@/components/ChatHeader'
import { ChatMessage, SuggestionChips, ChatInput, ScrollToBottom } from '@/components/chat/ChatMessage'

export default function HomePage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [isClient, setIsClient] = useState(false)
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isFirstMessage, setIsFirstMessage] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [showScrollToBottom, setShowScrollToBottom] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef(null)
  const chatContainerRef = useRef(null)

  // Initialize client-side only
  useEffect(() => {
    setIsClient(true)
  }, [])

  // Check authentication on mount (client-side only)
  useEffect(() => {
    if (!isClient) return
    
    if (!isAuthenticated()) {
      router.push('/login')
    } else {
      setIsLoading(false)
    }
  }, [router, isClient])

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (!isStreaming) {
      scrollToBottom()
    }
  }, [messages, isStreaming])

  // Handle scroll for scroll-to-bottom button
  useEffect(() => {
    const chatContainer = chatContainerRef.current
    if (!chatContainer) return

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = chatContainer
      const isAtBottom = scrollHeight - scrollTop <= clientHeight + 100
      setShowScrollToBottom(!isAtBottom && messages.length > 0)
    }

    chatContainer.addEventListener('scroll', handleScroll)
    return () => chatContainer.removeEventListener('scroll', handleScroll)
  }, [messages])

  // Suggestion chips data
  const suggestionChips = [
    { icon: '❓', text: 'Help' },
    { icon: '👥', text: 'All Employees' },
    { icon: '💰', text: 'Check my leave balance' },
    { icon: '📊', text: 'Show department statistics' },
    { icon: '📈', text: 'Leave trends analysis' },
    { icon: '🔍', text: 'Find employee' }
  ]

  const quickActionChips = [
    { icon: '❓', text: 'Help' },
    { icon: '👥', text: 'All Employees' },
    { icon: '💰', text: 'Check Balance' }
  ]

  const handleSuggestionClick = (text) => {
    setInputValue(text)
    handleSendMessage(text)
  }

  const handleSendMessage = async (messageText = inputValue) => {
    const text = messageText.trim()
    if (!text || isSending) return

    setIsSending(true)
    setIsStreaming(true)

    // Add user message
    const userMessage = { content: text, isUser: true, timestamp: new Date() }
    setMessages(prev => [...prev, userMessage])
    setInputValue('')

    // Show first message transition
    if (isFirstMessage) {
      setIsFirstMessage(false)
    }

    try {
      const response = await apiService.sendMessage(text)
      
      // Add bot response with streaming effect
      const botMessage = { 
        content: response.data.response, 
        isUser: false, 
        timestamp: new Date(),
        systemMode: response.data.system_mode 
      }
      
      setMessages(prev => [...prev, botMessage])
      
      // Simulate streaming delay
      setTimeout(() => setIsStreaming(false), 1000)

    } catch (error) {
      const errorMessage = { 
        content: `Sorry, I encountered an error: ${error.message}`, 
        isUser: false, 
        timestamp: new Date(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
      setIsStreaming(false)
    } finally {
      setIsSending(false)
    }
  }

  if (!isClient || isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0d0d0d',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#ececf1', fontSize: '1.125rem', marginBottom: '1rem' }}>Loading...</div>
          <div style={{
            width: '2rem',
            height: '2rem',
            border: '2px solid #6D28D9',
            borderTop: '2px solid transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto'
          }}></div>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0d0d0d',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Always show Chat Header */}
      <ChatHeader />

      {/* Landing Screen */}
      {isFirstMessage && (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1.5rem'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '32rem',
            margin: '0 auto',
            textAlign: 'center'
          }}>
            {/* Logo and Title */}
            <div style={{ marginBottom: '3rem' }}>
              <div style={{ marginBottom: '1.5rem' }}>
                {/* Logo placeholder */}
                <div style={{
                  width: '18rem',
                  height: '6rem',
                  margin: '0 auto',
                  background: 'linear-gradient(to right, #6D28D9, #7C3AED)',
                  borderRadius: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <span style={{ color: 'white', fontWeight: 'bold', fontSize: '1.5rem' }}>RiseHR</span>
                </div>
              </div>
              <p style={{
                color: '#8e8ea0',
                fontSize: '1.125rem',
                margin: 0
              }}>
                Agentic HR Solution (Preview)
              </p>
            </div>

            {/* Suggestion Chips */}
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'center',
              gap: '0.75rem',
              marginBottom: '2rem'
            }}>
              {suggestionChips.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion.text)}
                  style={{
                    padding: '0.75rem 1.125rem',
                    backgroundColor: '#2a2a2e',
                    border: '1px solid #3a3a3f',
                    borderRadius: '1.25rem',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    color: '#ececf1',
                    fontWeight: '500',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                  onMouseOver={(e) => {
                    e.target.style.backgroundColor = '#3f3f46'
                    e.target.style.borderColor = '#666'
                  }}
                  onMouseOut={(e) => {
                    e.target.style.backgroundColor = '#2a2a2e'
                    e.target.style.borderColor = '#3a3a3f'
                  }}
                >
                  <span>{suggestion.icon}</span>
                  <span>{suggestion.text}</span>
                </button>
              ))}
            </div>

            {/* Main Input */}
            <div style={{ maxWidth: '20rem', margin: '0 auto' }}>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  placeholder="Ask anything about HR..."
                  disabled={isSending}
                  style={{
                    width: '100%',
                    height: '3.25rem',
                    backgroundColor: '#2f2f33',
                    border: '1px solid #3a3a3f',
                    borderRadius: '1.125rem',
                    paddingLeft: '1.25rem',
                    paddingRight: '3rem',
                    color: '#ececf1',
                    fontSize: '1rem',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#6D28D9'}
                  onBlur={(e) => e.target.style.borderColor = '#3a3a3f'}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={isSending || !inputValue.trim()}
                  style={{
                    position: 'absolute',
                    right: '0.75rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: '2rem',
                    height: '2rem',
                    backgroundColor: (!isSending && inputValue.trim()) ? '#6D28D9' : '#666',
                    border: 'none',
                    borderRadius: '50%',
                    color: 'white',
                    cursor: (!isSending && inputValue.trim()) ? 'pointer' : 'not-allowed',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1rem',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => {
                    if (!isSending && inputValue.trim()) {
                      e.target.style.backgroundColor = '#7C3AED'
                    }
                  }}
                  onMouseOut={(e) => {
                    if (!isSending && inputValue.trim()) {
                      e.target.style.backgroundColor = '#6D28D9'
                    }
                  }}
                >
                  ↑
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chat Interface */}
      {!isFirstMessage && (
        <>
          {/* Messages Area */}
          <div 
            ref={chatContainerRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '1.5rem',
              scrollbarWidth: 'thin',
              scrollbarColor: '#444 transparent'
            }}
          >
            <div style={{ maxWidth: '64rem', margin: '0 auto' }}>
              {messages.map((message, index) => (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    justifyContent: message.isUser ? 'flex-end' : 'flex-start',
                    marginBottom: '1.5rem'
                  }}
                >
                  <div style={{
                    maxWidth: '85%',
                    padding: '0.75rem 1.125rem',
                    borderRadius: '1.25rem',
                    backgroundColor: message.isUser ? '#2a2a2e' : '#2f2f33',
                    color: '#ececf1',
                    lineHeight: '1.6',
                    wordWrap: 'break-word',
                    fontSize: '1rem',
                    ...(message.isUser ? { borderBottomRightRadius: '0.25rem' } : { borderBottomLeftRadius: '0.25rem' })
                  }}>
                    <div dangerouslySetInnerHTML={{
                      __html: message.content.replace(/\n/g, '<br>')
                    }} />
                    {isStreaming && index === messages.length - 1 && !message.isUser && (
                      <span style={{
                        display: 'inline-block',
                        width: '0.5rem',
                        height: '1rem',
                        backgroundColor: '#ececf1',
                        marginLeft: '0.25rem',
                        animation: 'pulse 2s infinite'
                      }} />
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Scroll to Bottom Button */}
          {showScrollToBottom && (
            <button
              onClick={scrollToBottom}
              style={{
                position: 'fixed',
                bottom: '8rem',
                right: '1.5rem',
                width: '2.5rem',
                height: '2.5rem',
                backgroundColor: '#2a2a2e',
                border: '1px solid #3a3a3f',
                borderRadius: '50%',
                color: '#ececf1',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.25rem',
                boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                zIndex: 10,
                transition: 'all 0.3s'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#3f3f46'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#2a2a2e'}
            >
              ↓
            </button>
          )}

          {/* Input Area */}
          <div style={{
            backgroundColor: '#1e1e1e',
            borderTop: '1px solid #3a3a3f',
            padding: '1.5rem'
          }}>
            <div style={{ maxWidth: '64rem', margin: '0 auto' }}>
              {/* Quick Action Chips */}
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: '0.75rem',
                marginBottom: '1rem'
              }}>
                {quickActionChips.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion.text)}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#2a2a2e',
                      border: '1px solid #3a3a3f',
                      borderRadius: '1.25rem',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      color: '#ececf1',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}
                    onMouseOver={(e) => e.target.style.backgroundColor = '#3f3f46'}
                    onMouseOut={(e) => e.target.style.backgroundColor = '#2a2a2e'}
                  >
                    <span>{suggestion.icon}</span>
                    <span>{suggestion.text}</span>
                  </button>
                ))}
              </div>

              {/* Chat Input */}
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  placeholder="Ask anything..."
                  disabled={isSending}
                  style={{
                    width: '100%',
                    height: '3.25rem',
                    backgroundColor: '#2f2f33',
                    border: '1px solid #3a3a3f',
                    borderRadius: '1.125rem',
                    paddingLeft: '1.25rem',
                    paddingRight: '3rem',
                    color: '#ececf1',
                    fontSize: '1rem',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#6D28D9'}
                  onBlur={(e) => e.target.style.borderColor = '#3a3a3f'}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={isSending || !inputValue.trim()}
                  style={{
                    position: 'absolute',
                    right: '0.75rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: '2rem',
                    height: '2rem',
                    backgroundColor: (!isSending && inputValue.trim()) ? '#6D28D9' : '#666',
                    border: 'none',
                    borderRadius: '50%',
                    color: 'white',
                    cursor: (!isSending && inputValue.trim()) ? 'pointer' : 'not-allowed',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1rem',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => {
                    if (!isSending && inputValue.trim()) {
                      e.target.style.backgroundColor = '#7C3AED'
                    }
                  }}
                  onMouseOut={(e) => {
                    if (!isSending && inputValue.trim()) {
                      e.target.style.backgroundColor = '#6D28D9'
                    }
                  }}
                >
                  ↑
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}