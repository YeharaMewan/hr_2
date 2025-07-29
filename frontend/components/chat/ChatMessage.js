// components/chat/ChatMessage.js
'use client'

import { useState, useEffect } from 'react'

export function ChatMessage({ message, isUser, isStreaming }) {
  const [displayedContent, setDisplayedContent] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (!isStreaming || isUser) {
      setDisplayedContent(message.content)
      return
    }

    // Streaming effect for bot messages
    if (currentIndex < message.content.length) {
      const timer = setTimeout(() => {
        setDisplayedContent(message.content.slice(0, currentIndex + 1))
        setCurrentIndex(currentIndex + 1)
      }, 15)
      return () => clearTimeout(timer)
    }
  }, [message.content, currentIndex, isStreaming, isUser])

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 animate-slide-up`}>
      <div className={`max-w-[85%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-[var(--color-hr-accent)] rounded-br-md'
              : 'bg-[var(--color-hr-surface-hover)] rounded-bl-md'
          } text-[var(--color-hr-text)] leading-relaxed`}
        >
          <div
            className="whitespace-pre-wrap break-words"
            dangerouslySetInnerHTML={{
              __html: displayedContent.replace(/\n/g, '<br>')
            }}
          />
          {isStreaming && !isUser && currentIndex < message.content.length && (
            <span className="inline-block w-2 h-4 bg-[var(--color-hr-text)] animate-pulse-subtle ml-1" />
          )}
        </div>
      </div>
    </div>
  )
}

// components/chat/SuggestionChips.js
export function SuggestionChips({ suggestions, onSuggestionClick, className = '' }) {
  return (
    <div className={`flex flex-wrap gap-3 justify-center ${className}`}>
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          onClick={() => onSuggestionClick(suggestion.text)}
          className="px-4 py-2 bg-[var(--color-hr-accent)] hover:bg-[var(--color-hr-accent-hover)] border border-[var(--color-hr-border)] rounded-full text-sm text-[var(--color-hr-text)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-hr-primary)] flex items-center gap-2"
        >
          <span>{suggestion.icon}</span>
          <span>{suggestion.text}</span>
        </button>
      ))}
    </div>
  )
}

// components/chat/ChatInput.js
import { Send } from 'lucide-react'

export function ChatInput({ value, onChange, onSubmit, disabled, placeholder }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSubmit()
    }
  }

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full h-13 bg-[var(--color-hr-surface-hover)] border border-[var(--color-hr-border)] rounded-2xl px-5 pr-12 text-[var(--color-hr-text)] placeholder-[var(--color-hr-text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-hr-primary)] focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <button
        onClick={onSubmit}
        disabled={disabled || !value.trim()}
        className="absolute right-3 top-1/2 transform -translate-y-1/2 w-8 h-8 bg-[var(--color-hr-primary)] hover:bg-[var(--color-hr-primary-hover)] disabled:bg-gray-600 disabled:cursor-not-allowed rounded-full flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-hr-primary)] focus:ring-offset-2 focus:ring-offset-[var(--color-hr-surface-hover)]"
      >
        <Send size={16} className="text-white" />
      </button>
    </div>
  )
}

// components/chat/ScrollToBottom.js
import { ChevronDown } from 'lucide-react'

export function ScrollToBottom({ show, onClick }) {
  if (!show) return null

  return (
    <button
      onClick={onClick}
      className="fixed bottom-32 right-6 w-10 h-10 bg-[var(--color-hr-accent)] hover:bg-[var(--color-hr-accent-hover)] border border-[var(--color-hr-border)] rounded-full flex items-center justify-center text-[var(--color-hr-text)] transition-all duration-300 shadow-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-hr-primary)] z-10"
      style={{
        opacity: show ? 1 : 0,
        visibility: show ? 'visible' : 'hidden'
      }}
    >
      <ChevronDown size={20} />
    </button>
  )
}