'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js'
import {
  getMarketplaceTemplate,
  createTemplatePurchase,
  confirmTemplatePurchase,
  formatPrice,
  type MarketplaceTemplate,
  type PurchaseResponse,
} from '@/lib/api/templates'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '')

export default function PurchasePage() {
  const params = useParams()
  const templateId = params.id as string

  const [template, setTemplate] = useState<MarketplaceTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [step, setStep] = useState<'email' | 'payment' | 'success'>('email')
  const [purchaseData, setPurchaseData] = useState<PurchaseResponse | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await getMarketplaceTemplate(templateId)
        if (data.price === 0) {
          setError('This template is free. No purchase required.')
        } else {
          setTemplate(data)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load template')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [templateId])

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email) return

    setLoading(true)
    setError(null)

    try {
      const data = await createTemplatePurchase(templateId, email)
      setPurchaseData(data)
      setStep('payment')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create payment')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !template) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted">Loading...</p>
      </div>
    )
  }

  if (error && !template) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-muted mb-4">{error}</p>
          <Link href="/templates" className="btn-ghost">
            Back to templates
          </Link>
        </div>
      </div>
    )
  }

  if (!template) return null

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b-2 border-border">
        <div className="max-w-lg mx-auto px-6">
          <div className="flex items-center justify-between h-14">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 bg-forest" />
              <span className="text-[10px] font-medium tracking-[0.15em] uppercase">SYMI</span>
            </Link>
            <Link
              href={`/templates/${templateId}`}
              className="text-[10px] tracking-[0.12em] uppercase opacity-40 hover:opacity-70 transition-opacity"
            >
              Cancel
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 pt-14 pb-8">
        <div className="max-w-lg mx-auto px-6 py-8">
          {/* Progress */}
          <div className="flex items-center justify-center gap-4 mb-12">
            <StepIndicator step={1} active={step === 'email'} completed={step !== 'email'} label="Email" />
            <div className="w-12 h-px bg-border" />
            <StepIndicator step={2} active={step === 'payment'} completed={step === 'success'} label="Pay" />
            <div className="w-12 h-px bg-border" />
            <StepIndicator step={3} active={step === 'success'} completed={false} label="Access" />
          </div>

          {/* Template Info */}
          <div className="text-center mb-10">
            <span className="text-5xl mb-4 block">{template.icon}</span>
            <h1 className="text-2xl font-light text-foreground mb-2">{template.name}</h1>
            <p className="text-3xl font-light text-forest">{formatPrice(template.price)}</p>
            <p className="text-micro text-muted mt-1">One-time payment</p>
          </div>

          {/* Email Step */}
          {step === 'email' && (
            <form onSubmit={handleEmailSubmit} className="space-y-6">
              <div>
                <label className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-3 block">
                  Where should we send access?
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full px-4 py-4 text-lg bg-surface border-2 border-border focus:border-forest outline-none transition-colors"
                  autoFocus
                />
              </div>

              {error && (
                <div className="p-4 border border-red-500/50 bg-red-500/5 text-red-400 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !email}
                className={`w-full py-4 text-[11px] font-medium tracking-[0.15em] uppercase transition-all duration-200 ${
                  email
                    ? 'bg-forest text-background hover:opacity-90'
                    : 'bg-border/50 text-muted cursor-not-allowed'
                }`}
              >
                {loading ? 'Loading...' : 'Continue to Payment'}
              </button>
            </form>
          )}

          {/* Payment Step */}
          {step === 'payment' && purchaseData && (
            <Elements
              stripe={stripePromise}
              options={{
                clientSecret: purchaseData.client_secret,
                appearance: {
                  theme: 'night',
                  variables: {
                    colorPrimary: '#22C55E',
                    colorBackground: '#0A0A0A',
                    colorText: '#FAFAFA',
                    colorDanger: '#EF4444',
                    fontFamily: 'ui-sans-serif, system-ui, sans-serif',
                    borderRadius: '0px',
                  },
                  rules: {
                    '.Input': {
                      border: '2px solid #27272A',
                      boxShadow: 'none',
                    },
                    '.Input:focus': {
                      border: '2px solid #22C55E',
                      boxShadow: 'none',
                    },
                  },
                },
              }}
            >
              <PaymentForm
                purchaseData={purchaseData}
                email={email}
                onSuccess={() => setStep('success')}
                onError={setError}
              />
            </Elements>
          )}

          {/* Success Step */}
          {step === 'success' && (
            <div className="text-center space-y-6">
              <div className="w-16 h-16 mx-auto bg-forest/10 border-2 border-forest flex items-center justify-center">
                <span className="text-forest text-2xl">✓</span>
              </div>

              <div>
                <h2 className="text-xl font-medium text-foreground mb-2">You&apos;re in!</h2>
                <p className="text-muted">Check your email for access details.</p>
              </div>

              <div className="p-6 bg-surface border-2 border-border text-left space-y-4">
                <div>
                  <p className="text-micro uppercase tracking-widest text-muted mb-1">What happens next</p>
                  <p className="text-sm text-foreground">
                    We&apos;ll send you access to the private repository within 1 hour.
                    You&apos;ll be added as a collaborator on GitHub and receive deployment instructions.
                  </p>
                </div>

                <div>
                  <p className="text-micro uppercase tracking-widest text-muted mb-1">Questions?</p>
                  <p className="text-sm text-foreground">
                    Reply to the email or contact{' '}
                    <a href="mailto:support@symione.com" className="text-forest hover:underline">
                      support@symione.com
                    </a>
                  </p>
                </div>
              </div>

              <Link href="/templates" className="btn-ghost inline-block">
                Back to Templates
              </Link>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function StepIndicator({
  step,
  active,
  completed,
  label,
}: {
  step: number
  active: boolean
  completed: boolean
  label: string
}) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`w-8 h-8 flex items-center justify-center border-2 text-sm font-medium transition-colors ${
          completed
            ? 'bg-forest border-forest text-background'
            : active
              ? 'border-forest text-forest'
              : 'border-border text-muted'
        }`}
      >
        {completed ? '✓' : step}
      </div>
      <span className="text-[9px] uppercase tracking-widest text-muted">{label}</span>
    </div>
  )
}

function PaymentForm({
  purchaseData,
  email,
  onSuccess,
  onError,
}: {
  purchaseData: PurchaseResponse
  email: string
  onSuccess: () => void
  onError: (error: string) => void
}) {
  const stripe = useStripe()
  const elements = useElements()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!stripe || !elements) return

    setLoading(true)
    setError(null)

    try {
      const { error: submitError } = await elements.submit()
      if (submitError) {
        throw new Error(submitError.message)
      }

      const { error: confirmError, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/templates/${purchaseData.template_id}/purchase?success=true`,
        },
        redirect: 'if_required',
      })

      if (confirmError) {
        throw new Error(confirmError.message)
      }

      if (paymentIntent?.status === 'succeeded') {
        // Confirm on backend and get delivery info
        await confirmTemplatePurchase(purchaseData.payment_intent_id, email)
        onSuccess()
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Payment failed'
      setError(message)
      onError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-3 block">
          Payment Details
        </label>
        <PaymentElement />
      </div>

      {error && (
        <div className="p-4 border border-red-500/50 bg-red-500/5 text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="pt-4">
        <button
          type="submit"
          disabled={loading || !stripe || !elements}
          className={`w-full py-4 text-[11px] font-medium tracking-[0.15em] uppercase transition-all duration-200 ${
            !loading
              ? 'bg-forest text-background hover:opacity-90'
              : 'bg-border/50 text-muted cursor-not-allowed'
          }`}
        >
          {loading ? 'Processing...' : `Pay ${formatPrice(purchaseData.amount)}`}
        </button>

        <p className="text-[9px] text-center opacity-30 mt-3">
          Processed securely by Stripe
        </p>
      </div>
    </form>
  )
}
