'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { createAgreement } from '@/lib/api'

const SERVICES = [
  'Mix & Master',
  'Beat Production',
  'Recording Session',
  'Sound Design',
  'Podcast Editing',
  'Ghost Production',
  'Vocal Tuning',
  'Album Artwork',
  'Other',
]

type PageState = 'form' | 'creating' | 'success' | 'error'

interface AgreementResult {
  fundingUrl: string
  submitUrl: string
  title: string
  amount: number
}

export default function MusicPage() {
  const [state, setState] = useState<PageState>('form')
  const [service, setService] = useState('')
  const [customService, setCustomService] = useState('')
  const [price, setPrice] = useState<number | ''>('')
  const [email, setEmail] = useState('')
  const [mounted, setMounted] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<AgreementResult | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const displayService = service === 'Other' ? customService : service
  const isValid = displayService && price && Number(price) >= 1

  const handleSubmit = async () => {
    if (!isValid) return
    setState('creating')
    setError('')

    try {
      const response = await createAgreement({
        title: displayService,
        description: `${displayService} - Payment via SYMIONE`,
        amount: Number(price),
        currency: 'EUR',
        proof_type: 'file',
        validation_config: {
          require_file: true,
          auto_approve: false,
        },
        ...(email && { payee_email: email }),
      })

      setResult({
        fundingUrl: response.funding_url,
        submitUrl: response.submit_url,
        title: displayService,
        amount: Number(price),
      })
      setState('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setState('error')
    }
  }

  const handleCopy = async () => {
    if (!result) return
    await navigator.clipboard.writeText(result.fundingUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleReset = () => {
    setState('form')
    setService('')
    setCustomService('')
    setPrice('')
    setEmail('')
    setResult(null)
    setError('')
  }

  return (
    <>
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,400&family=Inter:wght@400;500&display=swap');

        .music-page {
          --paper: #FAF8F2;
          --ink: #1A1A1A;
          --green: #1B4332;
          --warmgrey: #C9C5BC;
          --faint: #E8E5DE;
          font-family: 'Inter', system-ui, sans-serif;
        }

        .music-page::before {
          content: "";
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          opacity: 0.025;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        }

        .font-serif {
          font-family: 'Cormorant Garamond', Georgia, serif;
        }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .animate-fade-up {
          animation: fadeUp 0.7s ease-out forwards;
        }

        .animate-fade-in {
          animation: fadeIn 0.5s ease-out forwards;
        }

        .animate-pulse {
          animation: pulse 1.5s ease-in-out infinite;
        }

        .delay-1 { animation-delay: 0.1s; opacity: 0; }
        .delay-2 { animation-delay: 0.2s; opacity: 0; }
      `}</style>

      <div className="music-page min-h-screen flex flex-col" style={{ background: 'var(--paper)' }}>
        {/* Header */}
        <header style={{ borderBottom: '0.5px solid var(--faint)' }}>
          <div className="max-w-2xl mx-auto px-6 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 hover:opacity-70 transition-opacity">
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                <rect x="2" y="2" width="16" height="16" rx="2" stroke="var(--ink)" strokeWidth="1.5" fill="none"/>
                <path d="M6 10l3 3 5-6" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span className="text-[10px] font-medium tracking-[0.25em]" style={{ color: 'var(--ink)' }}>
                SYMIONE
              </span>
            </Link>

            <nav className="flex items-center gap-6">
              <Link
                href="/how-it-works"
                className="text-[10px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.4 }}
              >
                How it works
              </Link>
              <Link
                href="/legal"
                className="text-[10px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.4 }}
              >
                Legal
              </Link>
            </nav>
          </div>
        </header>

        {/* Main */}
        <main className="flex-1 flex items-center justify-center px-6 py-12 relative z-10">
          <div className="w-full max-w-sm">

            {/* ===== FORM STATE ===== */}
            {(state === 'form' || state === 'creating') && mounted && (
              <>
                {/* Title */}
                <div className="text-center mb-10 animate-fade-up">
                  <h1
                    className="font-serif text-[28px] tracking-[-0.02em] mb-3"
                    style={{ color: 'var(--ink)', fontWeight: 400 }}
                  >
                    Conditional Payment
                  </h1>
                  <p
                    className="text-[13px] leading-relaxed"
                    style={{ color: 'var(--ink)', opacity: 0.4 }}
                  >
                    Create a payment link. Get paid when you deliver.
                  </p>
                </div>

                {/* Card */}
                <div
                  className="relative p-8 animate-fade-up delay-1"
                  style={{
                    background: 'var(--paper)',
                    border: '0.5px solid var(--faint)',
                    boxShadow: '0 4px 24px rgba(0,0,0,0.03)',
                    opacity: state === 'creating' ? 0.6 : 1,
                    pointerEvents: state === 'creating' ? 'none' : 'auto',
                  }}
                >
                  {/* Corner accents */}
                  <div className="absolute -top-px -left-px h-4 w-4 border-l border-t" style={{ borderColor: 'var(--warmgrey)' }} />
                  <div className="absolute -top-px -right-px h-4 w-4 border-r border-t" style={{ borderColor: 'var(--warmgrey)' }} />
                  <div className="absolute -bottom-px -left-px h-4 w-4 border-l border-b" style={{ borderColor: 'var(--warmgrey)' }} />
                  <div className="absolute -bottom-px -right-px h-4 w-4 border-r border-b" style={{ borderColor: 'var(--warmgrey)' }} />

                  {/* Service */}
                  <div className="mb-5">
                    <label className="block text-[9px] font-medium tracking-[0.2em] mb-2" style={{ color: 'var(--ink)', opacity: 0.35 }}>
                      SERVICE
                    </label>
                    <select
                      value={service}
                      onChange={(e) => setService(e.target.value)}
                      className="w-full p-3 text-[14px] bg-transparent cursor-pointer focus:outline-none transition-colors"
                      style={{ border: '0.5px solid var(--faint)', color: service ? 'var(--ink)' : 'var(--warmgrey)' }}
                    >
                      <option value="">Select service...</option>
                      {SERVICES.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>

                  {/* Custom service */}
                  {service === 'Other' && (
                    <div className="mb-5">
                      <label className="block text-[9px] font-medium tracking-[0.2em] mb-2" style={{ color: 'var(--ink)', opacity: 0.35 }}>
                        DESCRIBE
                      </label>
                      <input
                        type="text"
                        value={customService}
                        onChange={(e) => setCustomService(e.target.value)}
                        placeholder="e.g., 3 track EP mix"
                        className="w-full p-3 text-[14px] bg-transparent focus:outline-none transition-colors"
                        style={{ border: '0.5px solid var(--faint)', color: 'var(--ink)' }}
                      />
                    </div>
                  )}

                  {/* Price */}
                  <div className="mb-5">
                    <label className="block text-[9px] font-medium tracking-[0.2em] mb-2" style={{ color: 'var(--ink)', opacity: 0.35 }}>
                      PRICE
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[14px]" style={{ color: 'var(--warmgrey)' }}>€</span>
                      <input
                        type="number"
                        value={price}
                        onChange={(e) => setPrice(e.target.value ? Number(e.target.value) : '')}
                        placeholder="200"
                        min={1}
                        className="w-full p-3 pl-8 text-[14px] bg-transparent focus:outline-none transition-colors"
                        style={{ border: '0.5px solid var(--faint)', color: 'var(--ink)' }}
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div className="mb-6">
                    <label className="block text-[9px] font-medium tracking-[0.2em] mb-2" style={{ color: 'var(--ink)', opacity: 0.35 }}>
                      YOUR EMAIL <span style={{ opacity: 0.5 }}>(optional)</span>
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@email.com"
                      className="w-full p-3 text-[14px] bg-transparent focus:outline-none transition-colors"
                      style={{ border: '0.5px solid var(--faint)', color: 'var(--ink)' }}
                    />
                  </div>

                  {/* Submit */}
                  <button
                    onClick={handleSubmit}
                    disabled={!isValid || state === 'creating'}
                    className="w-full py-3.5 text-[12px] font-medium tracking-[0.15em] transition-all hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed"
                    style={{ background: 'var(--green)', color: '#fff' }}
                  >
                    {state === 'creating' ? (
                      <span className="animate-pulse">CREATING...</span>
                    ) : (
                      'GET PAYMENT LINK'
                    )}
                  </button>

                  {/* Tagline */}
                  <div className="mt-6 pt-5 text-center" style={{ borderTop: '0.5px solid var(--faint)' }}>
                    <p className="text-[11px] italic font-serif" style={{ color: 'var(--ink)', opacity: 0.35 }}>
                      Payment unlocks when you confirm delivery
                    </p>
                  </div>
                </div>
              </>
            )}

            {/* ===== SUCCESS STATE ===== */}
            {state === 'success' && result && mounted && (
              <>
                {/* Title */}
                <div className="text-center mb-10 animate-fade-up">
                  <div className="flex items-center justify-center gap-2 mb-4">
                    <span className="h-2 w-2 rounded-full" style={{ background: 'var(--green)' }} />
                    <span className="text-[9px] font-medium tracking-[0.2em]" style={{ color: 'var(--green)' }}>
                      READY
                    </span>
                  </div>
                  <h1 className="font-serif text-[28px] tracking-[-0.02em] mb-3" style={{ color: 'var(--ink)', fontWeight: 400 }}>
                    Payment link created
                  </h1>
                  <p className="text-[13px] leading-relaxed" style={{ color: 'var(--ink)', opacity: 0.4 }}>
                    Share this link with your client to get paid.
                  </p>
                </div>

                {/* Result Card */}
                <div
                  className="relative p-8 animate-fade-up delay-1"
                  style={{
                    background: 'var(--paper)',
                    border: '0.5px solid var(--faint)',
                    boxShadow: '0 4px 24px rgba(0,0,0,0.03)'
                  }}
                >
                  {/* Corner accents */}
                  <div className="absolute -top-px -left-px h-4 w-4 border-l border-t" style={{ borderColor: 'var(--green)' }} />
                  <div className="absolute -top-px -right-px h-4 w-4 border-r border-t" style={{ borderColor: 'var(--green)' }} />
                  <div className="absolute -bottom-px -left-px h-4 w-4 border-l border-b" style={{ borderColor: 'var(--green)' }} />
                  <div className="absolute -bottom-px -right-px h-4 w-4 border-r border-b" style={{ borderColor: 'var(--green)' }} />

                  {/* Summary */}
                  <div className="mb-6 pb-6" style={{ borderBottom: '0.5px solid var(--faint)' }}>
                    <p className="text-[9px] font-medium tracking-[0.2em] mb-2" style={{ color: 'var(--ink)', opacity: 0.35 }}>
                      SERVICE
                    </p>
                    <p className="text-[16px]" style={{ color: 'var(--ink)' }}>{result.title}</p>
                    <p className="font-serif text-[24px] mt-2" style={{ color: 'var(--green)' }}>€{result.amount}</p>
                  </div>

                  {/* Payment Link */}
                  <div className="mb-4">
                    <p className="text-[9px] font-medium tracking-[0.2em] mb-2" style={{ color: 'var(--ink)', opacity: 0.35 }}>
                      PAYMENT LINK
                    </p>
                    <div
                      className="p-3 text-[12px] break-all"
                      style={{ background: 'rgba(27, 67, 50, 0.05)', border: '0.5px solid var(--faint)', color: 'var(--ink)' }}
                    >
                      {result.fundingUrl}
                    </div>
                  </div>

                  {/* Copy Button */}
                  <button
                    onClick={handleCopy}
                    className="w-full py-3.5 text-[12px] font-medium tracking-[0.15em] transition-all hover:opacity-90"
                    style={{ background: 'var(--green)', color: '#fff' }}
                  >
                    {copied ? '✓ COPIED' : 'COPY LINK'}
                  </button>

                  {/* Submit URL (secondary) */}
                  <div className="mt-6 pt-5" style={{ borderTop: '0.5px solid var(--faint)' }}>
                    <p className="text-[9px] font-medium tracking-[0.2em] mb-2" style={{ color: 'var(--ink)', opacity: 0.25 }}>
                      YOUR SUBMIT LINK (for when you deliver)
                    </p>
                    <p className="text-[11px] break-all" style={{ color: 'var(--ink)', opacity: 0.4 }}>
                      {result.submitUrl}
                    </p>
                  </div>
                </div>

                {/* Create Another */}
                <div className="mt-8 text-center animate-fade-in delay-2">
                  <button
                    onClick={handleReset}
                    className="text-[11px] tracking-[0.1em] transition-opacity hover:opacity-60"
                    style={{ color: 'var(--ink)', opacity: 0.4 }}
                  >
                    Create another payment →
                  </button>
                </div>
              </>
            )}

            {/* ===== ERROR STATE ===== */}
            {state === 'error' && mounted && (
              <>
                <div className="text-center mb-10 animate-fade-up">
                  <h1 className="font-serif text-[28px] tracking-[-0.02em] mb-3" style={{ color: 'var(--ink)', fontWeight: 400 }}>
                    Something went wrong
                  </h1>
                  <p className="text-[13px] leading-relaxed" style={{ color: '#c00' }}>
                    {error}
                  </p>
                </div>

                <button
                  onClick={handleReset}
                  className="w-full py-3.5 text-[12px] font-medium tracking-[0.15em] transition-all hover:opacity-90"
                  style={{ background: 'var(--green)', color: '#fff' }}
                >
                  TRY AGAIN
                </button>
              </>
            )}

            {/* Status */}
            {state === 'form' && mounted && (
              <div className="mt-8 flex items-center justify-center gap-6 animate-fade-in delay-2">
                <div className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: 'var(--green)' }} />
                  <span className="text-[9px] tracking-[0.15em]" style={{ color: 'var(--ink)', opacity: 0.3 }}>
                    STRIPE SECURED
                  </span>
                </div>
                <span style={{ color: 'var(--faint)' }}>·</span>
                <span className="text-[9px] tracking-[0.15em]" style={{ color: 'var(--ink)', opacity: 0.3 }}>
                  5% ON SUCCESS
                </span>
              </div>
            )}
          </div>
        </main>

        {/* Footer */}
        <footer style={{ borderTop: '0.5px solid var(--faint)' }}>
          <div className="max-w-2xl mx-auto px-6 py-6 flex items-center justify-between">
            <span className="text-[9px] tracking-[0.2em]" style={{ color: 'var(--ink)', opacity: 0.2 }}>
              SYMIONE · PARIS
            </span>
            <div className="flex items-center gap-4">
              <Link
                href="/privacy"
                className="text-[9px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.25 }}
              >
                Privacy
              </Link>
              <span style={{ color: 'var(--faint)' }}>·</span>
              <a
                href="mailto:contact@symione.com"
                className="text-[9px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.25 }}
              >
                Contact
              </a>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}
