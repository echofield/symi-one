/**
 * Challenge API client
 */

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

// Types

export type ChallengeType = 'simple_bet' | 'fitness' | 'delivery' | 'accountability' | 'custom'
export type ChallengeStatus = 'pending_acceptance' | 'active' | 'awaiting_proof' | 'resolving' | 'resolved' | 'disputed' | 'cancelled' | 'expired'
export type ChallengeResolutionType = 'party_a_wins' | 'party_b_wins' | 'draw' | 'disputed' | 'expired'
export type ChallengeProofType = 'attestation' | 'file' | 'url' | 'api' | 'check_in'

export interface ChallengeProof {
  id: string
  submitted_by: string
  proof_type: ChallengeProofType
  proof_data: Record<string, unknown>
  proof_hash: string
  attested_outcome: string | null
  file_key: string | null
  file_name: string | null
  url: string | null
  submitted_at: string
}

export interface ChallengeEvent {
  id: string
  event_type: string
  actor_id: string | null
  details: Record<string, unknown>
  created_at: string
}

export interface Challenge {
  id: string
  public_id: string
  challenge_type: ChallengeType
  title: string
  description: string
  conditions_json: Record<string, unknown>
  party_a_id: string
  party_b_id: string | null
  party_a_email: string
  party_b_email: string | null
  stake_amount: string
  currency: string
  platform_fee_percent: string
  party_a_funded: boolean
  party_b_funded: boolean
  status: ChallengeStatus
  winner_id: string | null
  resolution_type: ChallengeResolutionType | null
  resolution_reason: string | null
  dispute_window_hours: number
  timeout_resolution: string
  proof_deadline: string | null
  acceptance_deadline: string | null
  created_at: string
  accepted_at: string | null
  resolved_at: string | null
  invite_token: string
  invite_url: string | null
  proofs: ChallengeProof[]
  events: ChallengeEvent[]
}

export interface ChallengeTemplate {
  type: ChallengeType
  name: string
  description: string
  resolution_method: string
  default_dispute_window_hours: number
  proof_requirements: Record<string, unknown>
}

export interface ChallengeStats {
  total_challenges: number
  active: number
  pending: number
  resolved: number
  disputed: number
  wins: number
  losses: number
  win_rate: number
  total_staked: string
  total_won: string
  total_lost: string
}

export interface RecentChallenge {
  id: string
  challenge_type: ChallengeType
  stake_amount: string
  currency: string
  resolution_type: ChallengeResolutionType | null
  resolved_at: string | null
  duration_hours: number | null
}

// API Functions

export async function getTemplates(): Promise<{ templates: ChallengeTemplate[] }> {
  return request('/api/v1/challenges/templates')
}

export async function getRecentChallenges(limit = 10): Promise<RecentChallenge[]> {
  return request(`/api/v1/challenges/recent?limit=${limit}`)
}

export async function createChallenge(data: {
  challenge_type: ChallengeType
  title: string
  description: string
  stake_amount: number
  currency?: string
  platform_fee_percent?: number
  proof_deadline?: string
  opponent_email?: string
  template_params?: Record<string, unknown>
}, userId: string, userEmail: string): Promise<Challenge> {
  return request(`/api/v1/challenges?user_id=${encodeURIComponent(userId)}&user_email=${encodeURIComponent(userEmail)}`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getChallenge(id: string): Promise<Challenge> {
  return request(`/api/v1/challenges/${id}`)
}

export async function getChallengeByInvite(token: string): Promise<Challenge> {
  return request(`/api/v1/challenges/invite/${token}`)
}

export async function acceptChallenge(id: string, userId: string, userEmail: string): Promise<Challenge> {
  return request(`/api/v1/challenges/${id}/accept?user_id=${encodeURIComponent(userId)}&user_email=${encodeURIComponent(userEmail)}`, {
    method: 'POST',
  })
}

export async function getMyChallenges(
  userId: string,
  params?: { status?: string; limit?: number; offset?: number }
): Promise<{ challenges: Challenge[]; total: number }> {
  const query = new URLSearchParams({ user_id: userId })
  if (params?.status) query.set('status', params.status)
  if (params?.limit) query.set('limit', params.limit.toString())
  if (params?.offset) query.set('offset', params.offset.toString())

  return request(`/api/v1/challenges/me?${query.toString()}`)
}

export async function getMyStats(userId: string): Promise<ChallengeStats> {
  return request(`/api/v1/challenges/me/stats?user_id=${encodeURIComponent(userId)}`)
}

export async function createFundingPayment(
  challengeId: string,
  userId: string
): Promise<{ client_secret: string; payment_intent_id: string }> {
  return request(`/api/v1/challenges/${challengeId}/fund?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
  })
}

export async function submitProof(
  challengeId: string,
  userId: string,
  data: {
    proof_type: ChallengeProofType
    proof_data: Record<string, unknown>
    attested_outcome?: string
    file_key?: string
    file_name?: string
    url?: string
  }
): Promise<ChallengeProof> {
  return request(`/api/v1/challenges/${challengeId}/proof?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function resolveChallenge(
  challengeId: string,
  data: {
    resolution_type: ChallengeResolutionType
    reason?: string
  }
): Promise<Challenge> {
  return request(`/api/v1/challenges/${challengeId}/resolve`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function cancelChallenge(challengeId: string, userId: string): Promise<Challenge> {
  return request(`/api/v1/challenges/${challengeId}/cancel?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
  })
}

export async function evaluateSimpleBet(challengeId: string): Promise<Challenge> {
  return request(`/api/v1/challenges/${challengeId}/evaluate-bet`, {
    method: 'POST',
  })
}

// Utility functions

export function formatStake(amount: string, currency: string): string {
  const num = parseFloat(amount)
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })
  return formatter.format(num)
}

export function getChallengeStatusLabel(status: ChallengeStatus): string {
  const labels: Record<ChallengeStatus, string> = {
    pending_acceptance: 'Waiting for opponent',
    active: 'Active',
    awaiting_proof: 'Submit proof',
    resolving: 'Resolving',
    resolved: 'Resolved',
    disputed: 'Disputed',
    cancelled: 'Cancelled',
    expired: 'Expired',
  }
  return labels[status] || status
}

export function getChallengeTypeLabel(type: ChallengeType): string {
  const labels: Record<ChallengeType, string> = {
    simple_bet: 'Simple Bet',
    fitness: 'Fitness',
    delivery: 'Delivery',
    accountability: 'Accountability',
    custom: 'Custom',
  }
  return labels[type] || type
}
