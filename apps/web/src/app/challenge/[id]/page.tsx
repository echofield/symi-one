'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect, useCallback } from 'react'
import {
  getChallenge,
  acceptChallenge,
  cancelChallenge,
  evaluateSimpleBet,
  formatStake,
  getChallengeStatusLabel,
  getChallengeTypeLabel,
  type Challenge,
} from '@/lib/api/challenges'

export default function ChallengeDetail() {
  const params = useParams()
  const router = useRouter()
  const challengeId = params.id as string

  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  // Mock user (replace with real auth)
  const [userId] = useState('user_demo')
  const [userEmail] = useState('demo@symione.com')

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

  const isPartyA = challenge?.party_a_id === userId
  const isPartyB = challenge?.party_b_id === userId
  const isParty = isPartyA || isPartyB

  const canAccept = challenge?.status === 'pending_acceptance' && !isPartyA
  const canSubmitProof = isParty && ['active', 'awaiting_proof'].includes(challenge?.status || '')
  const canCancel = isPartyA && challenge?.status === 'pending_acceptance'

  const myProof = challenge?.proofs.find((p) => p.submitted_by === userId)
  const opponentProof = challenge?.proofs.find((p) => p.submitted_by !== userId)

  async function handleAccept() {
    if (!challenge) return
    setActionLoading(true)
    try {
      await acceptChallenge(challenge.public_id, userId, userEmail)
      await fetchChallenge()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to accept challenge')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleCancel() {
    if (!challenge) return
    if (!confirm('Are you sure you want to cancel this challenge?')) return
    setActionLoading(true)
    try {
      await cancelChallenge(challenge.public_id, userId)
      router.push('/challenge/me')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel challenge')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleEvaluate() {
    if (!challenge) return
    setActionLoading(true)
    try {
      await evaluateSimpleBet(challenge.public_id)
      await fetchChallenge()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to evaluate challenge')
    } finally {
      setActionLoading(false)
    }
  }

  function copyInviteLink() {
    if (!challenge?.invite_url) return
    navigator.clipboard.writeText(challenge.invite_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted">Loading challenge...</div>
      </div>
    )
  }

  if (error || !challenge) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-xl font-medium mb-4">Challenge not found</h1>
          <p className="text-muted mb-6">{error || 'This challenge may have been cancelled or expired.'}</p>
          <Link href="/challenge" className="btn-primary">
            Back to Challenges
          </Link>
        </div>
      </div>
    )
  }

  const statusColors: Record<string, string> = {
    pending_acceptance: 'badge-warning',
    active: 'badge-success',
    awaiting_proof: 'badge-warning',
    resolving: 'badge-warning',
    resolved: 'badge-success',
    disputed: 'badge-error',
    cancelled: 'badge-muted',
    expired: 'badge-muted',
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b-2 border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-16">
            <Link href="/challenge" className="flex items-center gap-3">
              <div className="w-3 h-3 bg-forest" />
              <span className="text-sm font-medium tracking-wider uppercase">SYMIONE</span>
            </Link>
            <Link href="/challenge/me" className="btn-ghost text-sm">
              My Challenges
            </Link>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 pt-16">
        <div className="max-w-4xl mx-auto px-6 py-16">
          {/* Status Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <span className={`badge ${statusColors[challenge.status] || 'badge-muted'}`}>
                {getChallengeStatusLabel(challenge.status)}
              </span>
              <span className="text-micro uppercase tracking-widest text-muted">
                {getChallengeTypeLabel(challenge.challenge_type)}
              </span>
            </div>
            <div className="text-micro text-muted">
              Created {new Date(challenge.created_at).toLocaleDateString()}
            </div>
          </div>

          {/* Challenge Card */}
          <div className="bg-surface border-2 border-foreground p-8 mb-8">
            <h1 className="text-2xl font-medium mb-4">{challenge.title}</h1>
            <p className="text-muted mb-8">{challenge.description}</p>

            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <p className="text-micro uppercase tracking-widest text-muted mb-1">Stake</p>
                <p className="text-2xl font-light">
                  {formatStake(challenge.stake_amount, challenge.currency)}
                </p>
                <p className="text-sm text-muted">each</p>
              </div>
              <div>
                <p className="text-micro uppercase tracking-widest text-muted mb-1">Winner gets</p>
                <p className="text-2xl font-light text-forest">
                  {formatStake(
                    String(parseFloat(challenge.stake_amount) * 2 * (1 - parseFloat(challenge.platform_fee_percent) / 100)),
                    challenge.currency
                  )}
                </p>
                <p className="text-sm text-muted">after {challenge.platform_fee_percent}% fee</p>
              </div>
              {challenge.proof_deadline && (
                <div>
                  <p className="text-micro uppercase tracking-widest text-muted mb-1">Deadline</p>
                  <p className="text-lg">
                    {new Date(challenge.proof_deadline).toLocaleDateString()}
                  </p>
                  <p className="text-sm text-muted">
                    {new Date(challenge.proof_deadline).toLocaleTimeString()}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Parties */}
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            {/* Party A */}
            <div className="bg-surface border-2 border-border p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-micro uppercase tracking-widest text-muted">Challenger</span>
                {isPartyA && <span className="text-micro text-forest">You</span>}
              </div>
              <p className="font-medium mb-2">{challenge.party_a_email}</p>
              <div className="flex items-center gap-4 text-sm">
                <span className={challenge.party_a_funded ? 'text-forest' : 'text-muted'}>
                  {challenge.party_a_funded ? 'Funded' : 'Not funded'}
                </span>
                {challenge.proofs.find((p) => p.submitted_by === challenge.party_a_id) && (
                  <span className="text-forest">Proof submitted</span>
                )}
              </div>
            </div>

            {/* Party B */}
            <div className="bg-surface border-2 border-border p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-micro uppercase tracking-widest text-muted">Opponent</span>
                {isPartyB && <span className="text-micro text-forest">You</span>}
              </div>
              {challenge.party_b_id ? (
                <>
                  <p className="font-medium mb-2">{challenge.party_b_email}</p>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={challenge.party_b_funded ? 'text-forest' : 'text-muted'}>
                      {challenge.party_b_funded ? 'Funded' : 'Not funded'}
                    </span>
                    {challenge.proofs.find((p) => p.submitted_by === challenge.party_b_id) && (
                      <span className="text-forest">Proof submitted</span>
                    )}
                  </div>
                </>
              ) : (
                <p className="text-muted">Waiting for opponent...</p>
              )}
            </div>
          </div>

          {/* Resolution */}
          {challenge.status === 'resolved' && (
            <div className="bg-forest text-background p-8 mb-8">
              <h2 className="text-xl font-medium mb-4">Challenge Resolved</h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm opacity-80 mb-1">Winner</p>
                  <p className="text-lg">
                    {challenge.winner_id === challenge.party_a_id
                      ? challenge.party_a_email
                      : challenge.winner_id === challenge.party_b_id
                        ? challenge.party_b_email
                        : 'Draw'}
                  </p>
                </div>
                <div>
                  <p className="text-sm opacity-80 mb-1">Resolution</p>
                  <p className="text-lg">{challenge.resolution_type?.replace('_', ' ')}</p>
                </div>
              </div>
              {challenge.resolution_reason && (
                <p className="mt-4 opacity-80">{challenge.resolution_reason}</p>
              )}
            </div>
          )}

          {/* Proofs */}
          {challenge.proofs.length > 0 && (
            <div className="mb-8">
              <h2 className="text-lg font-medium mb-4">Submitted Proofs</h2>
              <div className="space-y-4">
                {challenge.proofs.map((proof) => (
                  <div key={proof.id} className="bg-surface border-2 border-border p-6">
                    <div className="flex items-center justify-between mb-4">
                      <span className="font-medium">
                        {proof.submitted_by === challenge.party_a_id
                          ? challenge.party_a_email
                          : challenge.party_b_email}
                      </span>
                      <span className="text-micro text-muted">
                        {new Date(proof.submitted_at).toLocaleString()}
                      </span>
                    </div>
                    {proof.attested_outcome && (
                      <p className="text-lg">
                        Outcome: <span className="text-forest">{proof.attested_outcome}</span>
                      </p>
                    )}
                    {proof.url && (
                      <a href={proof.url} target="_blank" rel="noopener noreferrer" className="text-forest hover:underline">
                        {proof.url}
                      </a>
                    )}
                    <p className="text-micro text-muted mt-2">Hash: {proof.proof_hash.substring(0, 16)}...</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timeline */}
          {challenge.events.length > 0 && (
            <div className="mb-8">
              <h2 className="text-lg font-medium mb-4">Timeline</h2>
              <div className="space-y-2">
                {challenge.events.map((event) => (
                  <div key={event.id} className="flex items-center gap-4 py-2 border-b border-border last:border-0">
                    <div className="w-2 h-2 bg-forest" />
                    <div className="flex-1">
                      <span className="font-medium">{event.event_type.replace('_', ' ')}</span>
                      {event.actor_id && (
                        <span className="text-muted text-sm ml-2">by {event.actor_id}</span>
                      )}
                    </div>
                    <span className="text-micro text-muted">
                      {new Date(event.created_at).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-4">
            {/* Share Link */}
            {challenge.status === 'pending_acceptance' && (
              <div className="bg-surface border-2 border-border p-6">
                <h3 className="font-medium mb-2">Share this challenge</h3>
                <div className="flex items-center gap-4">
                  <input
                    type="text"
                    value={challenge.invite_url || ''}
                    readOnly
                    className="flex-1 px-4 py-2 bg-background border-2 border-border text-sm"
                  />
                  <button onClick={copyInviteLink} className="btn-secondary text-sm">
                    {copied ? 'Copied!' : 'Copy Link'}
                  </button>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-4">
              {canAccept && (
                <button
                  onClick={handleAccept}
                  disabled={actionLoading}
                  className="btn-primary"
                >
                  {actionLoading ? 'Accepting...' : `Accept & Stake ${formatStake(challenge.stake_amount, challenge.currency)}`}
                </button>
              )}

              {canSubmitProof && !myProof && (
                <Link href={`/challenge/${challenge.public_id}/proof`} className="btn-primary">
                  Submit Proof
                </Link>
              )}

              {/* Auto-evaluate if both proofs submitted for simple_bet */}
              {challenge.challenge_type === 'simple_bet' &&
                challenge.proofs.length === 2 &&
                challenge.status !== 'resolved' && (
                  <button
                    onClick={handleEvaluate}
                    disabled={actionLoading}
                    className="btn-secondary"
                  >
                    {actionLoading ? 'Evaluating...' : 'Check Results'}
                  </button>
                )}

              {canCancel && (
                <button
                  onClick={handleCancel}
                  disabled={actionLoading}
                  className="btn-ghost text-red-500"
                >
                  Cancel Challenge
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="mt-4 bg-red-500/10 border-2 border-red-500 p-4 text-red-500">
              {error}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
