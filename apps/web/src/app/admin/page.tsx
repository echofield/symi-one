'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { listAgreements, listOpenReviews, listDecisions } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'

function getStatusBadge(status: string) {
  const statusMap: Record<string, string> = {
    'passed': 'badge-success',
    'funded': 'badge-success',
    'completed': 'badge-success',
    'validating': 'badge-info',
    'submitted': 'badge-info',
    'pending': 'badge-default',
    'draft': 'badge-default',
    'failed': 'badge-error',
    'rejected': 'badge-error',
    'authorize': 'badge-success',
    'reject': 'badge-error',
  }
  return statusMap[status] || 'badge-default'
}

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalAgreements: 0,
    openReviews: 0,
    recentDecisions: [] as Array<{
      id: string
      decision_type: string
      outcome: string
      reason: string
      created_at: string
    }>,
    recentAgreements: [] as Array<{
      id: string
      public_id: string
      title: string
      amount: string
      currency: string
      status: string
      created_at: string
    }>,
  })

  useEffect(() => {
    async function load() {
      try {
        const [agreements, reviews, decisions] = await Promise.all([
          listAgreements({ limit: 5 }),
          listOpenReviews({ limit: 10 }),
          listDecisions({ limit: 5 }),
        ])

        setStats({
          totalAgreements: agreements.total,
          openReviews: reviews.total,
          recentDecisions: decisions.decisions,
          recentAgreements: agreements.agreements,
        })
      } catch (err) {
        console.error('Failed to load dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
        <div className="flex items-center gap-3 text-muted">
          <span className="spinner" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
      {/* Header */}
      <div className="mb-12 opacity-0 animate-fade-up">
        <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Control Center</p>
        <h1 className="text-headline text-foreground">Admin Dashboard</h1>
      </div>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <div className="card opacity-0 animate-fade-up stagger-1">
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Total Executions</p>
          <p className="text-5xl font-light text-forest">{stats.totalAgreements}</p>
        </div>

        <Link href="/admin/reviews" className="card-interactive opacity-0 animate-fade-up stagger-2">
          <div className="flex items-center justify-between mb-2">
            <p className="text-micro uppercase tracking-widest text-muted">Open Reviews</p>
            {stats.openReviews > 0 && (
              <span className="badge-warning">Needs attention</span>
            )}
          </div>
          <p className="text-5xl font-light text-forest">{stats.openReviews}</p>
        </Link>

        <div className="card opacity-0 animate-fade-up stagger-3">
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Recent Decisions</p>
          <p className="text-5xl font-light text-forest">{stats.recentDecisions.length}</p>
        </div>
      </div>

      {/* Data Tables */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Recent Executions */}
        <div className="card opacity-0 animate-fade-up stagger-4">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-title">Recent Executions</h2>
            <Link href="/create" className="btn-ghost text-sm">
              Create New
            </Link>
          </div>

          {stats.recentAgreements.length === 0 ? (
            <p className="text-body text-muted">No executions yet</p>
          ) : (
            <div className="space-y-4">
              {stats.recentAgreements.map((agreement) => (
                <div
                  key={agreement.id}
                  className="flex items-center justify-between py-4 border-b-2 border-border last:border-0"
                >
                  <div>
                    <p className="font-medium mb-1">{agreement.title}</p>
                    <p className="text-sm text-muted">
                      {formatCurrency(agreement.amount, agreement.currency)}
                    </p>
                  </div>
                  <span className={getStatusBadge(agreement.status)}>
                    {agreement.status.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Decisions */}
        <div className="card opacity-0 animate-fade-up stagger-5">
          <h2 className="text-title mb-6">Recent Decisions</h2>

          {stats.recentDecisions.length === 0 ? (
            <p className="text-body text-muted">No decisions yet</p>
          ) : (
            <div className="space-y-4">
              {stats.recentDecisions.map((decision) => (
                <div
                  key={decision.id}
                  className="py-4 border-b-2 border-border last:border-0"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">
                      {decision.decision_type.replace(/_/g, ' ')}
                    </span>
                    <span className={getStatusBadge(decision.outcome)}>
                      {decision.outcome}
                    </span>
                  </div>
                  <p className="text-sm text-muted truncate mb-1">
                    {decision.reason}
                  </p>
                  <p className="text-micro text-muted">
                    {formatDate(decision.created_at)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
