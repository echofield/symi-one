'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect, useCallback } from 'react'
import {
  getChallenge,
  submitProof,
  formatStake,
  type Challenge,
} from '@/lib/api/challenges'

type Outcome = 'party_a' | 'party_b' | 'draw'

export default function SubmitProof() {
  const params = useParams()
  const router = useRouter()
  const challengeId = params.id as string

  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Simple form state
  const [selectedOutcome, setSelectedOutcome] = useState<Outcome | null>(null)
  const [comment, setComment] = useState('')

  // Mock user (replace with real auth)
  const [userId] = useState('user_demo')

  const fetchChallenge = useCallback(async () => {
    try {
      const data = await getChallenge(challengeId)
      setChallenge(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load challenge')
    } finally {
      setLoading(false)
    }
  }, [challengeId])

  useEffect(() => {
    fetchChallenge()
  }, [fetchChallenge])

  const isParty = challenge?.party_a_id === userId || challenge?.party_b_id === userId
  const isPartyA = challenge?.party_a_id === userId
  const hasSubmitted = challenge?.proofs.some((p) => p.submitted_by === userId)
  const opponentName = isPartyA ? (challenge?.party_b_email || 'Opponent') : (challenge?.party_a_email || 'Challenger')

  async function handleSubmit() {
    if (!challenge || !selectedOutcome) return

    setSubmitting(true)
    setError(null)

    try {
      await submitProof(challenge.public_id, userId, {
        proof_type: 'attestation',
        proof_data: {
          outcome: selectedOutcome,
          comment: comment || undefined,
        },
        attested_outcome: selectedOutcome,
      })

      router.push(`/challenge/${challenge.public_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-forest border-t-transparent animate-spin" />
      </div>
    )
  }

  if (!challenge || !isParty) {
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
            <h1 className="text-xl font-medium mb-4">Access Denied</h1>
            <p className="text-sm opacity-50 mb-8">You are not part of this challenge.</p>
            <Link href="/challenge" className="text-[10px] font-medium tracking-[0.12em] uppercase text-forest">
              Go Back
            </Link>
          </div>
        </main>
      </div>
    )
  }

  if (hasSubmitted) {
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
            <h1 className="text-xl font-medium mb-4">Already Submitted</h1>
            <p className="text-sm opacity-50 mb-8">Waiting for your opponent to confirm the result.</p>
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
            <Link
              href={`/challenge/${challenge.public_id}`}
              className="text-[10px] tracking-[0.12em] uppercase opacity-40 hover:opacity-70 transition-opacity"
            >
              Cancel
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 pt-14 pb-32">
        <div className="max-w-lg mx-auto px-6 py-8">
          {/* Challenge Summary */}
          <div className="p-5 border border-border/50 mb-10">
            <h2 className="text-lg font-medium mb-3">{challenge.title}</h2>
            <div className="flex items-center justify-between text-sm">
              <span className="opacity-50">vs {opponentName}</span>
              <span className="text-forest">{formatStake(String(winnings.toFixed(2)), challenge.currency)} at stake</span>
            </div>
          </div>

          {/* Main Question */}
          <div className="text-center mb-10">
            <h1 className="text-2xl font-light mb-2">Who won?</h1>
            <p className="text-sm opacity-50">Both parties must agree on the outcome</p>
          </div>

          {/* Outcome Selection */}
          <div className="space-y-3 mb-10">
            <button
              onClick={() => setSelectedOutcome('party_a')}
              className={`w-full p-5 border text-left transition-all duration-200 ${
                selectedOutcome === 'party_a'
                  ? 'border-forest bg-forest/5'
                  : 'border-border/50 hover:border-forest/50'
              }`}
            >
              <p className={`text-lg font-medium ${selectedOutcome === 'party_a' ? 'text-forest' : ''}`}>
                I won
              </p>
              <p className="text-sm opacity-50 mt-1">
                I claim victory and the {formatStake(String(winnings.toFixed(2)), challenge.currency)} prize
              </p>
            </button>

            <button
              onClick={() => setSelectedOutcome('party_b')}
              className={`w-full p-5 border text-left transition-all duration-200 ${
                selectedOutcome === 'party_b'
                  ? 'border-forest bg-forest/5'
                  : 'border-border/50 hover:border-forest/50'
              }`}
            >
              <p className={`text-lg font-medium ${selectedOutcome === 'party_b' ? 'text-forest' : ''}`}>
                They won
              </p>
              <p className="text-sm opacity-50 mt-1">
                {opponentName} won this challenge
              </p>
            </button>

            <button
              onClick={() => setSelectedOutcome('draw')}
              className={`w-full p-5 border text-left transition-all duration-200 ${
                selectedOutcome === 'draw'
                  ? 'border-forest bg-forest/5'
                  : 'border-border/50 hover:border-forest/50'
              }`}
            >
              <p className={`text-lg font-medium ${selectedOutcome === 'draw' ? 'text-forest' : ''}`}>
                Draw
              </p>
              <p className="text-sm opacity-50 mt-1">
                No clear winner - refund stakes to both parties
              </p>
            </button>
          </div>

          {/* Optional Comment */}
          <div className="mb-8">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-3">
              Comment (optional)
            </p>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Add any notes about the result..."
              rows={3}
              className="w-full px-4 py-3 text-sm bg-surface border border-border/50 focus:border-forest outline-none transition-colors resize-none"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 border border-red-500/50 bg-red-500/5 text-red-600 text-sm mb-8">
              {error}
            </div>
          )}
        </div>
      </main>

      {/* Fixed Bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-t border-border/50 safe-area-bottom">
        <div className="max-w-lg mx-auto px-6 py-4">
          <button
            onClick={handleSubmit}
            disabled={submitting || !selectedOutcome}
            className={`w-full py-4 text-[11px] font-medium tracking-[0.15em] uppercase transition-all duration-200 ${
              selectedOutcome
                ? 'bg-forest text-background hover:opacity-90'
                : 'bg-border/50 text-muted cursor-not-allowed'
            }`}
          >
            {submitting ? 'Submitting...' : 'Confirm Result'}
          </button>
          <p className="text-[9px] text-center opacity-30 mt-3">
            This cannot be changed once submitted
          </p>
        </div>
      </div>
    </div>
  )
}
