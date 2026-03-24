'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect, useCallback } from 'react'
import {
  getChallengeByInvite,
  acceptChallenge,
  formatStake,
  type Challenge,
} from '@/lib/api/challenges'
import { getAccountByUser, createAccount, createOnboardingLink } from '@/lib/api/connect'

export default function ChallengeInvite() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string

  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [loading, setLoading] = useState(true)
  const [accepting, setAccepting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasConnectedAccount, setHasConnectedAccount] = useState<boolean | null>(null)

  // Mock user (replace with real auth)
  const [userId] = useState('user_acceptor_' + Math.random().toString(36).substring(7))
  const [userEmail] = useState('acceptor@symione.com')

  const fetchChallenge = useCallback(async () => {
    try {
      const data = await getChallengeByInvite(token)
      setChallenge(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Challenge not found')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    fetchChallenge()
  }, [fetchChallenge])

  useEffect(() => {
    async function checkAccount() {
      try {
        await getAccountByUser(userId)
        setHasConnectedAccount(true)
      } catch {
        setHasConnectedAccount(false)
      }
    }
    checkAccount()
  }, [userId])

  async function handleConnectStripe() {
    setAccepting(true)
    try {
      await createAccount({ user_id: userId, email: userEmail })
      const { url } = await createOnboardingLink(
        userId,
        `${window.location.origin}/challenge/invite/${token}?return=true`,
        `${window.location.origin}/connect/onboarding`
      )
      window.location.href = url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start Stripe onboarding')
      setAccepting(false)
    }
  }

  async function handleAccept() {
    if (!challenge) return

    setAccepting(true)
    setError(null)

    try {
      await acceptChallenge(challenge.public_id, userId, userEmail)
      router.push(`/challenge/${challenge.public_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to accept challenge')
      setAccepting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-forest border-t-transparent animate-spin" />
      </div>
    )
  }

  if (error || !challenge) {
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
            <h1 className="text-xl font-medium mb-4">Challenge Not Found</h1>
            <p className="text-sm opacity-50 mb-8">
              {error || 'This challenge may have expired or been cancelled.'}
            </p>
            <Link href="/challenge" className="text-[10px] font-medium tracking-[0.12em] uppercase text-forest">
              Browse Challenges
            </Link>
          </div>
        </main>
      </div>
    )
  }

  // Challenge already accepted or not available
  if (challenge.status !== 'pending_acceptance') {
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
            <div className="w-12 h-12 bg-forest/10 flex items-center justify-center mx-auto mb-6">
              <svg className="w-6 h-6 text-forest" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-xl font-medium mb-4">Challenge Active</h1>
            <p className="text-sm opacity-50 mb-8">
              This challenge has already been accepted and is in progress.
            </p>
            <Link
              href={`/challenge/${challenge.public_id}`}
              className="text-[10px] font-medium tracking-[0.12em] uppercase text-forest"
            >
              View Challenge
            </Link>
          </div>
        </main>
      </div>
    )
  }

  const winnings = parseFloat(challenge.stake_amount) * 2 * (1 - parseFloat(challenge.platform_fee_percent) / 100)

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
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

      {/* Main Content */}
      <main className="flex-1 pt-14 pb-32">
        <div className="max-w-lg mx-auto px-6 py-12">
          {/* Headline */}
          <div className="text-center mb-10">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-3">
              Challenge from {challenge.party_a_email?.split('@')[0] || 'Someone'}
            </p>
            <h1 className="text-2xl font-light">Do you accept?</h1>
          </div>

          {/* Challenge Card */}
          <div className="border border-foreground p-6 mb-8">
            <h2 className="text-xl font-medium mb-6">{challenge.title}</h2>

            <div className="h-px bg-border/50 mb-6" />

            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-1">Your stake</p>
                <p className="text-2xl font-light">
                  {formatStake(challenge.stake_amount, challenge.currency)}
                </p>
              </div>
              <div>
                <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-1">Winner takes</p>
                <p className="text-2xl font-light text-forest">
                  {formatStake(String(winnings.toFixed(2)), challenge.currency)}
                </p>
              </div>
            </div>

            {challenge.proof_deadline && (
              <div className="mt-6 pt-4 border-t border-border/50">
                <p className="text-sm opacity-50">
                  Deadline: {new Date(challenge.proof_deadline).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>

          {/* Connect Account - Inline */}
          {hasConnectedAccount === false && (
            <div className="p-5 border border-forest bg-forest/5 mb-8">
              <p className="text-sm font-medium mb-1">Connect your bank first</p>
              <p className="text-[11px] opacity-50 mb-4">
                Takes 2 minutes via Stripe. Required to stake money.
              </p>
              <button
                onClick={handleConnectStripe}
                disabled={accepting}
                className="text-[10px] font-medium tracking-[0.12em] uppercase text-forest hover:opacity-70 transition-opacity"
              >
                {accepting ? 'Connecting...' : 'Connect with Stripe'}
              </button>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="p-4 border border-red-500/50 bg-red-500/5 text-red-600 text-sm mb-8">
              {error}
            </div>
          )}

          {/* How it works */}
          <div className="p-5 bg-surface/50 border border-border/50">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-3">How it works</p>
            <div className="space-y-2 text-sm opacity-70">
              <p>1. You match their stake of {formatStake(challenge.stake_amount, challenge.currency)}</p>
              <p>2. Both stakes are held securely by Stripe</p>
              <p>3. Winner takes {formatStake(String(winnings.toFixed(2)), challenge.currency)} when resolved</p>
            </div>
          </div>
        </div>
      </main>

      {/* Fixed Bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-t border-border/50 safe-area-bottom">
        <div className="max-w-lg mx-auto px-6 py-4">
          <div className="flex gap-3">
            <Link
              href="/challenge"
              className="flex-1 py-4 text-[11px] font-medium tracking-[0.15em] uppercase text-center border border-border/50 hover:border-forest/50 transition-colors"
            >
              Decline
            </Link>
            <button
              onClick={handleAccept}
              disabled={accepting || hasConnectedAccount === false}
              className={`flex-[2] py-4 text-[11px] font-medium tracking-[0.15em] uppercase transition-all duration-200 ${
                hasConnectedAccount !== false
                  ? 'bg-forest text-background hover:opacity-90'
                  : 'bg-border/50 text-muted cursor-not-allowed'
              }`}
            >
              {accepting ? 'Accepting...' : `Accept and Match ${formatStake(challenge.stake_amount, challenge.currency)}`}
            </button>
          </div>
          <p className="text-[9px] text-center opacity-30 mt-3">
            By accepting, you authorize {formatStake(challenge.stake_amount, challenge.currency)} via Stripe
          </p>
        </div>
      </div>
    </div>
  )
}
