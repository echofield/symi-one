'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import {
  getAccountByUser,
  createAccount,
  createOnboardingLink,
  type ConnectedAccount,
} from '@/lib/api/connect'

export default function ConnectOnboarding() {
  const [account, setAccount] = useState<ConnectedAccount | null>(null)
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Mock user (replace with real auth)
  const [userId] = useState('user_demo')
  const [userEmail] = useState('demo@symione.com')

  useEffect(() => {
    async function checkAccount() {
      try {
        const data = await getAccountByUser(userId)
        setAccount(data)
      } catch {
        // No account yet - that's fine
      } finally {
        setLoading(false)
      }
    }
    checkAccount()
  }, [userId])

  async function startOnboarding() {
    setConnecting(true)
    setError(null)

    try {
      // Create account if doesn't exist
      if (!account) {
        await createAccount({
          user_id: userId,
          email: userEmail,
          country: 'FR',
        })
      }

      // Get onboarding link
      const { url } = await createOnboardingLink(
        userId,
        `${window.location.origin}/connect/success`,
        `${window.location.origin}/connect/onboarding`
      )

      // Redirect to Stripe
      window.location.href = url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start onboarding')
      setConnecting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-forest border-t-transparent animate-spin" />
      </div>
    )
  }

  // Account exists and is ready
  if (account?.can_transact) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border/50">
          <div className="max-w-lg mx-auto px-6">
            <div className="flex items-center justify-between h-14">
              <Link href="/challenge" className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 bg-forest" />
                <span className="text-[10px] font-medium tracking-[0.15em] uppercase">SYMI</span>
              </Link>
            </div>
          </div>
        </header>

        <main className="flex-1 pt-14 flex items-center justify-center">
          <div className="max-w-md mx-auto px-6 text-center">
            <div className="w-12 h-12 bg-forest flex items-center justify-center mx-auto mb-6">
              <svg className="w-6 h-6 text-background" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-xl font-medium mb-4">All set</h1>
            <p className="text-sm opacity-50 mb-8">
              Your bank account is connected and ready for challenges.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/challenge/new"
                className="px-6 py-3 bg-forest text-background text-[10px] font-medium tracking-[0.15em] uppercase hover:opacity-90 transition-opacity"
              >
                Create Challenge
              </Link>
              <Link
                href="/challenge/me"
                className="text-[10px] font-medium tracking-[0.12em] uppercase opacity-50 hover:opacity-70 transition-opacity"
              >
                Dashboard
              </Link>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // Account exists but needs more info
  if (account && !account.can_transact) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border/50">
          <div className="max-w-lg mx-auto px-6">
            <div className="flex items-center justify-between h-14">
              <Link href="/challenge" className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 bg-forest" />
                <span className="text-[10px] font-medium tracking-[0.15em] uppercase">SYMI</span>
              </Link>
            </div>
          </div>
        </header>

        <main className="flex-1 pt-14 flex items-center justify-center">
          <div className="max-w-md mx-auto px-6 text-center">
            <div className="w-12 h-12 bg-yellow-500/10 flex items-center justify-center mx-auto mb-6">
              <svg className="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h1 className="text-xl font-medium mb-4">Almost there</h1>
            <p className="text-sm opacity-50 mb-8">
              We need a bit more information to enable payments.
            </p>

            {error && (
              <div className="p-4 border border-red-500/50 bg-red-500/5 text-red-600 text-sm mb-6">
                {error}
              </div>
            )}

            <button
              onClick={startOnboarding}
              disabled={connecting}
              className="px-6 py-3 bg-forest text-background text-[10px] font-medium tracking-[0.15em] uppercase hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {connecting ? 'Redirecting...' : 'Complete Setup'}
            </button>
          </div>
        </main>
      </div>
    )
  }

  // No account - show onboarding prompt
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border/50">
        <div className="max-w-lg mx-auto px-6">
          <div className="flex items-center justify-between h-14">
            <Link href="/challenge" className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 bg-forest" />
              <span className="text-[10px] font-medium tracking-[0.15em] uppercase">SYMI</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 pt-14">
        <div className="max-w-lg mx-auto px-6 py-12">
          <div className="text-center mb-12">
            <h1 className="text-2xl font-light mb-4">Connect your bank</h1>
            <p className="text-sm opacity-50">
              Required to stake money on challenges. Takes about 2 minutes.
            </p>
          </div>

          {/* Steps */}
          <div className="space-y-4 mb-10">
            {[
              { step: '1', title: 'Verify identity', desc: 'Basic ID check for financial regulations' },
              { step: '2', title: 'Link bank account', desc: 'Where you receive winnings' },
              { step: '3', title: 'Start challenging', desc: 'Create and accept challenges immediately' },
            ].map((item) => (
              <div key={item.step} className="flex items-start gap-4 p-4 border border-border/50">
                <div className="w-8 h-8 bg-forest text-background flex items-center justify-center flex-shrink-0 text-sm font-medium">
                  {item.step}
                </div>
                <div>
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-[11px] opacity-50">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Security note */}
          <div className="p-4 bg-surface/50 border border-border/50 mb-10">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-forest flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div>
                <p className="text-sm font-medium">Powered by Stripe</p>
                <p className="text-[11px] opacity-50">
                  We never see your bank details. Stripe handles everything securely.
                </p>
              </div>
            </div>
          </div>

          {error && (
            <div className="p-4 border border-red-500/50 bg-red-500/5 text-red-600 text-sm mb-6">
              {error}
            </div>
          )}

          <div className="text-center">
            <button
              onClick={startOnboarding}
              disabled={connecting}
              className="w-full py-4 bg-forest text-background text-[11px] font-medium tracking-[0.15em] uppercase hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {connecting ? 'Redirecting to Stripe...' : 'Connect with Stripe'}
            </button>
            <p className="text-[9px] opacity-30 mt-3">
              You will be redirected to Stripe secure page
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
