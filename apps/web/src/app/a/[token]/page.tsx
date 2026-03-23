'use client'

import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { getPublicAgreement, fundAgreement } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!)

interface AgreementInfo {
  id: string
  title: string
  description: string
  amount: string
  currency: string
  proof_type: 'url' | 'file'
  status: string
  deadline_at: string | null
  validation_rules: string[]
  is_funded: boolean
  payer_email: string | null
}

function CheckoutForm({ clientSecret }: { clientSecret: string }) {
  const stripe = useStripe()
  const elements = useElements()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!stripe || !elements) return

    setLoading(true)
    setError(null)

    const { error: submitError } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: window.location.href + '?payment=success',
      },
    })

    if (submitError) {
      setError(submitError.message || 'Payment failed')
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="card border-red-500 bg-red-50 p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
      <PaymentElement />
      <button
        type="submit"
        disabled={!stripe || loading}
        className="btn-primary w-full justify-center"
      >
        {loading ? (
          <>
            <span className="spinner mr-2" />
            Processing...
          </>
        ) : (
          'Fund Execution'
        )}
      </button>
    </form>
  )
}

export default function FundingPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const token = params.token as string

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [agreement, setAgreement] = useState<AgreementInfo | null>(null)
  const [clientSecret, setClientSecret] = useState<string | null>(null)
  const [paymentSuccess, setPaymentSuccess] = useState(false)

  useEffect(() => {
    if (searchParams.get('payment') === 'success') {
      setPaymentSuccess(true)
    }
  }, [searchParams])

  useEffect(() => {
    async function load() {
      try {
        const data = await getPublicAgreement(token)
        setAgreement(data)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load agreement')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [token])

  const handleFund = async () => {
    if (!agreement) return

    setLoading(true)
    setError(null)

    try {
      const returnUrl = window.location.href
      const response = await fundAgreement(token, returnUrl)
      setClientSecret(response.client_secret)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to initialize payment')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center gap-3 text-muted">
          <span className="spinner" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

  if (error && !agreement) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="card max-w-md w-full border-red-500">
          <div className="w-12 h-12 border-2 border-red-500 flex items-center justify-center mb-6">
            <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Error</p>
          <h1 className="text-title mb-4">Unable to Load</h1>
          <p className="text-body text-muted mb-6">{error}</p>
          <Link href="/" className="btn-secondary">
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  if (paymentSuccess || agreement?.is_funded) {
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
            <h1 className="text-headline text-foreground mb-4">
              Execution Funded
            </h1>
            <p className="text-body text-muted mb-8">
              The funds have been secured and will be released when proof passes validation.
            </p>

            <div className="card mb-8 opacity-0 animate-fade-up stagger-2">
              <div className="flex items-center justify-between mb-4">
                <span className="badge-success">Funded</span>
              </div>
              <p className="text-4xl font-light mb-2">
                {formatCurrency(agreement?.amount || '0', agreement?.currency)}
              </p>
              <p className="text-body text-muted">{agreement?.title}</p>
            </div>

            <div className="pt-8 border-t-2 border-border opacity-0 animate-fade-up stagger-3">
              <p className="text-caption text-muted">
                The creator can now submit their proof. Payment will release automatically when validation passes.
              </p>
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
        {/* Execution Info */}
        <div className="mb-8 opacity-0 animate-fade-up">
          <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Fund Execution</p>
          <h1 className="text-headline text-foreground mb-4">{agreement?.title}</h1>
          <p className="text-body text-muted">{agreement?.description}</p>
        </div>

        {/* Execution Details Card */}
        <div className="card mb-8 opacity-0 animate-fade-up stagger-1">
          <div className="flex items-center justify-between mb-6">
            <span className="text-micro uppercase tracking-widest text-muted">Amount Due</span>
            <span className="badge-default">{agreement?.status}</span>
          </div>

          <p className="text-4xl font-light mb-6">
            {formatCurrency(agreement?.amount || '0', agreement?.currency)}
          </p>

          <div className="h-px bg-border mb-6" />

          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">Proof Type</span>
              <span className="font-medium capitalize">{agreement?.proof_type}</span>
            </div>

            {agreement?.validation_rules && agreement.validation_rules.length > 0 && (
              <div>
                <p className="text-sm text-muted mb-2">Validation Rules</p>
                <ul className="space-y-2">
                  {agreement.validation_rules.map((rule, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <span className="w-1 h-1 bg-forest" />
                      {rule}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Payment Card */}
        <div className="card opacity-0 animate-fade-up stagger-2">
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Secure Payment</p>
          <h2 className="text-title mb-2">Fund this Execution</h2>
          <p className="text-caption text-muted mb-6">
            Your payment will be held securely until proof is submitted and passes validation.
          </p>

          {error && (
            <div className="card border-red-500 bg-red-50 p-4 mb-6">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {clientSecret ? (
            <Elements
              stripe={stripePromise}
              options={{
                clientSecret,
                appearance: {
                  theme: 'flat',
                  variables: {
                    colorPrimary: '#1B4332',
                    fontFamily: 'var(--font-poppins), system-ui, sans-serif',
                    borderRadius: '0px',
                  },
                },
              }}
            >
              <CheckoutForm clientSecret={clientSecret} />
            </Elements>
          ) : (
            <button
              onClick={handleFund}
              disabled={loading}
              className="btn-primary w-full justify-center"
            >
              {loading ? (
                <>
                  <span className="spinner mr-2" />
                  Loading...
                </>
              ) : (
                `Proceed to Payment — ${formatCurrency(agreement?.amount || '0', agreement?.currency)}`
              )}
            </button>
          )}
        </div>
      </main>
    </div>
  )
}
