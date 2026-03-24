/**
 * Stripe Connect API client
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

export interface ConnectedAccount {
  id: string
  user_id: string
  email: string
  stripe_account_id: string
  charges_enabled: boolean
  payouts_enabled: boolean
  details_submitted: boolean
  country: string | null
  default_currency: string | null
  created_at: string
  can_transact: boolean
}

export interface AccountStatus {
  charges_enabled: boolean
  payouts_enabled: boolean
  details_submitted: boolean
  requirements: {
    currently_due: string[]
    eventually_due: string[]
    past_due: string[]
  }
  can_transact: boolean
}

// API Functions

export async function createAccount(data: {
  user_id: string
  email: string
  country?: string
}): Promise<ConnectedAccount> {
  return request('/api/v1/connect', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getAccountByUser(userId: string): Promise<ConnectedAccount> {
  return request(`/api/v1/connect/user/${encodeURIComponent(userId)}`)
}

export async function createOnboardingLink(
  userId: string,
  returnUrl: string,
  refreshUrl: string
): Promise<{ url: string }> {
  return request(`/api/v1/connect/onboarding-link?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    body: JSON.stringify({
      return_url: returnUrl,
      refresh_url: refreshUrl,
    }),
  })
}

export async function getAccountStatus(accountId: string): Promise<AccountStatus> {
  return request(`/api/v1/connect/accounts/${accountId}/status`)
}

export async function getDashboardLink(accountId: string): Promise<{ url: string }> {
  return request(`/api/v1/connect/accounts/${accountId}/dashboard`, {
    method: 'POST',
  })
}

// Utility functions

export function isAccountReady(account: ConnectedAccount | AccountStatus): boolean {
  return account.charges_enabled && account.payouts_enabled
}

export function getOnboardingStatus(account: ConnectedAccount | AccountStatus): 'complete' | 'pending' | 'not_started' {
  if (account.charges_enabled && account.payouts_enabled) {
    return 'complete'
  }
  if (account.details_submitted) {
    return 'pending'
  }
  return 'not_started'
}
