'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import {
  getRecentChallenges,
  getTemplates,
  formatStake,
  getChallengeTypeLabel,
  type RecentChallenge,
  type ChallengeTemplate,
} from '@/lib/api/challenges'

export default function ChallengeLanding() {
  const [recentChallenges, setRecentChallenges] = useState<RecentChallenge[]>([])
  const [templates, setTemplates] = useState<ChallengeTemplate[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [recent, templateData] = await Promise.all([
          getRecentChallenges(5),
          getTemplates(),
        ])
        setRecentChallenges(recent)
        setTemplates(templateData.templates)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b-2 border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-3 h-3 bg-forest" />
              <span className="text-sm font-medium tracking-wider uppercase">SYMIONE</span>
            </Link>
            <nav className="flex items-center gap-6">
              <Link href="/challenge/me" className="btn-ghost text-sm">
                My Challenges
              </Link>
              <Link href="/templates" className="btn-ghost text-sm">
                Build
              </Link>
              <Link href="/challenge/new" className="btn-secondary text-sm py-2 px-4">
                Create Challenge
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 pt-16">
        <section className="min-h-[80vh] flex items-center">
          <div className="max-w-7xl mx-auto px-6 lg:px-12 py-20">
            <div className="grid lg:grid-cols-12 gap-12 lg:gap-20 items-center">
              {/* Left Column */}
              <div className="lg:col-span-7 space-y-10">
                <div className="space-y-6 opacity-0 animate-fade-up">
                  <p className="text-micro uppercase tracking-[0.3em] text-muted">
                    Stake-Based Commitment
                  </p>
                  <h1 className="text-display text-foreground">
                    Put your money<br />
                    <span className="text-forest">where your mouth is.</span>
                  </h1>
                </div>

                <p className="text-xl font-light text-muted leading-relaxed max-w-xl opacity-0 animate-fade-up stagger-2">
                  Challenge anyone. Both stake real money.
                  Winner takes all. No arguments. Just proof.
                </p>

                <div className="flex items-center gap-4 opacity-0 animate-fade-up stagger-3">
                  <Link href="/challenge/new" className="btn-primary">
                    Create a Challenge
                  </Link>
                  <Link href="#how-it-works" className="btn-ghost">
                    How it works
                  </Link>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-12 pt-8 opacity-0 animate-fade-up stagger-4">
                  <div>
                    <p className="text-3xl font-light text-forest">10%</p>
                    <p className="text-micro uppercase tracking-widest text-muted mt-1">Platform Fee</p>
                  </div>
                  <div className="w-px h-12 bg-border" />
                  <div>
                    <p className="text-3xl font-light text-forest">Instant</p>
                    <p className="text-micro uppercase tracking-widest text-muted mt-1">Settlement</p>
                  </div>
                  <div className="w-px h-12 bg-border" />
                  <div>
                    <p className="text-3xl font-light text-forest">Stripe</p>
                    <p className="text-micro uppercase tracking-widest text-muted mt-1">Powered</p>
                  </div>
                </div>
              </div>

              {/* Right Column - Recent Feed */}
              <div className="lg:col-span-5 opacity-0 animate-fade-up stagger-5">
                <div className="relative">
                  <div className="absolute -top-4 -right-4 w-full h-full border-2 border-forest" />

                  <div className="relative bg-surface border-2 border-foreground p-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-micro uppercase tracking-widest text-muted">Live Feed</span>
                      <span className="badge-success">Recently Settled</span>
                    </div>

                    {loading ? (
                      <div className="py-8 text-center text-muted">Loading...</div>
                    ) : recentChallenges.length > 0 ? (
                      <div className="space-y-3">
                        {recentChallenges.map((challenge) => (
                          <div
                            key={challenge.id}
                            className="flex items-center justify-between py-3 border-b border-border last:border-0"
                          >
                            <div>
                              <p className="text-sm font-medium">
                                {getChallengeTypeLabel(challenge.challenge_type)}
                              </p>
                              <p className="text-micro text-muted">
                                {challenge.resolution_type === 'draw' ? 'Draw' : 'Winner declared'}
                                {challenge.duration_hours && ` in ${challenge.duration_hours}h`}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-light text-forest">
                                {formatStake(challenge.stake_amount, challenge.currency)}
                              </p>
                              <p className="text-micro text-muted">each</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="py-8 text-center text-muted">
                        <p>No settled challenges yet.</p>
                        <p className="text-sm mt-1">Be the first!</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How it Works */}
        <section id="how-it-works" className="py-30 bg-surface border-y-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="max-w-2xl mb-20">
              <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Process</p>
              <h2 className="text-headline text-foreground">
                Three steps. No arguments.
              </h2>
            </div>

            <div className="grid md:grid-cols-3 gap-px bg-border">
              {[
                {
                  step: '01',
                  title: 'Define',
                  description: 'Create a challenge. Set the stake. Describe what needs to happen. Share the link with your opponent.',
                },
                {
                  step: '02',
                  title: 'Both Stake',
                  description: 'Both parties put their money where their mouth is. Funds are held securely by Stripe until resolution.',
                },
                {
                  step: '03',
                  title: 'Prove & Settle',
                  description: 'Submit proof. If both agree on the outcome, winner gets paid instantly. If not, dispute resolution kicks in.',
                },
              ].map((item) => (
                <div key={item.step} className="bg-background p-10">
                  <p className="text-4xl font-light text-forest mb-6">{item.step}</p>
                  <h3 className="text-xl font-medium text-foreground mb-4">{item.title}</h3>
                  <p className="text-muted">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Challenge Types */}
        <section className="py-30">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="max-w-2xl mb-20">
              <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Challenge Types</p>
              <h2 className="text-headline text-foreground">
                Pick your battle.
              </h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.map((template) => (
                <Link
                  key={template.type}
                  href={`/challenge/new?type=${template.type}`}
                  className="group bg-surface border-2 border-border hover:border-forest transition-colors p-8"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-micro uppercase tracking-widest text-muted">
                      {template.resolution_method.replace('_', ' ')}
                    </span>
                    <span className="text-micro text-forest opacity-0 group-hover:opacity-100 transition-opacity">
                      Select
                    </span>
                  </div>
                  <h3 className="text-xl font-medium text-foreground mb-3">{template.name}</h3>
                  <p className="text-muted text-sm">{template.description}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-30 bg-forest text-background">
          <div className="max-w-7xl mx-auto px-6 lg:px-12 text-center">
            <h2 className="text-headline mb-6">Ready to challenge someone?</h2>
            <p className="text-xl font-light mb-10 opacity-80 max-w-xl mx-auto">
              No more empty promises. No more &quot;I told you so.&quot; Just proof and payment.
            </p>
            <Link
              href="/challenge/new"
              className="inline-flex items-center justify-center px-8 py-4 bg-background text-forest font-medium hover:bg-surface transition-colors"
            >
              Create Your First Challenge
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t-2 border-border py-10">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-forest" />
              <span className="text-sm font-medium tracking-wider uppercase">SYMIONE</span>
            </div>
            <div className="flex items-center gap-6">
              <Link href="/templates" className="text-micro text-muted hover:text-forest transition-colors">
                Developers: Build your own →
              </Link>
              <p className="text-micro text-muted">
                Powered by Stripe Connect
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
