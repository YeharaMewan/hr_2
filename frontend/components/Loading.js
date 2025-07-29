export default function Loading({ message = "Loading..." }) {
  return (
    <div className="min-h-screen bg-[var(--color-hr-bg)] flex items-center justify-center">
      <div className="text-center">
        <div className="text-[var(--color-hr-text)] text-lg mb-4">{message}</div>
        <div className="w-8 h-8 border-2 border-[var(--color-hr-primary)] border-t-transparent rounded-full animate-spin mx-auto"></div>
      </div>
    </div>
  )
}