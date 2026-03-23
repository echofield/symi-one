import Link from 'next/link'

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b-2 border-border bg-surface">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link href="/" className="flex items-center gap-3">
                <div className="w-3 h-3 bg-forest" />
                <span className="text-sm font-medium tracking-wider uppercase">SYMIONE PAY</span>
              </Link>
              <nav className="flex items-center gap-6">
                <Link
                  href="/admin"
                  className="text-sm text-muted hover:text-forest transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/admin/reviews"
                  className="text-sm text-muted hover:text-forest transition-colors"
                >
                  Reviews
                </Link>
              </nav>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-forest" />
              <span className="text-micro uppercase tracking-widest text-muted">Admin</span>
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}
