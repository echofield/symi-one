'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createAgreement } from '@/lib/api'

export default function CreateAgreementPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{
    fundingUrl: string
    submitUrl: string
  } | null>(null)

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    amount: '',
    currency: 'usd',
    proof_type: 'url' as 'url' | 'file',
    payer_email: '',
    payee_email: '',
    require_status_200: true,
    allowed_domains: '',
    min_lighthouse_score: '',
    allowed_mime_types: '',
    max_size_mb: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const validationConfig: Record<string, unknown> = {}

      if (formData.proof_type === 'url') {
        validationConfig.require_status_200 = formData.require_status_200
        if (formData.allowed_domains) {
          validationConfig.allowed_domains = formData.allowed_domains.split(',').map(d => d.trim())
        }
        if (formData.min_lighthouse_score) {
          validationConfig.min_lighthouse_score = parseInt(formData.min_lighthouse_score)
        }
      } else {
        if (formData.allowed_mime_types) {
          validationConfig.allowed_mime_types = formData.allowed_mime_types.split(',').map(m => m.trim())
        }
        if (formData.max_size_mb) {
          validationConfig.max_size_mb = parseInt(formData.max_size_mb)
        }
      }

      const response = await createAgreement({
        title: formData.title,
        description: formData.description,
        amount: parseFloat(formData.amount),
        currency: formData.currency,
        proof_type: formData.proof_type,
        validation_config: validationConfig,
        payer_email: formData.payer_email || undefined,
        payee_email: formData.payee_email || undefined,
      })

      setResult({
        fundingUrl: response.funding_url,
        submitUrl: response.submit_url,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create agreement')
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="flex items-center h-16">
              <Link href="/" className="flex items-center gap-3">
                <div className="w-3 h-3 bg-forest" />
                <span className="text-sm font-medium tracking-wider uppercase">SYMIONE PAY</span>
              </Link>
            </div>
          </div>
        </header>

        <main className="max-w-2xl mx-auto px-6 py-20">
          <div className="opacity-0 animate-fade-up">
            {/* Success Icon */}
            <div className="w-16 h-16 border-2 border-forest flex items-center justify-center mb-8">
              <svg className="w-8 h-8 text-forest" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Success</p>
            <h1 className="text-headline text-foreground mb-8">
              Execution Created
            </h1>

            <p className="text-body text-muted mb-12">
              Share these URLs with the appropriate parties to begin the payment process.
            </p>

            {/* Funding URL */}
            <div className="mb-8 opacity-0 animate-fade-up stagger-2">
              <label className="label">Funding URL — Send to Payer</label>
              <div className="card p-4 font-mono text-sm break-all mb-3">
                {result.fundingUrl}
              </div>
              <button
                onClick={() => navigator.clipboard.writeText(result.fundingUrl)}
                className="btn-secondary text-sm py-2"
              >
                Copy Funding URL
              </button>
            </div>

            {/* Submit URL */}
            <div className="mb-12 opacity-0 animate-fade-up stagger-3">
              <label className="label">Submit URL — Send to Creator</label>
              <div className="card p-4 font-mono text-sm break-all mb-3">
                {result.submitUrl}
              </div>
              <button
                onClick={() => navigator.clipboard.writeText(result.submitUrl)}
                className="btn-secondary text-sm py-2"
              >
                Copy Submit URL
              </button>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4 pt-8 border-t-2 border-border opacity-0 animate-fade-up stagger-4">
              <Link href="/create" className="btn-primary">
                Create Another
              </Link>
              <Link href="/" className="btn-ghost">
                Back to Home
              </Link>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b-2 border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center h-16">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-3 h-3 bg-forest" />
              <span className="text-sm font-medium tracking-wider uppercase">SYMIONE PAY</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-20">
        <div className="mb-12 opacity-0 animate-fade-up">
          <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">New Execution</p>
          <h1 className="text-headline text-foreground mb-4">
            Create Execution
          </h1>
          <p className="text-body text-muted">
            Define proof requirements and payment terms. When funded and validated,
            payment releases automatically.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {error && (
            <div className="card border-red-500 bg-red-50 p-4">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Title */}
          <div className="opacity-0 animate-fade-up stagger-1">
            <label htmlFor="title" className="label">Title</label>
            <input
              id="title"
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g., Website Redesign Deliverable"
              className="input"
              required
            />
          </div>

          {/* Description */}
          <div className="opacity-0 animate-fade-up stagger-2">
            <label htmlFor="description" className="label">Description</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe what proof is expected..."
              className="input min-h-[120px] resize-none"
              required
            />
          </div>

          {/* Amount + Currency */}
          <div className="grid grid-cols-2 gap-4 opacity-0 animate-fade-up stagger-3">
            <div>
              <label htmlFor="amount" className="label">Amount</label>
              <input
                id="amount"
                type="number"
                step="0.01"
                min="0.50"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                placeholder="100.00"
                className="input"
                required
              />
            </div>
            <div>
              <label htmlFor="currency" className="label">Currency</label>
              <select
                id="currency"
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="input"
              >
                <option value="usd">USD</option>
                <option value="eur">EUR</option>
                <option value="gbp">GBP</option>
              </select>
            </div>
          </div>

          {/* Proof Type */}
          <div className="opacity-0 animate-fade-up stagger-4">
            <label className="label">Proof Type</label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, proof_type: 'url' })}
                className={`card p-6 text-left transition-all ${
                  formData.proof_type === 'url'
                    ? 'border-forest shadow-sharp -translate-x-1 -translate-y-1'
                    : 'hover:border-forest'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-3 h-3 border-2 ${formData.proof_type === 'url' ? 'bg-forest border-forest' : 'border-border'}`} />
                  <span className="font-medium">URL</span>
                </div>
                <p className="text-caption text-muted">
                  Link to deployed website or resource
                </p>
              </button>

              <button
                type="button"
                onClick={() => setFormData({ ...formData, proof_type: 'file' })}
                className={`card p-6 text-left transition-all ${
                  formData.proof_type === 'file'
                    ? 'border-forest shadow-sharp -translate-x-1 -translate-y-1'
                    : 'hover:border-forest'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-3 h-3 border-2 ${formData.proof_type === 'file' ? 'bg-forest border-forest' : 'border-border'}`} />
                  <span className="font-medium">File</span>
                </div>
                <p className="text-caption text-muted">
                  Upload document or media file
                </p>
              </button>
            </div>
          </div>

          {/* URL Validation Options */}
          {formData.proof_type === 'url' && (
            <div className="card space-y-6 opacity-0 animate-scale-in">
              <p className="text-micro uppercase tracking-widest text-muted">URL Validation Rules</p>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.require_status_200}
                  onChange={(e) => setFormData({ ...formData, require_status_200: e.target.checked })}
                  className="w-4 h-4 border-2 border-border checked:bg-forest checked:border-forest"
                />
                <span className="text-body">Require HTTP 200 status</span>
              </label>

              <div>
                <label htmlFor="allowed_domains" className="label">
                  Allowed Domains
                </label>
                <input
                  id="allowed_domains"
                  type="text"
                  value={formData.allowed_domains}
                  onChange={(e) => setFormData({ ...formData, allowed_domains: e.target.value })}
                  placeholder="example.com, vercel.app"
                  className="input"
                />
                <p className="text-micro text-muted mt-2">Comma-separated. Leave empty to allow any domain.</p>
              </div>

              <div>
                <label htmlFor="min_lighthouse_score" className="label">
                  Minimum Lighthouse Score
                </label>
                <input
                  id="min_lighthouse_score"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.min_lighthouse_score}
                  onChange={(e) => setFormData({ ...formData, min_lighthouse_score: e.target.value })}
                  placeholder="80"
                  className="input"
                />
              </div>
            </div>
          )}

          {/* File Validation Options */}
          {formData.proof_type === 'file' && (
            <div className="card space-y-6 opacity-0 animate-scale-in">
              <p className="text-micro uppercase tracking-widest text-muted">File Validation Rules</p>

              <div>
                <label htmlFor="allowed_mime_types" className="label">
                  Allowed MIME Types
                </label>
                <input
                  id="allowed_mime_types"
                  type="text"
                  value={formData.allowed_mime_types}
                  onChange={(e) => setFormData({ ...formData, allowed_mime_types: e.target.value })}
                  placeholder="image/*, application/pdf"
                  className="input"
                />
                <p className="text-micro text-muted mt-2">Comma-separated. Use * for wildcards.</p>
              </div>

              <div>
                <label htmlFor="max_size_mb" className="label">
                  Maximum File Size (MB)
                </label>
                <input
                  id="max_size_mb"
                  type="number"
                  min="1"
                  max="100"
                  value={formData.max_size_mb}
                  onChange={(e) => setFormData({ ...formData, max_size_mb: e.target.value })}
                  placeholder="10"
                  className="input"
                />
              </div>
            </div>
          )}

          {/* Emails */}
          <div className="grid grid-cols-2 gap-4 opacity-0 animate-fade-up stagger-5">
            <div>
              <label htmlFor="payer_email" className="label">Payer Email (Optional)</label>
              <input
                id="payer_email"
                type="email"
                value={formData.payer_email}
                onChange={(e) => setFormData({ ...formData, payer_email: e.target.value })}
                placeholder="payer@example.com"
                className="input"
              />
            </div>
            <div>
              <label htmlFor="payee_email" className="label">Payee Email (Optional)</label>
              <input
                id="payee_email"
                type="email"
                value={formData.payee_email}
                onChange={(e) => setFormData({ ...formData, payee_email: e.target.value })}
                placeholder="payee@example.com"
                className="input"
              />
            </div>
          </div>

          {/* Submit */}
          <div className="pt-8 opacity-0 animate-fade-up stagger-6">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center"
            >
              {loading ? (
                <>
                  <span className="spinner mr-2" />
                  Creating...
                </>
              ) : (
                'Create Execution'
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  )
}
