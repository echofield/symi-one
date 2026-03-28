'use client'

import Link from 'next/link'
import { useState } from 'react'

const SERVICE_TEMPLATES = [
  {
    id: 'mix-master',
    title: 'Mix & Master',
    description: 'Full mix and master for a track',
    defaultPrice: 200,
    proofType: 'file' as const,
  },
  {
    id: 'beat',
    title: 'Beat Production',
    description: 'Custom beat or instrumental',
    defaultPrice: 150,
    proofType: 'file' as const,
  },
  {
    id: 'recording',
    title: 'Recording Session',
    description: 'Studio time + engineering',
    defaultPrice: 100,
    proofType: 'file' as const,
  },
  {
    id: 'sound-design',
    title: 'Sound Design',
    description: 'Custom sounds, FX, or samples',
    defaultPrice: 250,
    proofType: 'file' as const,
  },
  {
    id: 'podcast',
    title: 'Podcast Editing',
    description: 'Edit, clean, and master episode',
    defaultPrice: 75,
    proofType: 'file' as const,
  },
  {
    id: 'ghost',
    title: 'Ghost Production',
    description: 'Full track, your name on it',
    defaultPrice: 500,
    proofType: 'file' as const,
  },
  {
    id: 'vocal-tuning',
    title: 'Vocal Tuning',
    description: 'Pitch correction and editing',
    defaultPrice: 50,
    proofType: 'file' as const,
  },
  {
    id: 'artwork',
    title: 'Album Artwork',
    description: 'Cover art design',
    defaultPrice: 100,
    proofType: 'file' as const,
  },
]

export default function MusicPage() {
  const [selected, setSelected] = useState<string | null>(null)
  const [price, setPrice] = useState<number>(0)
  const [customTitle, setCustomTitle] = useState('')

  const selectedTemplate = SERVICE_TEMPLATES.find(t => t.id === selected)

  const handleSelect = (template: typeof SERVICE_TEMPLATES[0]) => {
    setSelected(template.id)
    setPrice(template.defaultPrice)
    setCustomTitle(template.title)
  }

  const handleCreate = () => {
    if (!selectedTemplate) return
    // Navigate to create page with pre-filled data
    const params = new URLSearchParams({
      title: customTitle,
      amount: price.toString(),
      proof_type: selectedTemplate.proofType,
      description: selectedTemplate.description,
    })
    window.location.href = `/create?${params.toString()}`
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Minimal Header */}
      <header className="border-b-2 border-border">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-2 h-2 bg-forest" />
            <span className="text-sm font-medium tracking-wider uppercase">SYMIONE</span>
          </Link>
          <span className="text-sm text-muted">Music Services</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12">
        {/* One liner */}
        <div className="mb-10">
          <h1 className="text-2xl font-light mb-2">Create payment link</h1>
          <p className="text-muted">Select service. Set price. Share link. Get paid when you deliver.</p>
        </div>

        {/* Service Grid */}
        <div className="grid md:grid-cols-2 gap-4 mb-10">
          {SERVICE_TEMPLATES.map((template) => (
            <button
              key={template.id}
              onClick={() => handleSelect(template)}
              className={`p-6 text-left border-2 transition-all ${
                selected === template.id
                  ? 'border-forest bg-forest/5'
                  : 'border-border hover:border-foreground'
              }`}
            >
              <p className="text-lg font-medium mb-1">{template.title}</p>
              <p className="text-sm text-muted">{template.description}</p>
            </button>
          ))}
        </div>

        {/* Price Input - Shows when selected */}
        {selected && (
          <div className="border-2 border-foreground p-8 space-y-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted uppercase tracking-wider">Configure</span>
              <button
                onClick={() => setSelected(null)}
                className="text-sm text-muted hover:text-foreground"
              >
                Clear
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-muted mb-2">Service Title</label>
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
              className="w-full py-4 bg-forest text-white font-medium hover:bg-forest/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Create Payment Link
            </button>

            <p className="text-center text-sm text-muted">
              Client pays upfront. You deliver. Payment releases.
            </p>
          </div>
        )}

        {/* How it works - minimal */}
        {!selected && (
          <div className="border-t-2 border-border pt-10 mt-10">
            <div className="grid md:grid-cols-3 gap-8 text-center">
              <div>
                <span className="text-3xl font-light text-border">01</span>
                <p className="mt-2 text-sm">Select service & set price</p>
              </div>
              <div>
                <span className="text-3xl font-light text-border">02</span>
                <p className="mt-2 text-sm">Share link with client</p>
              </div>
              <div>
                <span className="text-3xl font-light text-border">03</span>
                <p className="mt-2 text-sm">Deliver work, get paid</p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Minimal Footer */}
      <footer className="border-t-2 border-border mt-auto">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between text-sm text-muted">
          <span>Powered by Stripe</span>
          <span>5% on successful payments</span>
        </div>
      </footer>
    </div>
  )
}
