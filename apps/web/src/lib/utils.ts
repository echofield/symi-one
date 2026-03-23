import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: string | number, currency: string = 'usd'): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
  }).format(num)
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'draft':
      return 'bg-gray-100 text-gray-800'
    case 'awaiting_funding':
      return 'bg-yellow-100 text-yellow-800'
    case 'funded':
      return 'bg-blue-100 text-blue-800'
    case 'proof_submitted':
    case 'validating':
      return 'bg-purple-100 text-purple-800'
    case 'passed':
    case 'paid':
    case 'captured':
      return 'bg-green-100 text-green-800'
    case 'failed':
    case 'rejected':
    case 'cancelled':
      return 'bg-red-100 text-red-800'
    case 'manual_review_required':
    case 'open':
      return 'bg-orange-100 text-orange-800'
    case 'resolved':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}
