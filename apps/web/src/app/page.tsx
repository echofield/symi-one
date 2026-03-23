import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b-2 border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-forest" />
              <span className="text-sm font-medium tracking-wider uppercase">SYMIONE PAY</span>
            </div>
            <nav className="flex items-center gap-6">
              <Link href="/create" className="btn-secondary text-sm py-2 px-4">
                Create Execution
              </Link>
              <Link href="/admin" className="btn-ghost text-sm">
                Admin
              </Link>
              <Link href="/debug" className="btn-ghost text-sm text-muted">
                API
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 pt-16">
        <section className="min-h-[90vh] flex items-center">
          <div className="max-w-7xl mx-auto px-6 lg:px-12 py-20">
            <div className="grid lg:grid-cols-12 gap-12 lg:gap-20 items-center">
              {/* Left Column - Main Content */}
              <div className="lg:col-span-7 space-y-10">
                <div className="space-y-6 opacity-0 animate-fade-up">
                  <p className="text-micro uppercase tracking-[0.3em] text-muted">
                    Proof-to-Payment Execution Layer
                  </p>
                  <h1 className="text-display text-foreground">
                    Send work.<br />
                    <span className="text-forest">Get paid when it passes.</span>
                  </h1>
                </div>

                <p className="text-xl font-light text-muted leading-relaxed max-w-xl opacity-0 animate-fade-up stagger-2">
                  One party deposits. Another submits proof.
                  Payment releases automatically when validation passes.
                  No invoices. No disputes. No waiting.
                </p>

                <div className="flex items-center gap-4 opacity-0 animate-fade-up stagger-3">
                  <Link href="/create" className="btn-primary">
                    Create Execution
                  </Link>
                  <Link href="#how-it-works" className="btn-ghost">
                    How it works
                  </Link>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-12 pt-8 opacity-0 animate-fade-up stagger-4">
                  <div>
                    <p className="text-3xl font-light text-forest">0%</p>
                    <p className="text-micro uppercase tracking-widest text-muted mt-1">Disputes</p>
                  </div>
                  <div className="w-px h-12 bg-border" />
                  <div>
                    <p className="text-3xl font-light text-forest">&lt;1s</p>
                    <p className="text-micro uppercase tracking-widest text-muted mt-1">Validation</p>
                  </div>
                  <div className="w-px h-12 bg-border" />
                  <div>
                    <p className="text-3xl font-light text-forest">Auto</p>
                    <p className="text-micro uppercase tracking-widest text-muted mt-1">Release</p>
                  </div>
                </div>
              </div>

              {/* Right Column - Visual Element */}
              <div className="lg:col-span-5 opacity-0 animate-fade-up stagger-5">
                <div className="relative">
                  {/* Decorative background */}
                  <div className="absolute -top-4 -right-4 w-full h-full border-2 border-forest" />

                  {/* Main card */}
                  <div className="relative bg-surface border-2 border-foreground p-8 space-y-6">
                    <div className="flex items-center justify-between">
                      <span className="text-micro uppercase tracking-widest text-muted">Execution</span>
                      <span className="badge-success">Funded</span>
                    </div>

                    <div className="space-y-1">
                      <p className="text-caption text-muted">Website Redesign</p>
                      <p className="text-3xl font-light">$2,500.00</p>
                    </div>

                    <div className="h-px bg-border" />

                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted">Proof Required</span>
                        <span className="font-medium">URL</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted">Validation</span>
                        <span className="font-medium">Reachable + Lighthouse &ge;80</span>
                      </div>
                    </div>

                    <div className="pt-4">
                      <div className="w-full h-2 bg-forest-50">
                        <div className="w-2/3 h-full bg-forest transition-all duration-1000" />
                      </div>
                      <p className="text-micro text-muted mt-2">Awaiting proof submission</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How it Works */}
        <section id="how-it-works" className="py-30 bg-surface border-y-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="max-w-2xl mb-20">
              <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Process</p>
              <h2 className="text-headline text-foreground">
                Three steps to automated payments
              </h2>
            </div>

            <div className="grid md:grid-cols-3 gap-px bg-border">
              {[
                {
                  step: '01',
                  title: 'Create Execution',
                  description: 'Define proof requirements, set validation rules, specify payment amount. Share funding link with payer.',
                },
                {
                  step: '02',
                  title: 'Fund & Submit',
                  description: 'Payer funds via Stripe. Creator submits proof URL or file when work is complete.',
                },
                {
                  step: '03',
                  title: 'Auto-Release',
                  description: 'Proof validates automatically. If it passes, payment releases instantly. No manual intervention.',
                },
              ].map((item, i) => (
                <div
                  key={item.step}
                  className="bg-background p-10 group hover:bg-forest transition-colors duration-300"
                >
                  <span className="text-5xl font-light text-border group-hover:text-white/20 transition-colors">
                    {item.step}
                  </span>
                  <h3 className="text-title mt-8 mb-4 group-hover:text-white transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-body text-muted group-hover:text-white/70 transition-colors">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Validation Types */}
        <section className="py-30">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="grid lg:grid-cols-2 gap-20">
              <div>
                <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Validators</p>
                <h2 className="text-headline text-foreground mb-6">
                  Proof that proves itself
                </h2>
                <p className="text-body text-muted max-w-md">
                  Automated validation means no back-and-forth. Define your rules once,
                  and every submission is checked instantly against objective criteria.
                </p>
              </div>

              <div className="grid gap-4">
                {/* URL Proof Card */}
                <div className="card-interactive">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <p className="text-micro uppercase tracking-widest text-muted mb-2">Proof Type</p>
                      <h3 className="text-title">URL Proof</h3>
                    </div>
                    <div className="w-10 h-10 border-2 border-forest flex items-center justify-center">
                      <svg className="w-5 h-5 text-forest" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                    </div>
                  </div>
                  <ul className="space-y-3 text-body text-muted">
                    <li className="flex items-center gap-3">
                      <span className="w-1 h-1 bg-forest" />
                      URL reachable (HTTP 200)
                    </li>
                    <li className="flex items-center gap-3">
                      <span className="w-1 h-1 bg-forest" />
                      Domain allowlist
                    </li>
                    <li className="flex items-center gap-3">
                      <span className="w-1 h-1 bg-forest" />
                      Lighthouse performance score
                    </li>
                  </ul>
                </div>

                {/* File Proof Card */}
                <div className="card-interactive">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <p className="text-micro uppercase tracking-widest text-muted mb-2">Proof Type</p>
                      <h3 className="text-title">File Proof</h3>
                    </div>
                    <div className="w-10 h-10 border-2 border-forest flex items-center justify-center">
                      <svg className="w-5 h-5 text-forest" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                  </div>
                  <ul className="space-y-3 text-body text-muted">
                    <li className="flex items-center gap-3">
                      <span className="w-1 h-1 bg-forest" />
                      File exists in storage
                    </li>
                    <li className="flex items-center gap-3">
                      <span className="w-1 h-1 bg-forest" />
                      MIME type validation
                    </li>
                    <li className="flex items-center gap-3">
                      <span className="w-1 h-1 bg-forest" />
                      Maximum file size check
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-30 bg-forest">
          <div className="max-w-7xl mx-auto px-6 lg:px-12 text-center">
            <h2 className="text-headline text-white mb-6">
              Stop chasing payments
            </h2>
            <p className="text-xl font-light text-white/70 max-w-xl mx-auto mb-10">
              Create your first proof-to-payment execution in under a minute.
            </p>
            <Link
              href="/create"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-forest font-medium border-2 border-white transition-all duration-200 hover:bg-transparent hover:text-white"
            >
              Get Started
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-8 border-t-2 border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-forest" />
              <span className="text-micro uppercase tracking-widest text-muted">SYMIONE PAY</span>
            </div>
            <p className="text-micro text-muted">
              Proof-to-Payment Execution Layer
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
