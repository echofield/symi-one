'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { getReview, resolveReview } from '@/lib/api'
import { formatDate, formatCurrency } from '@/lib/utils'

interface ReviewDetail {
  review: {
    id: string
    agreement_id: string
    submission_id: string
    reason: string
    status: string
    resolution: string | null
    resolved_at: string | null
    created_at: string
  }
  agreement: Record<string, unknown>
  submission: Record<string, unknown>
  validation_results: Array<Record<string, unknown>>
}

function getStatusBadge(status: string) {
  const statusMap: Record<string, string> = {
    'passed': 'badge-success',
    'funded': 'badge-success',
    'completed': 'badge-success',
    'resolved': 'badge-success',
    'approved': 'badge-success',
    'validating': 'badge-info',
    'submitted': 'badge-info',
    'pending': 'badge-warning',
    'open': 'badge-warning',
    'draft': 'badge-default',
    'failed': 'badge-error',
    'rejected': 'badge-error',
  }
  return statusMap[status] || 'badge-default'
}

export default function ReviewDetailPage() {
  const params = useParams()
  const router = useRouter()
  const reviewId = params.id as string

  const [loading, setLoading] = useState(true)
  const [resolving, setResolving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ReviewDetail | null>(null)
  const [notes, setNotes] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const detail = await getReview(reviewId)
        setData(detail)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load review')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [reviewId])

  const handleResolve = async (resolution: 'approve' | 'reject') => {
    setResolving(true)
    setError(null)

    try {
      await resolveReview(reviewId, resolution, notes || undefined)
      router.push('/admin/reviews')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to resolve review')
      setResolving(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 lg:px-12 py-12">
        <div className="flex items-center gap-3 text-muted">
          <span className="spinner" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="max-w-4xl mx-auto px-6 lg:px-12 py-12">
        <div className="card max-w-md border-red-500">
          <div className="w-12 h-12 border-2 border-red-500 flex items-center justify-center mb-6">
            <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Error</p>
          <h1 className="text-title mb-4">Unable to Load</h1>
          <p className="text-body text-muted mb-6">{error}</p>
          <Link href="/admin/reviews" className="btn-secondary">
            Back to Reviews
          </Link>
        </div>
      </div>
    )
  }

  const isResolved = data?.review.status === 'resolved'

  return (
    <div className="max-w-4xl mx-auto px-6 lg:px-12 py-12">
      {/* Back Link */}
      <div className="mb-8 opacity-0 animate-fade-up">
        <Link href="/admin/reviews" className="text-sm text-muted hover:text-forest transition-colors">
          &larr; Back to Reviews
        </Link>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-12 opacity-0 animate-fade-up stagger-1">
        <div>
          <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Review</p>
          <h1 className="text-headline text-foreground mb-2">#{reviewId.slice(0, 8)}</h1>
          <p className="text-caption text-muted">
            Created {formatDate(data!.review.created_at)}
          </p>
        </div>
        <span className={getStatusBadge(data!.review.status)}>
          {data!.review.status}
        </span>
      </div>

      {/* Reason for Review */}
      <div className="card mb-6 opacity-0 animate-fade-up stagger-2">
        <p className="text-micro uppercase tracking-widest text-muted mb-4">Reason for Review</p>
        <p className="text-body">{data!.review.reason}</p>
      </div>

      {/* Execution Info */}
      <div className="card mb-6 opacity-0 animate-fade-up stagger-3">
        <p className="text-micro uppercase tracking-widest text-muted mb-6">Execution</p>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <p className="text-micro uppercase tracking-widest text-muted mb-2">Title</p>
            <p className="font-medium">{data!.agreement.title as string}</p>
          </div>
          <div>
            <p className="text-micro uppercase tracking-widest text-muted mb-2">Amount</p>
            <p className="font-medium">
              {formatCurrency(data!.agreement.amount as string, data!.agreement.currency as string)}
            </p>
          </div>
          <div>
            <p className="text-micro uppercase tracking-widest text-muted mb-2">Proof Type</p>
            <p className="capitalize">{data!.agreement.proof_type as string}</p>
          </div>
          <div>
            <p className="text-micro uppercase tracking-widest text-muted mb-2">Status</p>
            <span className={getStatusBadge(data!.agreement.status as string)}>
              {(data!.agreement.status as string).replace(/_/g, ' ')}
            </span>
          </div>
        </div>

        <div>
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Description</p>
          <p className="text-body text-muted">{data!.agreement.description as string}</p>
        </div>
      </div>

      {/* Submission Info */}
      <div className="card mb-6 opacity-0 animate-fade-up stagger-4">
        <p className="text-micro uppercase tracking-widest text-muted mb-6">Submission</p>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <p className="text-micro uppercase tracking-widest text-muted mb-2">Proof Type</p>
            <p className="capitalize">{data!.submission.proof_type as string}</p>
          </div>
          <div>
            <p className="text-micro uppercase tracking-widest text-muted mb-2">Status</p>
            <span className={getStatusBadge(data!.submission.status as string)}>
              {(data!.submission.status as string).replace(/_/g, ' ')}
            </span>
          </div>
        </div>

        {Boolean(data!.submission.url) && (
          <div className="mb-4">
            <p className="text-micro uppercase tracking-widest text-muted mb-2">URL</p>
            <div className="bg-surface border-2 border-border p-4 font-mono text-sm break-all">
              <a
                href={data!.submission.url as string}
                target="_blank"
                rel="noopener noreferrer"
                className="text-forest hover:underline"
              >
                {data!.submission.url as string}
              </a>
            </div>
          </div>
        )}

        {Boolean(data!.submission.file_name) && (
          <div className="mb-4">
            <p className="text-micro uppercase tracking-widest text-muted mb-2">File</p>
            <p className="text-body">{data!.submission.file_name as string}</p>
          </div>
        )}

        <div>
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Submitted At</p>
          <p className="text-body">{formatDate(data!.submission.submitted_at as string)}</p>
        </div>
      </div>

      {/* Validation Results */}
      <div className="card mb-6 opacity-0 animate-fade-up stagger-5">
        <p className="text-micro uppercase tracking-widest text-muted mb-6">Validation Results</p>

        {data!.validation_results.length === 0 ? (
          <p className="text-body text-muted">No validation results available</p>
        ) : (
          <div className="space-y-3">
            {data!.validation_results.map((result, i) => (
              <div
                key={i}
                className={`p-4 border-2 ${
                  result.passed
                    ? 'border-forest bg-forest-50'
                    : 'border-red-500 bg-red-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">
                    {(result.validator_type as string).replace(/_/g, ' ')}
                  </span>
                  <span className={result.passed ? 'badge-success' : 'badge-error'}>
                    {result.passed ? 'Passed' : 'Failed'}
                  </span>
                </div>
                {Boolean(result.details) && (
                  <pre className="text-sm text-muted whitespace-pre-wrap font-mono">
                    {JSON.stringify(result.details, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Resolution Form */}
      {!isResolved && (
        <div className="card opacity-0 animate-fade-up stagger-6">
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Action Required</p>
          <h2 className="text-title mb-2">Resolve Review</h2>
          <p className="text-caption text-muted mb-6">
            Approve or reject this submission. This action cannot be undone.
          </p>

          {error && (
            <div className="card border-red-500 bg-red-50 p-4 mb-6">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="mb-6">
            <label htmlFor="notes" className="label">Notes (optional)</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any notes about your decision..."
              className="input min-h-[100px] resize-none"
            />
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => handleResolve('approve')}
              disabled={resolving}
              className="flex-1 inline-flex items-center justify-center px-6 py-3 bg-forest text-white font-normal text-sm tracking-wide border-2 border-forest transition-all duration-200 hover:bg-forest-600 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {resolving ? (
                <>
                  <span className="spinner mr-2" />
                  Processing...
                </>
              ) : (
                'Approve & Release Payment'
              )}
            </button>
            <button
              onClick={() => handleResolve('reject')}
              disabled={resolving}
              className="flex-1 inline-flex items-center justify-center px-6 py-3 bg-red-600 text-white font-normal text-sm tracking-wide border-2 border-red-600 transition-all duration-200 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {resolving ? (
                <>
                  <span className="spinner mr-2" />
                  Processing...
                </>
              ) : (
                'Reject Submission'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Resolved Status */}
      {isResolved && (
        <div className="card opacity-0 animate-fade-up stagger-6">
          <p className="text-micro uppercase tracking-widest text-muted mb-4">Resolution</p>
          <div className="flex items-center gap-4">
            <span className={getStatusBadge(data!.review.resolution || '')}>
              {data!.review.resolution}
            </span>
            <span className="text-body text-muted">
              Resolved {formatDate(data!.review.resolved_at!)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
