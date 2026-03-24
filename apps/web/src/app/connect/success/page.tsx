'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { getAccountByUser, getAccountStatus, type ConnectedAccount, type AccountStatus } from '@/lib/api/connect'

export default function ConnectSuccess() {
  const [account, setAccount] = useState<ConnectedAccount | null>(null)
  const [status, setStatus] = useState<AccountStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Mock user (replace with real auth)
  const [userId] = useState('user_demo')

  useEffect(() => {
    async function checkStatus() {
      try {
        const accountData = await getAccountByUser(userId)
        setAccount(accountData)

        // Get fresh status from Stripe
        const statusData = await getAccountStatus(accountData.id)
        setStatus(statusData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to check account status')
      } finally {
        setLoading(false)
      }
    }

    checkStatus()
  }, [userId])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-forest border-t-transparent animate-spin mx-auto mb-4" />
          <p className="text-sm opacity-50">Checking account status...</p>
        </div>
      </div>
    )
  }

  if (error) {
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
            <div className="w-12 h-12 bg-red-500/10 flex items-center justify-center mx-auto mb-6">
              <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-xl font-medium mb-4">Something went wrong</h1>
            <p className="text-sm opacity-50 mb-8">{error}</p>
            <Link
              href="/connect/onboarding"
              className="px-6 py-3 bg-forest text-background text-[10px] font-medium tracking-[0.15em] uppercase hover:opacity-90 transition-opacity"
            >
              Try Again
            </Link>
          </div>
        </main>
      </div>
    )
  }

  const isReady = status?.can_transact || account?.can_transact

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
          {isReady ? (
            <>
              <div className="w-12 h-12 bg-forest flex items-center justify-center mx-auto mb-6">
                <svg className="w-6 h-6 text-background" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-xl font-medium mb-4">Ready to go</h1>
              <p className="text-sm opacity-50 mb-8">
                Your account is verified. You can now create and accept challenges.
              </p>

              {/* Account Status */}
              <div className="p-5 border border-border/50 mb-8 text-left">
                <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-4">Account Status</p>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="opacity-50">Charges</span>
                    <span className={status?.charges_enabled ? 'text-forest' : 'text-red-500'}>
                      {status?.charges_enabled ? 'Enabled' : 'Pending'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="opacity-50">Payouts</span>
                    <span className={status?.payouts_enabled ? 'text-forest' : 'text-red-500'}>
                      {status?.payouts_enabled ? 'Enabled' : 'Pending'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="opacity-50">Verification</span>
                    <span className={status?.details_submitted ? 'text-forest' : 'opacity-50'}>
                      {status?.details_submitted ? 'Complete' : 'Pending'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center gap-4">
                <Link
                  href="/challenge/new"
                  className="px-6 py-3 bg-forest text-background text-[10px] font-medium tracking-[0.15em] uppercase hover:opacity-90 transition-opacity"
                >
                  Create Challenge
                </Link>
                <Link
                  href="/challenge"
                  className="text-[10px] font-medium tracking-[0.12em] uppercase opacity-50 hover:opacity-70 transition-opacity"
                >
                  Browse
                </Link>
              </div>
            </>
          ) : (
            <>
              <div className="w-12 h-12 bg-yellow-500/10 flex items-center justify-center mx-auto mb-6">
                <svg className="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h1 className="text-xl font-medium mb-4">Almost there</h1>
              <p className="text-sm opacity-50 mb-8">
                Your account is being reviewed. This usually takes a few minutes.
              </p>

              {status?.requirements && status.requirements.currently_due.length > 0 && (
                <div className="p-5 border border-border/50 mb-8 text-left">
                  <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-4">Pending</p>
                  <ul className="space-y-2 text-sm">
                    {status.requirements.currently_due.map((req) => (
                      <li key={req} className="flex items-center gap-2 opacity-70">
                        <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full" />
                        {req.replace(/_/g, ' ')}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex items-center justify-center gap-4">
                <Link
                  href="/connect/onboarding"
                  className="px-6 py-3 bg-forest text-background text-[10px] font-medium tracking-[0.15em] uppercase hover:opacity-90 transition-opacity"
                >
                  Complete Setup
                </Link>
                <Link
                  href="/challenge"
                  className="text-[10px] font-medium tracking-[0.12em] uppercase opacity-50 hover:opacity-70 transition-opacity"
                >
                  Continue Later
                </Link>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
