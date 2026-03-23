'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { listOpenReviews } from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface Review {
  id: string
  agreement_id: string
  submission_id: string
  reason: string
  status: string
  resolution: string | null
  created_at: string
}

function getStatusBadge(status: string) {
  const statusMap: Record<string, string> = {
    'pending': 'badge-warning',
    'resolved': 'badge-success',
    'open': 'badge-info',
  }
  return statusMap[status] || 'badge-default'
}

export default function ReviewsPage() {
  const [loading, setLoading] = useState(true)
  const [reviews, setReviews] = useState<Review[]>([])
  const [total, setTotal] = useState(0)

  useEffect(() => {
    async function load() {
      try {
        const data = await listOpenReviews({ limit: 50 })
        setReviews(data.reviews)
        setTotal(data.total)
      } catch (err) {
        console.error('Failed to load reviews:', err)
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
        <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Queue</p>
        <h1 className="text-headline text-foreground mb-2">Manual Reviews</h1>
        <p className="text-body text-muted">
          {total} open review{total !== 1 ? 's' : ''} requiring attention
        </p>
      </div>

      {reviews.length === 0 ? (
        <div className="card text-center py-16 opacity-0 animate-fade-up stagger-1">
          <div className="w-16 h-16 border-2 border-forest flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-forest" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-title mb-2">All caught up!</h3>
          <p className="text-body text-muted">No reviews pending at this time.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review, i) => (
            <div
              key={review.id}
              className="card-interactive opacity-0 animate-fade-up"
              style={{ animationDelay: `${0.1 + i * 0.05}s` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-micro uppercase tracking-widest text-muted mb-2">
                    Review #{review.id.slice(0, 8)}
                  </p>
                  <p className="text-caption text-muted">
                    Created {formatDate(review.created_at)}
                  </p>
                </div>
                <span className={getStatusBadge(review.status)}>
                  {review.status}
                </span>
              </div>

              <div className="mb-6">
                <p className="text-micro uppercase tracking-widest text-muted mb-2">Reason for review</p>
                <p className="text-body">{review.reason}</p>
              </div>

              <Link href={`/admin/reviews/${review.id}`} className="btn-primary">
                Review Details
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
