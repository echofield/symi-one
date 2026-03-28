import Link from 'next/link'

export default function MusicPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b-2 border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-3 h-3 bg-forest" />
              <span className="text-sm font-medium tracking-wider uppercase">SYMIONE</span>
            </Link>
            <nav className="flex items-center gap-6">
              <Link href="/create" className="btn-primary text-sm py-2 px-4">
                Create Deal
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
                <div className="space-y-6">
                  <p className="text-micro uppercase tracking-[0.3em] text-muted">
                    For Sound Engineers & Producers
                  </p>
                  <h1 className="text-display text-foreground">
                    Get paid when you deliver.<br />
                    <span className="text-forest">Not before. Not maybe.</span>
                  </h1>
                </div>

                <p className="text-xl font-light text-muted leading-relaxed max-w-xl">
                  No more 50% upfront that vanishes. No more chasing invoices.
                  Client funds upfront, you deliver, payment releases automatically.
                </p>

                <div className="flex items-center gap-4">
                  <Link href="/create" className="btn-primary">
                    Create a Deal
                  </Link>
                  <Link href="#how-it-works" className="btn-ghost">
                    How it works
                  </Link>
                </div>

                {/* Pain points */}
                <div className="pt-8 space-y-3">
                  <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">No More</p>
                  <div className="flex flex-wrap gap-3">
                    {['Ghosting after delivery', 'Endless invoice follow-ups', 'Working for "exposure"', '"I\'ll pay next week"'].map((item) => (
                      <span key={item} className="px-3 py-1 border border-border text-sm text-muted">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column - Visual Element */}
              <div className="lg:col-span-5">
                <div className="relative">
                  {/* Decorative background */}
                  <div className="absolute -top-4 -right-4 w-full h-full border-2 border-forest" />

                  {/* Main card */}
                  <div className="relative bg-surface border-2 border-foreground p-8 space-y-6">
                    <div className="flex items-center justify-between">
                      <span className="text-micro uppercase tracking-widest text-muted">Example</span>
                      <span className="badge-success">Ready</span>
                    </div>

                    <div className="space-y-1">
                      <p className="text-caption text-muted">Mix & Master</p>
                      <p className="text-3xl font-light">€200.00</p>
                    </div>

                    <div className="h-px bg-border" />

                    <div className="space-y-3">
                      <div className="flex items-center gap-3 text-sm">
                        <span className="w-5 h-5 border border-forest flex items-center justify-center">
                          <span className="w-2 h-2 bg-forest" />
                        </span>
                        <span className="text-muted">Client pays → money locked</span>
                      </div>
                      <div className="flex items-center gap-3 text-sm">
                        <span className="w-5 h-5 border border-forest flex items-center justify-center">
                          <span className="w-2 h-2 bg-forest" />
                        </span>
                        <span className="text-muted">You deliver → payment released</span>
                      </div>
                    </div>

                    <Link
                      href="/create"
                      className="block w-full text-center py-3 bg-forest text-white font-medium hover:bg-forest/90 transition-colors"
                    >
                      Create this deal
                    </Link>
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
                Three steps to get paid
              </h2>
            </div>

            <div className="grid md:grid-cols-3 gap-px bg-border">
              {[
                {
                  step: '01',
                  title: 'Create Deal',
                  description: 'Define the work: Mix & Master, Beat, Recording session. Set your price. Get a payment link.',
                },
                {
                  step: '02',
                  title: 'Client Funds',
                  description: 'Share the link. Client pays via card. Money is locked securely until you deliver.',
                },
                {
                  step: '03',
                  title: 'Deliver & Get Paid',
                  description: 'Submit your work. Payment releases instantly to your account. Done.',
                },
              ].map((item) => (
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

        {/* Use Cases */}
        <section className="py-30">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="grid lg:grid-cols-2 gap-20">
              <div>
                <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Works For</p>
                <h2 className="text-headline text-foreground mb-6">
                  Any music service
                </h2>
                <p className="text-body text-muted max-w-md">
                  From mixing to mastering, beat production to recording sessions.
                  If you create it and they pay for it, SYMIONE handles the rest.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {[
                  'Mix & Master',
                  'Beat Production',
                  'Recording Session',
                  'Sound Design',
                  'Podcast Editing',
                  'Ghost Production',
                  'Vocal Tuning',
                  'Album Artwork',
                ].map((item) => (
                  <div key={item} className="p-4 border-2 border-border hover:border-forest transition-colors">
                    <p className="text-body">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-30 bg-forest">
          <div className="max-w-7xl mx-auto px-6 lg:px-12 text-center">
            <h2 className="text-headline text-white mb-6">
              Stop working for free
            </h2>
            <p className="text-xl font-light text-white/70 max-w-xl mx-auto mb-10">
              Create your first deal in under a minute. Get paid when you deliver.
            </p>
            <Link
              href="/create"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-forest font-medium border-2 border-white transition-all duration-200 hover:bg-transparent hover:text-white"
            >
              Create Your First Deal
            </Link>
            <p className="text-sm text-white/50 mt-6">
              Free to create · 5% only on successful payments · Powered by Stripe
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-8 border-t-2 border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-2 h-2 bg-forest" />
              <span className="text-micro uppercase tracking-widest text-muted">SYMIONE</span>
            </Link>
            <p className="text-micro text-muted">
              Payments that execute
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
