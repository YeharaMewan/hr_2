import './globals.css'

export const metadata = {
  title: 'HR Agent - Agentic HR Solution',
  description: 'Advanced multi-agent HR system powered by LangGraph Swarm',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
        <meta name="theme-color" content="#6D28D9" />
        <meta name="description" content={metadata.description} />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}