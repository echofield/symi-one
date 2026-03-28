'use client'

import Link from 'next/link'
import { useState, useRef } from 'react'

const SERVICE_TEMPLATES = [
  { id: 'mix-master', title: 'Mix & Master', description: 'Full mix and master for a track', defaultPrice: 200 },
  { id: 'beat', title: 'Beat Production', description: 'Custom beat or instrumental', defaultPrice: 150 },
  { id: 'recording', title: 'Recording Session', description: 'Studio time + engineering', defaultPrice: 100 },
  { id: 'sound-design', title: 'Sound Design', description: 'Custom sounds, FX, or samples', defaultPrice: 250 },
  { id: 'podcast', title: 'Podcast Editing', description: 'Edit, clean, and master episode', defaultPrice: 75 },
  { id: 'ghost', title: 'Ghost Production', description: 'Full track, your name on it', defaultPrice: 500 },
  { id: 'vocal-tuning', title: 'Vocal Tuning', description: 'Pitch correction and editing', defaultPrice: 50 },
  { id: 'artwork', title: 'Album Artwork', description: 'Cover art design', defaultPrice: 100 },
]

export default function MusicPage() {
  const [role, setRole] = useState<'freelancer' | 'client'>('freelancer')
  const [selected, setSelected] = useState<string | null>(null)
  const [price, setPrice] = useState<number>(0)
  const [customTitle, setCustomTitle] = useState('')
  const [showConfig, setShowConfig] = useState(false)
  const configRef = useRef<HTMLDivElement>(null)

  const selectedTemplate = SERVICE_TEMPLATES.find(t => t.id === selected)

  const handleSelect = (template: typeof SERVICE_TEMPLATES[0]) => {
    setSelected(template.id)
    setPrice(template.defaultPrice)
    setCustomTitle(template.title)
    setShowConfig(false)
  }

  const handleContinue = () => {
    setShowConfig(true)
    setTimeout(() => {
      configRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 100)
  }

  const handleCreate = () => {
    if (!selectedTemplate) return
    const params = new URLSearchParams({
      title: customTitle,
      amount: price.toString(),
      proof_type: 'file',
      description: selectedTemplate.description,
    })
    window.location.href = `/create?${params.toString()}`
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      {/* Header */}
      <header className="border-b-2 border-border">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-2 h-2 bg-forest" />
            <span className="text-sm font-medium tracking-wider uppercase">SYMIONE</span>
          </Link>
          <span className="text-xs text-muted tracking-wide">Payment unlocks on delivery</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10">
        {/* Role Toggle */}
        <div className="flex gap-2 mb-8">
          <button
            onClick={() => setRole('freelancer')}
            className={`px-4 py-2 text-sm border-2 transition-all ${
              role === 'freelancer'
                ? 'border-forest bg-forest text-white'
                : 'border-border text-muted hover:border-foreground'
            }`}
          >
            I deliver work
          </button>
          <button
            onClick={() => setRole('client')}
            className={`px-4 py-2 text-sm border-2 transition-all ${
              role === 'client'
                ? 'border-forest bg-forest text-white'
                : 'border-border text-muted hover:border-foreground'
            }`}
          >
            I hire talent
          </button>
        </div>

        {/* Headline + Emotional Hook */}
        <div className="mb-8">
          <h1 className="text-3xl font-light mb-3">
            {role === 'freelancer'
              ? 'Get paid when you deliver'
              : "Don't pay until it's delivered"
            }
          </h1>
          <p className="text-muted">
            {role === 'freelancer'
              ? 'No more 50% upfront that vanishes. No more chasing invoices.'
              : 'Your money stays locked until work is submitted.'
            }
          </p>
        </div>

        {/* Primary CTA */}
        {!selected && (
          <div className="mb-12 p-6 border-2 border-forest bg-forest/5">
            <p className="text-lg font-medium mb-2">
              {role === 'freelancer'
                ? 'Create your first payment link'
                : 'Set up a secure deal'
              }
            </p>
            <p className="text-sm text-muted mb-4">
              Select a service below. Takes 30 seconds.
            </p>
          </div>
        )}

        {/* Service Grid */}
        <div className="grid md:grid-cols-2 gap-4 mb-10">
          {SERVICE_TEMPLATES.map((template) => {
            const isSelected = selected === template.id
            return (
              <button
                key={template.id}
                onClick={() => handleSelect(template)}
                className={`p-6 text-left border-2 transition-all relative ${
                  isSelected
                    ? 'border-forest bg-forest/5'
                    : 'border-border hover:border-foreground'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-lg font-medium mb-1">{template.title}</p>
                    <p className="text-sm text-muted">{template.description}</p>
                  </div>
                  {isSelected && (
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 bg-forest flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      </span>
                    </div>
                  )}
                </div>
                {isSelected && (
                  <p className="text-xs text-forest mt-3 font-medium">Ready to configure</p>
                )}
              </button>
            )
          })}
        </div>

        {/* Config Panel */}
        {showConfig && selectedTemplate && (
          <div ref={configRef} className="border-2 border-foreground p-8 space-y-6 mb-10">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted uppercase tracking-wider">Configure</span>
              <button
                onClick={() => { setSelected(null); setShowConfig(false) }}
                className="text-sm text-muted hover:text-foreground"
              >
                Start over
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-muted mb-2">Service</label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  className="w-full p-3 border-2 border-border bg-transparent text-lg focus:border-forest focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm text-muted mb-2">Price (EUR)</label>
                <input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(Number(e.target.value))}
                  className="w-full p-3 border-2 border-border bg-transparent text-3xl font-light focus:border-forest focus:outline-none"
                  min={1}
                />
              </div>
            </div>

            <button
              onClick={handleCreate}
              disabled={!price || price < 1}
              className="w-full py-4 bg-forest text-white font-medium hover:bg-forest/90 transition-colors disabled:opacity-50"
            >
              Create Payment Link
            </button>

            <p className="text-center text-sm text-muted">
              {role === 'freelancer'
                ? 'Share link with client. Get paid when you deliver.'
                : 'Share link. Pay securely. Release on delivery.'
              }
            </p>
          </div>
        )}
      </main>

      {/* Fixed Bottom Bar - appears when selected */}
      {selected && !showConfig && (
        <div className="fixed bottom-0 left-0 right-0 bg-background border-t-2 border-foreground">
          <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium">{selectedTemplate?.title}</p>
              <p className="text-sm text-muted">Ready</p>
            </div>
            <button
              onClick={handleContinue}
              className="px-8 py-3 bg-forest text-white font-medium hover:bg-forest/90 transition-colors flex items-center gap-2"
            >
              Continue
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Minimal Footer - only when no bottom bar */}
      {(!selected || showConfig) && (
        <footer className="border-t-2 border-border mt-auto">
          <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between text-sm text-muted">
            <span>Powered by Stripe</span>
            <span>5% on successful payments</span>
          </div>
        </footer>
      )}
    </div>
  )
}
