'use client'

import Link from 'next/link'

export default function MusicPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Hero */}
      <div className="max-w-2xl mx-auto px-6 pt-20 pb-16">
        <div className="text-center mb-12">
          <div className="text-4xl mb-6">🎧</div>
          <h1 className="text-4xl md:text-5xl font-bold mb-6 leading-tight">
            Get paid when you deliver.
          </h1>
          <p className="text-xl text-gray-400">
            Not before. Not maybe. When it's done.
          </p>
        </div>

        {/* Example Card */}
        <div className="bg-[#141414] border border-gray-800 rounded-2xl p-8 mb-12">
          <div className="flex justify-between items-start mb-6">
            <div>
              <div className="text-sm text-gray-500 mb-1">EXAMPLE</div>
              <div className="text-2xl font-semibold">Mix & Master</div>
            </div>
            <div className="text-3xl font-bold">€200</div>
          </div>

          <div className="space-y-3 mb-8">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-emerald-900/50 flex items-center justify-center">
                <svg className="w-3 h-3 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="text-gray-300">Client pays → money locked</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-emerald-900/50 flex items-center justify-center">
                <svg className="w-3 h-3 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="text-gray-300">You deliver → payment released</span>
            </div>
          </div>

          <Link
            href="/create"
            className="block w-full bg-white text-black text-center py-4 rounded-xl font-semibold hover:bg-gray-100 transition-colors"
          >
            Create this deal
          </Link>
        </div>

        {/* Pain Points */}
        <div className="mb-16">
          <div className="text-sm text-gray-500 mb-4">NO MORE:</div>
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-gray-400">
              <span className="text-red-500">×</span>
              <span>50% upfront that disappears with the client</span>
            </div>
            <div className="flex items-center gap-3 text-gray-400">
              <span className="text-red-500">×</span>
              <span>"I'll pay you next week" that never comes</span>
            </div>
            <div className="flex items-center gap-3 text-gray-400">
              <span className="text-red-500">×</span>
              <span>Awkward invoice follow-ups</span>
            </div>
            <div className="flex items-center gap-3 text-gray-400">
              <span className="text-red-500">×</span>
              <span>Working for free on "exposure"</span>
            </div>
          </div>
        </div>

        {/* How it works */}
        <div className="mb-16">
          <div className="text-sm text-gray-500 mb-6">HOW IT WORKS</div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-3xl font-bold text-white mb-2">1</div>
              <div className="text-sm text-gray-400">Create deal</div>
              <div className="text-xs text-gray-600">2 minutes</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white mb-2">2</div>
              <div className="text-sm text-gray-400">Client funds</div>
              <div className="text-xs text-gray-600">Stripe secure</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white mb-2">3</div>
              <div className="text-sm text-gray-400">Deliver & paid</div>
              <div className="text-xs text-gray-600">Instant release</div>
            </div>
          </div>
        </div>

        {/* Use Cases */}
        <div className="mb-16">
          <div className="text-sm text-gray-500 mb-4">WORKS FOR</div>
          <div className="flex flex-wrap gap-2">
            {['Mix & Master', 'Beat Production', 'Vocal Recording', 'Sound Design', 'Podcast Editing', 'Music Video', 'Album Artwork', 'Ghost Production'].map((item) => (
              <span key={item} className="px-3 py-1 bg-gray-800 rounded-full text-sm text-gray-300">
                {item}
              </span>
            ))}
          </div>
        </div>

        {/* Final CTA */}
        <div className="text-center mb-12">
          <Link
            href="/create"
            className="inline-block bg-white text-black px-8 py-4 rounded-xl font-semibold hover:bg-gray-100 transition-colors"
          >
            Create your first deal
          </Link>
          <p className="text-sm text-gray-600 mt-4">
            Free to create. 5% only on successful payments.
          </p>
        </div>

        {/* Trust */}
        <div className="text-center text-sm text-gray-600 space-y-2">
          <div className="flex items-center justify-center gap-4">
            <span>🔒 Powered by Stripe</span>
            <span>·</span>
            <span>No subscription</span>
            <span>·</span>
            <span>No monthly fees</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 mt-12">
        <div className="max-w-2xl mx-auto px-6 text-center text-sm text-gray-600">
          <Link href="/" className="hover:text-white transition-colors">
            SYMIONE
          </Link>
          <span className="mx-2">·</span>
          <span>Payments that execute</span>
        </div>
      </footer>
    </div>
  )
}
