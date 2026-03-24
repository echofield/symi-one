'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import {
  createChallenge,
  type ChallengeType,
} from '@/lib/api/challenges'
import { getAccountByUser, createAccount, createOnboardingLink } from '@/lib/api/connect'

type ChallengeMode = 'solo' | 'duel' | 'cell'

const DEADLINE_OPTIONS = [
  { label: '24h', value: 1 },
  { label: '1 week', value: 7 },
  { label: '1 month', value: 30 },
  { label: 'Custom', value: 0 },
]

const STAKE_OPTIONS = [5, 10, 20, 50]

export default function CreateChallenge() {
  const router = useRouter()

  // Form state
  const [mode, setMode] = useState<ChallengeMode>('duel')
  const [title, setTitle] = useState('')
  const [deadlineDays, setDeadlineDays] = useState<number>(7)
  const [customDeadline, setCustomDeadline] = useState('')
  const [stakeAmount, setStakeAmount] = useState(20)
  const [customStake, setCustomStake] = useState('')

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCustomDeadline, setShowCustomDeadline] = useState(false)
  const [showCustomStake, setShowCustomStake] = useState(false)

  // User state (mock for now - replace with real auth)
  const [userId] = useState('user_' + Math.random().toString(36).substring(7))
  const [userEmail] = useState('demo@symione.com')
  const [hasConnectedAccount, setHasConnectedAccount] = useState<boolean | null>(null)

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

  function getDeadlineDate(): string | undefined {
    if (deadlineDays === 0 && customDeadline) {
      return new Date(customDeadline).toISOString()
    }
    if (deadlineDays > 0) {
      const date = new Date()
      date.setDate(date.getDate() + deadlineDays)
      return date.toISOString()
    }
    return undefined
  }

  function getChallengeType(): ChallengeType {
    // Map mode to challenge type
    if (mode === 'solo') return 'accountability'
    if (mode === 'cell') return 'custom' // Group challenges
    return 'simple_bet' // Duel mode
  }

  async function handleConnectStripe() {
    setLoading(true)
    try {
      await createAccount({ user_id: userId, email: userEmail })
      const { url } = await createOnboardingLink(
        userId,
        `${window.location.origin}/challenge/new?return=true`,
        `${window.location.origin}/connect/onboarding`
      )
      window.location.href = url
    } catch (err) {
      setError('Failed to start Stripe onboarding')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate() {
    if (!title.trim()) {
      setError('Give your challenge a name')
      return
    }

    const finalStake = showCustomStake && customStake ? parseInt(customStake) : stakeAmount
    if (finalStake < 5) {
      setError('Minimum stake is 5 EUR')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const challenge = await createChallenge(
        {
          challenge_type: getChallengeType(),
          title: title.trim(),
          description: title.trim(), // Use title as description for fast path
          stake_amount: finalStake,
          currency: 'eur',
          proof_deadline: getDeadlineDate(),
        },
        userId,
        userEmail
      )

      // Redirect to share page instead of detail page
      router.push(`/c/${challenge.public_id}/share`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create challenge')
    } finally {
      setLoading(false)
    }
  }

  const finalStake = showCustomStake && customStake ? parseInt(customStake) || 0 : stakeAmount
  const winnings = finalStake * 2 * 0.90 // Both stakes minus 10% fee

  const isValid = title.trim().length > 0 && finalStake >= 5

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
            <Link href="/challenge" className="text-[10px] tracking-[0.12em] uppercase opacity-40 hover:opacity-70 transition-opacity">
              Cancel
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 pt-14 pb-32">
        <div className="max-w-lg mx-auto px-6 py-8">
          {/* Mode Selector */}
          <div className="mb-10">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-4">Mode</p>
            <div className="flex gap-2">
              {[
                { id: 'solo', label: 'Solo', desc: 'Challenge yourself' },
                { id: 'duel', label: 'Duel', desc: '1v1 with a friend' },
                { id: 'cell', label: 'Cell', desc: 'Group challenge' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setMode(opt.id as ChallengeMode)}
                  className={`flex-1 py-4 px-3 border transition-all duration-200 ${
                    mode === opt.id
                      ? 'border-forest bg-forest/5'
                      : 'border-border/50 hover:border-forest/50'
                  }`}
                >
                  <p className={`text-sm font-medium mb-0.5 ${mode === opt.id ? 'text-forest' : ''}`}>
                    {opt.label}
                  </p>
                  <p className="text-[10px] opacity-40">{opt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Title Input */}
          <div className="mb-10">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-4">
              {mode === 'solo' ? 'What will you accomplish?' : 'What are you betting on?'}
            </p>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={
                mode === 'solo'
                  ? 'Run 5k every day this week'
                  : mode === 'cell'
                    ? 'First to close 10 deals'
                    : 'PSG beats Marseille tonight'
              }
              className="w-full px-0 py-4 text-xl font-light bg-transparent border-0 border-b border-border/50 focus:border-forest outline-none transition-colors placeholder:opacity-30"
              autoFocus
            />
          </div>

          {/* Deadline Pills */}
          <div className="mb-10">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-4">Deadline</p>
            <div className="flex flex-wrap gap-2">
              {DEADLINE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    setDeadlineDays(opt.value)
                    setShowCustomDeadline(opt.value === 0)
                  }}
                  className={`px-4 py-2.5 text-sm border transition-all duration-200 ${
                    deadlineDays === opt.value
                      ? 'border-forest bg-forest/5 text-forest'
                      : 'border-border/50 hover:border-forest/50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {showCustomDeadline && (
              <input
                type="datetime-local"
                value={customDeadline}
                onChange={(e) => setCustomDeadline(e.target.value)}
                className="mt-3 w-full px-4 py-3 text-sm bg-surface border border-border/50 focus:border-forest outline-none transition-colors"
              />
            )}
          </div>

          {/* Stake Amount */}
          <div className="mb-10">
            <div className="flex items-center justify-between mb-4">
              <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40">
                {mode === 'solo' ? 'Commitment' : 'Stake'}
              </p>
              <p className="text-[10px] opacity-40">EUR</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {STAKE_OPTIONS.map((amount) => (
                <button
                  key={amount}
                  onClick={() => {
                    setStakeAmount(amount)
                    setShowCustomStake(false)
                  }}
                  className={`px-5 py-3 text-lg font-light border transition-all duration-200 ${
                    stakeAmount === amount && !showCustomStake
                      ? 'border-forest bg-forest/5 text-forest'
                      : 'border-border/50 hover:border-forest/50'
                  }`}
                >
                  {amount}
                </button>
              ))}
              <button
                onClick={() => setShowCustomStake(true)}
                className={`px-5 py-3 text-lg font-light border transition-all duration-200 ${
                  showCustomStake
                    ? 'border-forest bg-forest/5 text-forest'
                    : 'border-border/50 hover:border-forest/50'
                }`}
              >
                Other
              </button>
            </div>
            {showCustomStake && (
              <input
                type="number"
                value={customStake}
                onChange={(e) => setCustomStake(e.target.value)}
                placeholder="Enter amount"
                min={5}
                className="mt-3 w-full px-4 py-3 text-lg font-light bg-surface border border-border/50 focus:border-forest outline-none transition-colors"
                autoFocus
              />
            )}
          </div>

          {/* Summary */}
          {mode !== 'solo' && isValid && (
            <div className="p-5 border border-border/50 bg-surface/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-1">Winner takes</p>
                  <p className="text-2xl font-light text-forest">{winnings.toFixed(0)} EUR</p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] opacity-40">{finalStake} each</p>
                  <p className="text-[10px] opacity-40">10% platform fee</p>
                </div>
              </div>
            </div>
          )}

          {/* Connect Account Warning */}
          {hasConnectedAccount === false && (
            <div className="mt-6 p-5 border border-forest bg-forest/5">
              <p className="text-sm font-medium mb-1">Connect your bank first</p>
              <p className="text-[11px] opacity-50 mb-4">
                To stake money, connect your bank via Stripe. Takes 2 minutes.
              </p>
              <button
                onClick={handleConnectStripe}
                disabled={loading}
                className="text-[10px] font-medium tracking-[0.12em] uppercase text-forest hover:opacity-70 transition-opacity"
              >
                {loading ? 'Connecting...' : 'Connect with Stripe'}
              </button>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-6 p-4 border border-red-500/50 bg-red-500/5 text-red-600 text-sm">
              {error}
            </div>
          )}
        </div>
      </main>

      {/* Fixed Bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-t border-border/50 safe-area-bottom">
        <div className="max-w-lg mx-auto px-6 py-4">
          <button
            onClick={handleCreate}
            disabled={loading || !isValid || hasConnectedAccount === false}
            className={`w-full py-4 text-[11px] font-medium tracking-[0.15em] uppercase transition-all duration-200 ${
              isValid && hasConnectedAccount !== false
                ? 'bg-forest text-background hover:opacity-90'
                : 'bg-border/50 text-muted cursor-not-allowed'
            }`}
          >
            {loading ? 'Creating...' : mode === 'solo' ? 'Start Challenge' : 'Create and Share'}
          </button>
          <p className="text-[9px] text-center opacity-30 mt-3">
            By creating, you authorize {finalStake} EUR via Stripe
          </p>
        </div>
      </div>
    </div>
  )
}
