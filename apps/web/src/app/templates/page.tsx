'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import {
  getMarketplaceTemplates,
  formatPrice,
  type MarketplaceTemplate,
} from '@/lib/api/templates'

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<MarketplaceTemplate[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await getMarketplaceTemplates()
        setTemplates(data.templates)
      } catch (error) {
        console.error('Failed to fetch templates:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

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
              <Link href="/challenge" className="btn-ghost text-sm">
                Challenges
              </Link>
              <Link href="/challenge/new" className="btn-secondary text-sm py-2 px-4">
                Create Challenge
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 pt-16">
        <section className="py-20 lg:py-30">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="max-w-3xl space-y-6">
              <p className="text-micro uppercase tracking-[0.3em] text-muted">
                Developer Templates
              </p>
              <h1 className="text-display text-foreground">
                Build on <span className="text-forest">Reliable</span>
              </h1>
              <p className="text-xl font-light text-muted leading-relaxed">
                Conditional payment apps. Pre-built. Fork and deploy in 90 seconds.
                Every template runs on SYMIONE protocol — escrow, disputes, proof validation,
                settlement. You build the product. We handle the money.
              </p>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-12 pt-12">
              <div>
                <p className="text-3xl font-light text-forest">4</p>
                <p className="text-micro uppercase tracking-widest text-muted mt-1">Templates</p>
              </div>
              <div className="w-px h-12 bg-border" />
              <div>
                <p className="text-3xl font-light text-forest">90s</p>
                <p className="text-micro uppercase tracking-widest text-muted mt-1">To Deploy</p>
              </div>
              <div className="w-px h-12 bg-border" />
              <div>
                <p className="text-3xl font-light text-forest">5%</p>
                <p className="text-micro uppercase tracking-widest text-muted mt-1">Protocol Fee</p>
              </div>
            </div>
          </div>
        </section>

        {/* Template Grid */}
        <section className="py-20 bg-surface border-y-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            {loading ? (
              <div className="text-center py-20 text-muted">Loading templates...</div>
            ) : (
              <div className="grid md:grid-cols-2 gap-6">
                {templates.map((template) => (
                  <TemplateCard key={template.id} template={template} />
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Protocol Section */}
        <section className="py-20 lg:py-30">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="max-w-2xl mb-16">
              <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Protocol</p>
              <h2 className="text-headline text-foreground mb-6">
                Every template runs on SYMIONE
              </h2>
              <p className="text-muted text-lg leading-relaxed">
                The SYMIONE protocol handles the hard parts: escrow, proof validation,
                dispute resolution, and settlement. You focus on your vertical.
                We handle the money infrastructure.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-px bg-border">
              {[
                {
                  title: 'Escrow',
                  description: 'Funds held securely by Stripe until conditions are met. No manual releases.',
                },
                {
                  title: 'Proof Validation',
                  description: 'Built-in attestation, file upload, URL, and API-based proof systems.',
                },
                {
                  title: 'Dispute Resolution',
                  description: 'When parties disagree, the protocol handles arbitration and fund distribution.',
                },
                {
                  title: 'Instant Settlement',
                  description: 'Winner receives funds immediately via Stripe Connect Express.',
                },
                {
                  title: 'Compliance',
                  description: 'Stripe handles KYC, tax reporting, and global payment regulations.',
                },
                {
                  title: 'Developer SDK',
                  description: 'TypeScript SDK for custom integrations. Webhooks for all events.',
                },
              ].map((item) => (
                <div key={item.title} className="bg-background p-8">
                  <h3 className="text-lg font-medium text-foreground mb-3">{item.title}</h3>
                  <p className="text-muted text-sm">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Protocol Fee Disclosure */}
        <section className="py-16 border-t-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="max-w-2xl">
              <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Economics</p>
              <h3 className="text-xl font-medium text-foreground mb-4">
                5% Protocol Fee
              </h3>
              <p className="text-muted leading-relaxed">
                Every transaction processed through these templates includes a 5% protocol fee
                to SYMIONE. This funds the protocol, the evaluation engine, dispute resolution,
                and ongoing development. This fee is invisible to your end users but part of
                the infrastructure cost for developers.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t-2 border-border py-10">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-forest" />
              <span className="text-sm font-medium tracking-wider uppercase">SYMIONE</span>
            </div>
            <p className="text-micro text-muted">
              Conditional payment protocol. Powered by Stripe Connect.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

function TemplateCard({ template }: { template: MarketplaceTemplate }) {
  return (
    <div className="group bg-background border-2 border-border hover:border-forest transition-colors">
      <div className="p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <span className="text-4xl">{template.icon}</span>
          <div className="flex items-center gap-2">
            {template.is_pro && (
              <span className="px-2 py-1 text-[10px] font-medium tracking-wider uppercase bg-forest/10 text-forest border border-forest/20">
                PRO
              </span>
            )}
            <span className={`text-lg font-light ${template.price === 0 ? 'text-forest' : 'text-foreground'}`}>
              {formatPrice(template.price)}
            </span>
          </div>
        </div>

        {/* Content */}
        <h3 className="text-xl font-medium text-foreground mb-2">{template.name}</h3>
        <p className="text-muted text-sm mb-4">{template.description}</p>

        {/* Use Cases */}
        <p className="text-micro text-muted mb-6">
          <span className="opacity-60">Fork this for:</span>{' '}
          {template.use_cases.slice(0, 3).join(', ')}
        </p>

        {/* Stack */}
        <div className="flex flex-wrap gap-2 mb-6">
          {template.stack.map((tech) => (
            <span
              key={tech}
              className="px-2 py-1 text-[10px] font-medium tracking-wider uppercase bg-surface border border-border"
            >
              {tech}
            </span>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {template.price === 0 ? (
            <>
              {template.deploy_url && (
                <a
                  href={template.deploy_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary text-sm py-2 px-4"
                >
                  Deploy to Vercel
                </a>
              )}
              {template.repo_url && (
                <a
                  href={template.repo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-ghost text-sm"
                >
                  View on GitHub
                </a>
              )}
            </>
          ) : (
            <Link
              href={`/templates/${template.id}/purchase`}
              className="btn-primary text-sm py-2 px-4"
            >
              Purchase — {formatPrice(template.price)}
            </Link>
          )}
          <Link
            href={`/templates/${template.id}`}
            className="btn-ghost text-sm"
          >
            Learn more
          </Link>
        </div>
      </div>
    </div>
  )
}
