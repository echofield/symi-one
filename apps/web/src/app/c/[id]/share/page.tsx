'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect, useCallback } from 'react'
import {
  getChallenge,
  formatStake,
  type Challenge,
} from '@/lib/api/challenges'

export default function ShareChallenge() {
  const params = useParams()
  const router = useRouter()
  const challengeId = params.id as string

  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [shareError, setShareError] = useState<string | null>(null)

  const fetchChallenge = useCallback(async () => {
    try {
      const data = await getChallenge(challengeId)
      setChallenge(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Challenge not found')
    } finally {
      setLoading(false)
    }
  }, [challengeId])

  useEffect(() => {
    fetchChallenge()
  }, [fetchChallenge])

  const inviteUrl = challenge?.invite_token
    ? `${typeof window !== 'undefined' ? window.location.origin : ''}/challenge/invite/${challenge.invite_token}`
    : ''

  const shareText = challenge
    ? `${challenge.title} - ${formatStake(challenge.stake_amount, challenge.currency)} stake`
    : ''

  async function handleNativeShare() {
    if (!navigator.share) {
      setShareError('Share not supported on this device')
      return
    }

    try {
      await navigator.share({
        title: challenge?.title || 'SYMI Challenge',
        text: shareText,
        url: inviteUrl,
      })
    } catch (err) {
      // User cancelled or share failed
      if ((err as Error).name !== 'AbortError') {
        setShareError('Failed to share')
      }
    }
  }

  async function handleCopyLink() {
    try {
      await navigator.clipboard.writeText(inviteUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setShareError('Failed to copy link')
    }
  }

  function handleWhatsApp() {
    const url = `https://wa.me/?text=${encodeURIComponent(`${shareText}\n\n${inviteUrl}`)}`
    window.open(url, '_blank')
  }

  function handleiMessage() {
    // SMS/iMessage link - works on iOS
    const url = `sms:?body=${encodeURIComponent(`${shareText}\n\n${inviteUrl}`)}`
    window.location.href = url
  }

  function handleTelegram() {
    const url = `https://t.me/share/url?url=${encodeURIComponent(inviteUrl)}&text=${encodeURIComponent(shareText)}`
    window.open(url, '_blank')
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
            <h1 className="text-xl font-medium mb-4">Challenge Not Found</h1>
            <p className="text-sm opacity-50 mb-8">{error || 'This challenge may have been removed.'}</p>
            <Link href="/challenge" className="text-[10px] font-medium tracking-[0.12em] uppercase text-forest">
              Go Back
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
              View Details
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 pt-14 pb-8">
        <div className="max-w-lg mx-auto px-6 py-12">
          {/* Success Message */}
          <div className="text-center mb-12">
            <div className="w-12 h-12 bg-forest flex items-center justify-center mx-auto mb-6">
              <svg className="w-6 h-6 text-background" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-light mb-2">Challenge Created</h1>
            <p className="text-sm opacity-50">Now share it with your opponent</p>
          </div>

          {/* Challenge Summary */}
          <div className="p-6 border border-border/50 mb-8">
            <h2 className="text-lg font-medium mb-4">{challenge.title}</h2>
            <div className="flex items-center justify-between text-sm">
              <div>
                <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-1">Stake</p>
                <p>{formatStake(challenge.stake_amount, challenge.currency)} each</p>
              </div>
              <div className="text-right">
                <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-1">Winner gets</p>
                <p className="text-forest">{formatStake(String(winnings.toFixed(2)), challenge.currency)}</p>
              </div>
            </div>
          </div>

          {/* Native Share Button (Primary) */}
          {'share' in navigator && (
            <button
              onClick={handleNativeShare}
              className="w-full py-4 mb-4 bg-forest text-background text-[11px] font-medium tracking-[0.15em] uppercase hover:opacity-90 transition-opacity"
            >
              Share Challenge
            </button>
          )}

          {/* Share Options */}
          <div className="mb-8">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-4 text-center">
              {'share' in navigator ? 'Or share via' : 'Share via'}
            </p>
            <div className="grid grid-cols-3 gap-3">
              <button
                onClick={handleWhatsApp}
                className="py-4 border border-border/50 hover:border-forest/50 transition-colors"
              >
                <p className="text-sm font-medium">WhatsApp</p>
              </button>
              <button
                onClick={handleiMessage}
                className="py-4 border border-border/50 hover:border-forest/50 transition-colors"
              >
                <p className="text-sm font-medium">iMessage</p>
              </button>
              <button
                onClick={handleTelegram}
                className="py-4 border border-border/50 hover:border-forest/50 transition-colors"
              >
                <p className="text-sm font-medium">Telegram</p>
              </button>
            </div>
          </div>

          {/* Copy Link */}
          <div className="mb-8">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-3">Challenge Link</p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={inviteUrl}
                readOnly
                className="flex-1 px-4 py-3 text-sm bg-surface border border-border/50 outline-none truncate"
              />
              <button
                onClick={handleCopyLink}
                className={`px-4 py-3 border transition-all duration-200 ${
                  copied
                    ? 'border-forest bg-forest/5 text-forest'
                    : 'border-border/50 hover:border-forest/50'
                }`}
              >
                <span className="text-sm">{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          </div>

          {/* Error */}
          {shareError && (
            <div className="p-4 border border-red-500/50 bg-red-500/5 text-red-600 text-sm mb-8">
              {shareError}
            </div>
          )}

          {/* What happens next */}
          <div className="p-5 bg-surface/50 border border-border/50">
            <p className="text-[9px] font-medium tracking-[0.2em] uppercase opacity-40 mb-3">What happens next</p>
            <div className="space-y-3 text-sm">
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 bg-forest/10 text-forest flex items-center justify-center flex-shrink-0 text-[10px] font-medium">1</div>
                <p className="opacity-70">They click the link and accept the challenge</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 bg-forest/10 text-forest flex items-center justify-center flex-shrink-0 text-[10px] font-medium">2</div>
                <p className="opacity-70">Both stakes are held securely by Stripe</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 bg-forest/10 text-forest flex items-center justify-center flex-shrink-0 text-[10px] font-medium">3</div>
                <p className="opacity-70">Winner takes all when the challenge resolves</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Bottom Action */}
      <div className="border-t border-border/50">
        <div className="max-w-lg mx-auto px-6 py-4">
          <button
            onClick={() => router.push(`/challenge/${challenge.public_id}`)}
            className="w-full py-3 text-[10px] font-medium tracking-[0.12em] uppercase opacity-50 hover:opacity-70 transition-opacity"
          >
            View Challenge Details
          </button>
        </div>
      </div>
    </div>
  )
}
