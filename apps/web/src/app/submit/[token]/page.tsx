'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import {
  getSubmissionInfo,
  submitUrlProof,
  getPresignedUploadUrl,
  submitFileProof,
} from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'

interface SubmissionInfo {
  id: string
  title: string
  description: string
  amount: string
  currency: string
  proof_type: 'url' | 'file'
  status: string
  validation_rules: string[]
  is_funded: boolean
  submission?: {
    id: string
    status: string
    url?: string
    file_name?: string
    submitted_at: string
    validation_results?: Array<{
      validator_type: string
      passed: boolean
      details_json: Record<string, unknown>
    }>
  }
}

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
    'manual_review_required': 'badge-warning',
  }
  return statusMap[status] || 'badge-default'
}

export default function SubmitPage() {
  const params = useParams()
  const token = params.token as string

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<SubmissionInfo | null>(null)

  // URL submission
  const [url, setUrl] = useState('')

  // File submission
  const [file, setFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)

  const loadInfo = useCallback(async () => {
    try {
      const data = await getSubmissionInfo(token)
      setInfo(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load submission info')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadInfo()
  }, [loadInfo])

  // Poll for status updates after submission
  useEffect(() => {
    if (info?.submission?.status === 'validating' || info?.submission?.status === 'submitted') {
      const interval = setInterval(loadInfo, 3000)
      return () => clearInterval(interval)
    }
  }, [info?.submission?.status, loadInfo])

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      await submitUrlProof(token, url)
      await loadInfo()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to submit URL')
    } finally {
      setSubmitting(false)
    }
  }

  const handleFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    setSubmitting(true)
    setError(null)
    setUploadProgress(0)

    try {
      // Get presigned URL
      const presign = await getPresignedUploadUrl(
        token,
        file.name,
        file.type,
        file.size
      )

      // Upload file directly to R2
      const uploadResponse = await fetch(presign.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      })

      if (!uploadResponse.ok) {
        throw new Error('File upload failed')
      }

      setUploadProgress(100)

      // Submit file proof
      await submitFileProof(
        token,
        presign.object_key,
        file.name,
        file.type,
        file.size
      )

      await loadInfo()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to upload file')
    } finally {
      setSubmitting(false)
      setUploadProgress(0)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center gap-3 text-muted">
          <span className="spinner" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

  if (error && !info) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="card max-w-md w-full border-red-500">
          <div className="w-12 h-12 border-2 border-red-500 flex items-center justify-center mb-6">
            <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <p className="text-micro uppercase tracking-widest text-muted mb-2">Error</p>
          <h1 className="text-title mb-4">Unable to Load</h1>
          <p className="text-body text-muted mb-6">{error}</p>
          <Link href="/" className="btn-secondary">
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  if (!info?.is_funded) {
    return (
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b-2 border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="flex items-center h-16">
              <Link href="/" className="flex items-center gap-3">
                <div className="w-3 h-3 bg-forest" />
                <span className="text-sm font-medium tracking-wider uppercase">SYMIONE PAY</span>
              </Link>
            </div>
          </div>
        </header>

        <main className="max-w-2xl mx-auto px-6 py-20">
          <div className="opacity-0 animate-fade-up">
            {/* Waiting Icon */}
            <div className="w-16 h-16 border-2 border-border flex items-center justify-center mb-8">
              <svg className="w-8 h-8 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>

            <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Awaiting Funding</p>
            <h1 className="text-headline text-foreground mb-4">
              Execution Not Yet Funded
            </h1>
            <p className="text-body text-muted mb-8">
              This execution must be funded before proof can be submitted.
            </p>

            <div className="card">
              <p className="text-4xl font-light mb-2">
                {formatCurrency(info?.amount || '0', info?.currency)}
              </p>
              <p className="text-body text-muted">{info?.title}</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  const hasSubmission = !!info?.submission

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b-2 border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center h-16">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-3 h-3 bg-forest" />
              <span className="text-sm font-medium tracking-wider uppercase">SYMIONE PAY</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-20">
        {/* Execution Info */}
        <div className="mb-8 opacity-0 animate-fade-up">
          <p className="text-micro uppercase tracking-[0.3em] text-muted mb-4">Submit Proof</p>
          <h1 className="text-headline text-foreground mb-4">{info?.title}</h1>
          <p className="text-body text-muted">{info?.description}</p>
        </div>

        {/* Execution Details Card */}
        <div className="card mb-8 opacity-0 animate-fade-up stagger-1">
          <div className="flex items-center justify-between mb-6">
            <span className="text-micro uppercase tracking-widest text-muted">Payment on Success</span>
            <span className={getStatusBadge(info?.status || '')}>
              {info?.status?.replace(/_/g, ' ')}
            </span>
          </div>

          <p className="text-4xl font-light mb-6">
            {formatCurrency(info?.amount || '0', info?.currency)}
          </p>

          {info?.validation_rules && info.validation_rules.length > 0 && (
            <>
              <div className="h-px bg-border mb-6" />
              <div>
                <p className="text-sm text-muted mb-2">Validation Rules</p>
                <ul className="space-y-2">
                  {info.validation_rules.map((rule, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <span className="w-1 h-1 bg-forest" />
                      {rule}
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>

        {/* Submission Status Card */}
        {hasSubmission && (
          <div className="card mb-8 opacity-0 animate-fade-up stagger-2">
            <div className="flex items-center justify-between mb-4">
              <p className="text-micro uppercase tracking-widest text-muted">Submission Status</p>
              <span className={getStatusBadge(info.submission!.status)}>
                {info.submission!.status.replace(/_/g, ' ')}
              </span>
            </div>

            <p className="text-caption text-muted mb-6">
              Submitted: {formatDate(info.submission!.submitted_at)}
            </p>

            {info.submission!.url && (
              <div className="mb-4">
                <label className="label">URL Submitted</label>
                <div className="bg-surface border-2 border-border p-4 font-mono text-sm break-all">
                  {info.submission!.url}
                </div>
              </div>
            )}

            {info.submission!.file_name && (
              <div className="mb-4">
                <label className="label">File Submitted</label>
                <div className="bg-surface border-2 border-border p-4 text-sm">
                  {info.submission!.file_name}
                </div>
              </div>
            )}

            {/* Validation Results */}
            {info.submission!.validation_results && info.submission!.validation_results.length > 0 && (
              <div className="mt-6">
                <label className="label">Validation Results</label>
                <div className="space-y-3 mt-2">
                  {info.submission!.validation_results.map((result, i) => (
                    <div
                      key={i}
                      className={`p-4 border-2 ${
                        result.passed
                          ? 'border-forest bg-forest-50'
                          : 'border-red-500 bg-red-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{result.validator_type.replace(/_/g, ' ')}</span>
                        <span className={result.passed ? 'badge-success' : 'badge-error'}>
                          {result.passed ? 'Passed' : 'Failed'}
                        </span>
                      </div>
                      {Boolean(result.details_json?.reason) && (
                        <p className="mt-2 text-sm text-muted">
                          {String(result.details_json.reason)}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Status-specific messages */}
            {info.submission!.status === 'validating' && (
              <div className="flex items-center gap-3 p-4 border-2 border-forest bg-forest-50 mt-6">
                <span className="spinner text-forest" />
                <span className="text-forest font-medium">Validating submission...</span>
              </div>
            )}

            {info.submission!.status === 'passed' && (
              <div className="p-6 border-2 border-forest bg-forest-50 mt-6 text-center">
                <div className="w-12 h-12 border-2 border-forest flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-forest" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-forest font-medium">Validation Passed!</p>
                <p className="text-sm text-muted mt-1">
                  Payment will be released shortly.
                </p>
              </div>
            )}

            {info.submission!.status === 'failed' && (
              <div className="p-6 border-2 border-red-500 bg-red-50 mt-6 text-center">
                <div className="w-12 h-12 border-2 border-red-500 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <p className="text-red-600 font-medium">Validation Failed</p>
                <p className="text-sm text-muted mt-1">
                  Please review the validation results above.
                </p>
              </div>
            )}

            {info.submission!.status === 'manual_review_required' && (
              <div className="p-6 border-2 border-amber-500 bg-amber-50 mt-6 text-center">
                <div className="w-12 h-12 border-2 border-amber-500 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </div>
                <p className="text-amber-700 font-medium">Manual Review Required</p>
                <p className="text-sm text-muted mt-1">
                  Your submission is being reviewed by an administrator.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Submit Form - show only if no submission yet */}
        {!hasSubmission && (
          <div className="card opacity-0 animate-fade-up stagger-2">
            <p className="text-micro uppercase tracking-widest text-muted mb-2">Submit</p>
            <h2 className="text-title mb-2">Submit Your Proof</h2>
            <p className="text-caption text-muted mb-6">
              {info?.proof_type === 'url'
                ? 'Enter the URL that proves your work is complete.'
                : 'Upload a file that proves your work is complete.'}
            </p>

            {error && (
              <div className="card border-red-500 bg-red-50 p-4 mb-6">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {info?.proof_type === 'url' ? (
              <form onSubmit={handleUrlSubmit} className="space-y-6">
                <div>
                  <label htmlFor="url" className="label">URL</label>
                  <input
                    id="url"
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com/my-work"
                    className="input"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn-primary w-full justify-center"
                >
                  {submitting ? (
                    <>
                      <span className="spinner mr-2" />
                      Submitting...
                    </>
                  ) : (
                    'Submit URL'
                  )}
                </button>
              </form>
            ) : (
              <form onSubmit={handleFileSubmit} className="space-y-6">
                <div>
                  <label htmlFor="file" className="label">File</label>
                  <input
                    id="file"
                    type="file"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="input py-2"
                    required
                  />
                  {file && (
                    <p className="text-sm text-muted mt-2">
                      {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </p>
                  )}
                </div>
                {uploadProgress > 0 && uploadProgress < 100 && (
                  <div className="w-full h-2 bg-border">
                    <div
                      className="h-2 bg-forest transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                )}
                <button
                  type="submit"
                  disabled={submitting || !file}
                  className="btn-primary w-full justify-center"
                >
                  {submitting ? (
                    <>
                      <span className="spinner mr-2" />
                      Uploading...
                    </>
                  ) : (
                    'Upload & Submit'
                  )}
                </button>
              </form>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
