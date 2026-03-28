'use client'

import { useState } from 'react'

const SERVICES = [
  'Mix & Master',
  'Beat Production',
  'Recording Session',
  'Sound Design',
  'Podcast Editing',
  'Ghost Production',
  'Vocal Tuning',
  'Album Artwork',
  'Other',
]

export default function MusicPage() {
  const [service, setService] = useState('')
  const [customService, setCustomService] = useState('')
  const [price, setPrice] = useState<number | ''>('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)

  const displayService = service === 'Other' ? customService : service
  const isValid = displayService && price && Number(price) >= 1

  const handleSubmit = async () => {
    if (!isValid) return
    setLoading(true)

    const params = new URLSearchParams({
      title: displayService,
      amount: String(price),
      proof_type: 'file',
      ...(email && { email }),
    })
    window.location.href = `/create?${params.toString()}`
  }

  return (
    <div className="min-h-screen bg-[#fafafa] flex flex-col">
      {/* Centered Content */}
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2 mb-10">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-[#1a1a1a]">
              <rect x="2" y="2" width="16" height="16" rx="2" stroke="currentColor" strokeWidth="2" fill="none"/>
              <path d="M6 10l3 3 5-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span className="text-sm font-semibold tracking-wider uppercase">SYMIONE</span>
          </div>

          {/* Card */}
          <div className="bg-white rounded-2xl shadow-[0_2px_20px_rgba(0,0,0,0.08)] p-8">
            {/* Service */}
            <div className="mb-5">
              <label className="block text-sm text-gray-500 mb-2">Service</label>
              <select
                value={service}
                onChange={(e) => setService(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-lg bg-white text-base focus:border-[#1a1a1a] focus:outline-none appearance-none cursor-pointer"
                style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center' }}
              >
                <option value="">Select service...</option>
                {SERVICES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Custom service input */}
            {service === 'Other' && (
              <div className="mb-5">
                <label className="block text-sm text-gray-500 mb-2">Describe the work</label>
                <input
                  type="text"
                  value={customService}
                  onChange={(e) => setCustomService(e.target.value)}
                  placeholder="e.g., 3 track EP mix"
                  className="w-full p-3 border border-gray-200 rounded-lg text-base focus:border-[#1a1a1a] focus:outline-none"
                />
              </div>
            )}

            {/* Price */}
            <div className="mb-5">
              <label className="block text-sm text-gray-500 mb-2">Price</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">€</span>
                <input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value ? Number(e.target.value) : '')}
                  placeholder="200"
                  min={1}
                  className="w-full p-3 pl-8 border border-gray-200 rounded-lg text-base focus:border-[#1a1a1a] focus:outline-none"
                />
              </div>
            </div>

            {/* Email */}
            <div className="mb-6">
              <label className="block text-sm text-gray-500 mb-2">Your email <span className="text-gray-300">(optional)</span></label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@email.com"
                className="w-full p-3 border border-gray-200 rounded-lg text-base focus:border-[#1a1a1a] focus:outline-none"
              />
            </div>

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={!isValid || loading}
              className="w-full py-3.5 bg-[#1a1a1a] text-white font-medium rounded-lg hover:bg-[#333] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Get payment link'}
            </button>

            {/* Tagline */}
            <div className="mt-6 pt-5 border-t border-gray-100 text-center">
              <p className="text-sm text-gray-400">
                Payment unlocks when you confirm delivery
              </p>
            </div>
          </div>

          {/* Stripe badge */}
          <div className="mt-8 flex items-center justify-center gap-2 text-gray-400">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z"/>
            </svg>
            <span className="text-xs">Powered by Stripe</span>
          </div>
        </div>
      </main>
    </div>
  )
}
