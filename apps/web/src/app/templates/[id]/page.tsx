'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import {
  getMarketplaceTemplate,
  formatPrice,
  type MarketplaceTemplate,
} from '@/lib/api/templates'

export default function TemplateDetailPage() {
  const params = useParams()
  const templateId = params.id as string

  const [template, setTemplate] = useState<MarketplaceTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await getMarketplaceTemplate(templateId)
        setTemplate(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load template')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [templateId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted">Loading...</p>
      </div>
    )
  }

  if (error || !template) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-muted mb-4">{error || 'Template not found'}</p>
          <Link href="/templates" className="btn-ghost">
            Back to templates
          </Link>
        </div>
      </div>
    )
  }

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
              <Link href="/templates" className="btn-ghost text-sm">
                All Templates
              </Link>
              <Link href="/challenge/new" className="btn-secondary text-sm py-2 px-4">
                Create Challenge
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 pt-16">
        {/* Hero */}
        <section className="py-20 lg:py-30 border-b-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <Link
              href="/templates"
              className="inline-flex items-center gap-2 text-micro uppercase tracking-widest text-muted hover:text-forest mb-8"
            >
              <span>←</span> All Templates
            </Link>

            <div className="grid lg:grid-cols-2 gap-16 items-start">
              {/* Left - Info */}
              <div className="space-y-8">
                <div className="flex items-start gap-4">
                  <span className="text-5xl">{template.icon}</span>
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h1 className="text-4xl font-light text-foreground">{template.name}</h1>
                      {template.is_pro && (
                        <span className="px-2 py-1 text-[10px] font-medium tracking-wider uppercase bg-forest/10 text-forest border border-forest/20">
                          PRO
                        </span>
                      )}
                    </div>
                    <p className={`text-2xl font-light ${template.price === 0 ? 'text-forest' : 'text-foreground'}`}>
                      {formatPrice(template.price)}
                      {template.price > 0 && <span className="text-muted text-base ml-2">one-time</span>}
                    </p>
                  </div>
                </div>

                <p className="text-xl font-light text-muted leading-relaxed">
                  {template.long_description}
                </p>

                {/* Stack */}
                <div className="flex flex-wrap gap-2">
                  {template.stack.map((tech) => (
                    <span
                      key={tech}
                      className="px-3 py-1.5 text-xs font-medium tracking-wider uppercase bg-surface border border-border"
                    >
                      {tech}
                    </span>
                  ))}
                </div>

                {/* CTA */}
                <div className="flex items-center gap-4 pt-4">
                  {template.price === 0 ? (
                    <>
                      {template.deploy_url && (
                        <a
                          href={template.deploy_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-primary"
                        >
                          Deploy to Vercel
                        </a>
                      )}
                      {template.repo_url && (
                        <a
                          href={template.repo_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-ghost"
                        >
                          View on GitHub
                        </a>
                      )}
                    </>
                  ) : (
                    <Link
                      href={`/templates/${template.id}/purchase`}
                      className="btn-primary"
                    >
                      Purchase — {formatPrice(template.price)}
                    </Link>
                  )}
                </div>
              </div>

              {/* Right - Preview placeholder */}
              <div className="bg-surface border-2 border-border aspect-video flex items-center justify-center">
                <span className="text-8xl opacity-20">{template.icon}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-20 bg-surface">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="grid lg:grid-cols-2 gap-16">
              {/* What's Included */}
              <div>
                <h2 className="text-micro uppercase tracking-[0.3em] text-muted mb-6">
                  What&apos;s Included
                </h2>
                <ul className="space-y-4">
                  {template.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <span className="text-forest mt-1">✓</span>
                      <span className="text-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Fork Ideas */}
              <div>
                <h2 className="text-micro uppercase tracking-[0.3em] text-muted mb-6">
                  Build This Into
                </h2>
                <ul className="space-y-4">
                  {template.use_cases.map((useCase, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <span className="text-muted">→</span>
                      <span className="text-foreground">{useCase}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* How to Deploy */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <h2 className="text-micro uppercase tracking-[0.3em] text-muted mb-8">
              How to Deploy
            </h2>

            {template.price === 0 ? (
              <div className="grid md:grid-cols-3 gap-8">
                {[
                  {
                    step: '01',
                    title: 'Click Deploy',
                    description: 'Click "Deploy to Vercel" to clone the template to your own GitHub.',
                  },
                  {
                    step: '02',
                    title: 'Configure',
                    description: 'Set your environment variables: SYMIONE API key and Stripe keys.',
                  },
                  {
                    step: '03',
                    title: 'Live',
                    description: 'Your conditional payment app is live. Customize and ship.',
                  },
                ].map((item) => (
                  <div key={item.step} className="bg-surface border-2 border-border p-8">
                    <p className="text-3xl font-light text-forest mb-4">{item.step}</p>
                    <h3 className="text-lg font-medium text-foreground mb-2">{item.title}</h3>
                    <p className="text-muted text-sm">{item.description}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid md:grid-cols-3 gap-8">
                {[
                  {
                    step: '01',
                    title: 'Purchase',
                    description: `Pay ${formatPrice(template.price)} once. Lifetime access, no subscriptions.`,
                  },
                  {
                    step: '02',
                    title: 'Receive Access',
                    description: 'Get private repo access and deploy link within 1 hour.',
                  },
                  {
                    step: '03',
                    title: 'Customize & Deploy',
                    description: 'Add your branding, configure your fees, deploy to Vercel.',
                  },
                ].map((item) => (
                  <div key={item.step} className="bg-surface border-2 border-border p-8">
                    <p className="text-3xl font-light text-forest mb-4">{item.step}</p>
                    <h3 className="text-lg font-medium text-foreground mb-2">{item.title}</h3>
                    <p className="text-muted text-sm">{item.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Protocol Info */}
        <section className="py-16 bg-surface border-t-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="flex items-start gap-4">
              <div className="w-3 h-3 bg-forest mt-1.5" />
              <div className="max-w-2xl">
                <h3 className="text-lg font-medium text-foreground mb-2">
                  Runs on SYMIONE Protocol
                </h3>
                <p className="text-muted text-sm leading-relaxed">
                  Built-in escrow, proof validation, dispute resolution, and settlement.
                  You focus on your product. The protocol handles the money.
                  Every transaction processed through this template includes a 5% protocol fee to SYMIONE.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Bottom CTA */}
        <section className="py-20 border-t-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12 text-center">
            {template.price === 0 ? (
              <>
                <h2 className="text-2xl font-light text-foreground mb-6">
                  Ready to build?
                </h2>
                <div className="flex items-center justify-center gap-4">
                  {template.deploy_url && (
                    <a
                      href={template.deploy_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-primary"
                    >
                      Deploy to Vercel
                    </a>
                  )}
                  {template.repo_url && (
                    <a
                      href={template.repo_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-ghost"
                    >
                      View Source
                    </a>
                  )}
                </div>
              </>
            ) : (
              <>
                <h2 className="text-2xl font-light text-foreground mb-6">
                  Ready to build your challenge business?
                </h2>
                <Link
                  href={`/templates/${template.id}/purchase`}
                  className="btn-primary"
                >
                  Purchase {template.name} — {formatPrice(template.price)}
                </Link>
              </>
            )}
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
