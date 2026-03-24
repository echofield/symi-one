'use client'

import Link from 'next/link'
import { useState, useEffect, useCallback } from 'react'
import {
  getMyChallenges,
  getMyStats,
  formatStake,
  getChallengeStatusLabel,
  type Challenge,
  type ChallengeStats,
  type ChallengeStatus,
} from '@/lib/api/challenges'
import { getAccountByUser, getDashboardLink, type ConnectedAccount } from '@/lib/api/connect'

type Tab = 'active' | 'pending' | 'resolved' | 'disputed'

export default function MyChallengeDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('active')
  const [challenges, setChallenges] = useState<Challenge[]>([])
  const [stats, setStats] = useState<ChallengeStats | null>(null)
  const [account, setAccount] = useState<ConnectedAccount | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Mock user (replace with real auth)
  const [userId] = useState('user_demo')

  const statusFilters: Record<Tab, ChallengeStatus[]> = {
    active: ['active', 'awaiting_proof'],
    pending: ['pending_acceptance'],
    resolved: ['resolved', 'expired', 'cancelled'],
    disputed: ['disputed'],
  }

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [challengeData, statsData] = await Promise.all([
        getMyChallenges(userId, { status: statusFilters[activeTab].join(',') }),
        getMyStats(userId),
      ])
      setChallenges(challengeData.challenges)
      setStats(statsData)

      // Try to get connected account
      try {
        const accountData = await getAccountByUser(userId)
        setAccount(accountData)
      } catch {
        // No account yet
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [activeTab, userId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  async function openStripeDashboard() {
    if (!account) return
    try {
      const { url } = await getDashboardLink(account.id)
      window.open(url, '_blank')
    } catch (err) {
      console.error('Failed to get dashboard link:', err)
    }
  }

  const tabLabels: Record<Tab, string> = {
    active: 'Active',
    pending: 'Pending',
    resolved: 'History',
    disputed: 'Disputed',
  }

  const tabCounts: Record<Tab, number> = {
    active: stats?.active || 0,
    pending: stats?.pending || 0,
    resolved: stats?.resolved || 0,
    disputed: stats?.disputed || 0,
  }

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
              href="/challenge/new"
              className="text-[10px] font-medium tracking-[0.12em] uppercase text-forest hover:opacity-70 transition-opacity"
            >
              New Challenge
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 pt-14">
        <div className="max-w-lg mx-auto px-6 py-8">
          {/* Stats Summary */}
          {stats && (
            <div className="grid grid-cols-4 gap-px bg-border/30 mb-8">
              <div className="bg-background p-4 text-center">
                <p className="text-xl font-light text-forest">{stats.wins}</p>
                <p className="text-[9px] font-medium tracking-[0.15em] uppercase opacity-40 mt-1">Wins</p>
              </div>
              <div className="bg-background p-4 text-center">
                <p className="text-xl font-light">{stats.losses}</p>
                <p className="text-[9px] font-medium tracking-[0.15em] uppercase opacity-40 mt-1">Losses</p>
              </div>
              <div className="bg-background p-4 text-center">
                <p className="text-xl font-light text-forest">{stats.win_rate}%</p>
                <p className="text-[9px] font-medium tracking-[0.15em] uppercase opacity-40 mt-1">Rate</p>
              </div>
              <div className="bg-background p-4 text-center">
                <p className="text-xl font-light text-forest">{stats.total_won}</p>
                <p className="text-[9px] font-medium tracking-[0.15em] uppercase opacity-40 mt-1">Won</p>
              </div>
            </div>
          )}

          {/* Account Warning */}
          {!account && (
            <div className="p-5 border border-forest bg-forest/5 mb-8">
              <p className="text-sm font-medium mb-1">Connect your bank</p>
              <p className="text-[11px] opacity-50 mb-4">
                Required to create or accept challenges.
              </p>
              <Link
                href="/connect/onboarding"
                className="text-[10px] font-medium tracking-[0.12em] uppercase text-forest hover:opacity-70 transition-opacity"
              >
                Connect with Stripe
              </Link>
            </div>
          )}

          {/* Stripe Dashboard Link */}
          {account && account.can_transact && (
            <button
              onClick={openStripeDashboard}
              className="w-full text-left p-4 border border-border/50 hover:border-forest/50 transition-colors mb-8"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Stripe Dashboard</p>
                  <p className="text-[11px] opacity-50">View payouts and account settings</p>
                </div>
                <svg className="w-4 h-4 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>
          )}

          {/* Tabs */}
          <div className="flex border-b border-border/50 mb-6">
            {(Object.keys(tabLabels) as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-3 text-[10px] font-medium tracking-[0.12em] uppercase transition-colors border-b-2 -mb-px ${
                  activeTab === tab
                    ? 'border-forest text-forest'
                    : 'border-transparent opacity-40 hover:opacity-70'
                }`}
              >
                {tabLabels[tab]}
                {tabCounts[tab] > 0 && (
                  <span className="ml-1.5 text-[9px] opacity-60">
                    {tabCounts[tab]}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Loading */}
          {loading && (
            <div className="py-12 flex justify-center">
              <div className="w-6 h-6 border-2 border-forest border-t-transparent animate-spin" />
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="p-4 border border-red-500/50 bg-red-500/5 text-red-600 text-sm mb-6">
              {error}
            </div>
          )}

          {/* Empty State */}
          {!loading && challenges.length === 0 && (
            <div className="py-16 text-center">
              <p className="text-sm opacity-50 mb-6">No {tabLabels[activeTab].toLowerCase()} challenges</p>
              <Link
                href="/challenge/new"
                className="inline-block px-6 py-3 bg-forest text-background text-[10px] font-medium tracking-[0.15em] uppercase hover:opacity-90 transition-opacity"
              >
                Create Challenge
              </Link>
            </div>
          )}

          {/* Challenge List */}
          {!loading && challenges.length > 0 && (
            <div className="space-y-3">
              {challenges.map((challenge) => (
                <Link
                  key={challenge.id}
                  href={`/challenge/${challenge.public_id}`}
                  className="block p-5 border border-border/50 hover:border-forest/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium truncate">{challenge.title}</h3>
                      <p className="text-[11px] opacity-50 mt-1">
                        vs {challenge.party_b_email || 'Waiting...'}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-sm font-light text-forest">
                        {formatStake(challenge.stake_amount, challenge.currency)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className={`text-[9px] font-medium tracking-[0.12em] uppercase ${
                      challenge.status === 'resolved' ? 'text-forest' :
                      challenge.status === 'disputed' ? 'text-red-500' :
                      'opacity-50'
                    }`}>
                      {getChallengeStatusLabel(challenge.status)}
                    </span>
                    <span className="text-[10px] opacity-40">
                      {challenge.resolved_at
                        ? new Date(challenge.resolved_at).toLocaleDateString()
                        : challenge.proof_deadline
                          ? `Due ${new Date(challenge.proof_deadline).toLocaleDateString()}`
                          : new Date(challenge.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  {/* Win/Loss indicator */}
                  {challenge.status === 'resolved' && challenge.winner_id && (
                    <div className={`mt-3 pt-3 border-t border-border/30 text-[10px] font-medium ${
                      challenge.winner_id === userId ? 'text-forest' : 'text-red-500'
                    }`}>
                      {challenge.winner_id === userId ? 'You won' : 'You lost'}
                    </div>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
