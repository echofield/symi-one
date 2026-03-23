const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Ensure endpoint has trailing slash (FastAPI requires it)
  const normalizedEndpoint = endpoint.includes('?')
    ? endpoint.replace('?', '/?')
    : endpoint.endsWith('/') ? endpoint : `${endpoint}/`
  const url = `${API_URL}${normalizedEndpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(response.status, error.detail || 'Request failed')
  }

  return response.json()
}

// Public API (no auth required)

export async function getPublicAgreement(token: string) {
  return request<{
    id: string
    title: string
    description: string
    amount: string
    currency: string
    proof_type: 'url' | 'file'
    status: string
    deadline_at: string | null
    validation_rules: string[]
    is_funded: boolean
    payer_email: string | null
  }>(`/api/public/agreements/${token}`)
}

export async function fundAgreement(token: string, returnUrl: string) {
  return request<{
    client_secret: string
    payment_intent_id: string
  }>(`/api/public/agreements/${token}/fund`, {
    method: 'POST',
    body: JSON.stringify({ return_url: returnUrl }),
  })
}

export async function getSubmissionInfo(token: string) {
  return request<{
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
  }>(`/api/public/submissions/${token}`)
}

export async function submitUrlProof(token: string, url: string) {
  return request<{
    submission: {
      id: string
      status: string
      url: string
      submitted_at: string
    }
  }>(`/api/public/submissions/${token}/url`, {
    method: 'POST',
    body: JSON.stringify({ url }),
  })
}

export async function getPresignedUploadUrl(
  token: string,
  fileName: string,
  mimeType: string,
  sizeBytes: number
) {
  return request<{
    upload_url: string
    object_key: string
    expires_at: string
  }>(`/api/public/submissions/${token}/presign`, {
    method: 'POST',
    body: JSON.stringify({
      file_name: fileName,
      mime_type: mimeType,
      size_bytes: sizeBytes,
    }),
  })
}

export async function submitFileProof(
  token: string,
  fileKey: string,
  fileName: string,
  mimeType: string,
  sizeBytes: number
) {
  return request<{
    submission: {
      id: string
      status: string
      file_key: string
      file_name: string
      submitted_at: string
    }
  }>(`/api/public/submissions/${token}/file`, {
    method: 'POST',
    body: JSON.stringify({
      file_key: fileKey,
      file_name: fileName,
      mime_type: mimeType,
      size_bytes: sizeBytes,
    }),
  })
}

// Admin API

export async function createAgreement(data: {
  title: string
  description: string
  amount: number
  currency?: string
  proof_type: 'url' | 'file'
  validation_config: Record<string, unknown>
  payer_email?: string
  payee_email?: string
  deadline_at?: string
}) {
  return request<{
    agreement: {
      id: string
      public_id: string
      title: string
      status: string
      funding_url_token: string
      submit_url_token: string
      created_at: string
    }
    funding_url: string
    submit_url: string
  }>('/api/agreements', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getAgreement(id: string) {
  return request<{
    id: string
    public_id: string
    title: string
    description: string
    amount: string
    currency: string
    proof_type: 'url' | 'file'
    status: string
    payer_email: string | null
    payee_email: string | null
    funding_url_token: string
    submit_url_token: string
    deadline_at: string | null
    created_at: string
    updated_at: string
    validation_config?: Record<string, unknown>
    payment?: {
      id: string
      status: string
      funded_at: string | null
      captured_at: string | null
    }
    submissions?: Array<{
      id: string
      status: string
      submitted_at: string
    }>
  }>(`/api/agreements/${id}`)
}

export async function listAgreements(params?: { skip?: number; limit?: number }) {
  const query = new URLSearchParams()
  if (params?.skip) query.set('skip', params.skip.toString())
  if (params?.limit) query.set('limit', params.limit.toString())
  const queryString = query.toString() ? `?${query.toString()}` : ''

  return request<{
    agreements: Array<{
      id: string
      public_id: string
      title: string
      amount: string
      currency: string
      status: string
      created_at: string
    }>
    total: number
  }>(`/api/agreements${queryString}`)
}

// Reviews API

export async function listOpenReviews(params?: { skip?: number; limit?: number }) {
  const query = new URLSearchParams()
  if (params?.skip) query.set('skip', params.skip.toString())
  if (params?.limit) query.set('limit', params.limit.toString())
  const queryString = query.toString() ? `?${query.toString()}` : ''

  return request<{
    reviews: Array<{
      id: string
      agreement_id: string
      submission_id: string
      reason: string
      status: string
      resolution: string | null
      created_at: string
    }>
    total: number
  }>(`/api/admin/reviews/open${queryString}`)
}

export async function getReview(id: string) {
  return request<{
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
  }>(`/api/admin/reviews/${id}`)
}

export async function resolveReview(id: string, resolution: 'approve' | 'reject', notes?: string) {
  return request<{
    id: string
    status: string
    resolution: string
    resolved_at: string
  }>(`/api/admin/reviews/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ resolution, notes }),
  })
}

// Decisions API

export async function listDecisions(params?: { agreement_id?: string; skip?: number; limit?: number }) {
  const query = new URLSearchParams()
  if (params?.agreement_id) query.set('agreement_id', params.agreement_id)
  if (params?.skip) query.set('skip', params.skip.toString())
  if (params?.limit) query.set('limit', params.limit.toString())
  const queryString = query.toString() ? `?${query.toString()}` : ''

  return request<{
    decisions: Array<{
      id: string
      agreement_id: string
      decision_type: string
      outcome: string
      reason: string
      created_at: string
    }>
    total: number
  }>(`/api/admin/decisions${queryString}`)
}
