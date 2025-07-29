'use client'

import { useState, useEffect } from 'react'
import Loading from './Loading'

export default function ClientOnly({ children, fallback = <Loading /> }) {
  const [hasMounted, setHasMounted] = useState(false)

  useEffect(() => {
    setHasMounted(true)
  }, [])

  if (!hasMounted) {
    return fallback
  }

  return children
}