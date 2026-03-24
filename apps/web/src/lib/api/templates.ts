/**
 * Templates marketplace API client
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

export interface MarketplaceTemplate {
  id: string
  name: string
  description: string
  long_description: string
  icon: string
  price: number // cents
  is_pro: boolean
  repo_url: string | null
  deploy_url: string | null
  stack: string[]
  use_cases: string[]
  features: string[]
}

export interface PurchaseResponse {
  client_secret: string
  payment_intent_id: string
  template_id: string
  template_name: string
  amount: number
  currency: string
}

export interface DeliveryResponse {
  template_id: string
  template_name: string
  buyer_email: string
  delivery_method: string
  instructions: string
  repo_url: string | null
  deploy_url: string | null
}

// API Functions

export async function getMarketplaceTemplates(): Promise<{ templates: MarketplaceTemplate[] }> {
  return request('/api/v1/templates')
}

export async function getMarketplaceTemplate(id: string): Promise<MarketplaceTemplate> {
  return request(`/api/v1/templates/${id}`)
}

export async function createTemplatePurchase(
  templateId: string,
  email: string
): Promise<PurchaseResponse> {
  return request('/api/v1/templates/purchase', {
    method: 'POST',
    body: JSON.stringify({
      template_id: templateId,
      email,
    }),
  })
}

export async function confirmTemplatePurchase(
  paymentIntentId: string,
  email: string
): Promise<DeliveryResponse> {
  return request('/api/v1/templates/purchase/confirm', {
    method: 'POST',
    body: JSON.stringify({
      payment_intent_id: paymentIntentId,
      email,
    }),
  })
}

// Utility functions

export function formatPrice(cents: number): string {
  if (cents === 0) return 'Free'
  return `€${(cents / 100).toFixed(0)}`
}
