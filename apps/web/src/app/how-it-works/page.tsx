'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

export default function HowItWorksPage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <>
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,400&family=Inter:wght@400;500&display=swap');

        .symi-page {
          --paper: #FAF8F2;
          --ink: #1A1A1A;
          --green: #1B4332;
          --warmgrey: #C9C5BC;
          --faint: #E8E5DE;
          font-family: 'Inter', system-ui, sans-serif;
        }

        .symi-page::before {
          content: "";
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          opacity: 0.025;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        }

        .font-serif {
          font-family: 'Cormorant Garamond', Georgia, serif;
        }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .animate-fade-up {
          animation: fadeUp 0.7s ease-out forwards;
        }

        .delay-1 { animation-delay: 0.1s; opacity: 0; }
        .delay-2 { animation-delay: 0.2s; opacity: 0; }
        .delay-3 { animation-delay: 0.3s; opacity: 0; }
      `}</style>

      <div className="symi-page min-h-screen flex flex-col" style={{ background: 'var(--paper)' }}>
        {/* Header */}
        <header style={{ borderBottom: '0.5px solid var(--faint)' }}>
          <div className="max-w-2xl mx-auto px-6 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 hover:opacity-70 transition-opacity">
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                <rect x="2" y="2" width="16" height="16" rx="2" stroke="var(--ink)" strokeWidth="1.5" fill="none"/>
                <path d="M6 10l3 3 5-6" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span className="text-[10px] font-medium tracking-[0.25em]" style={{ color: 'var(--ink)' }}>
                SYMIONE
              </span>
            </Link>

            <Link
              href="/music"
              className="text-[10px] font-medium tracking-[0.15em] transition-opacity hover:opacity-70"
              style={{ color: 'var(--green)' }}
            >
              CREATE PAYMENT
            </Link>
          </div>
        </header>

        {/* Main */}
        <main className="flex-1 px-6 py-16 relative z-10">
          <div className="max-w-2xl mx-auto">
            {mounted && (
              <>
                {/* Title */}
                <div className="mb-16 animate-fade-up">
                  <p
                    className="text-[9px] font-medium tracking-[0.2em] mb-4"
                    style={{ color: 'var(--green)', opacity: 0.7 }}
                  >
                    HOW IT WORKS
                  </p>
                  <h1
                    className="font-serif text-[36px] leading-[1.2] tracking-[-0.02em] mb-6"
                    style={{ color: 'var(--ink)' }}
                  >
                    Payment that executes on delivery
                  </h1>
                  <p
                    className="text-[15px] leading-relaxed"
                    style={{ color: 'var(--ink)', opacity: 0.5 }}
                  >
                    SYMIONE is a conditional payment layer. Money is locked when the client pays,
                    and released when you confirm the work is delivered.
                  </p>
                </div>

                {/* Steps */}
                <div className="space-y-12 animate-fade-up delay-1">
                  <Step
                    number="01"
                    title="Create a payment link"
                    description="Select your service type and set your price. You get a unique payment link to share with your client."
                  />
                  <Step
                    number="02"
                    title="Client pays upfront"
                    description="Your client clicks the link and pays via card. The money is securely held — not in your account yet, but guaranteed."
                  />
                  <Step
                    number="03"
                    title="Deliver your work"
                    description="Complete the work and deliver it however you normally would — WeTransfer, Dropbox, email, in person."
                  />
                  <Step
                    number="04"
                    title="Confirm & get paid"
                    description="Once delivered, confirm completion. Payment is released instantly to your bank account."
                  />
                </div>

                {/* Details */}
                <div className="mt-20 pt-12 animate-fade-up delay-2" style={{ borderTop: '0.5px solid var(--faint)' }}>
                  <h2
                    className="font-serif text-[24px] mb-8"
                    style={{ color: 'var(--ink)' }}
                  >
                    Details
                  </h2>

                  <div className="space-y-6">
                    <Detail
                      label="FEE"
                      content="5% on successful payments only. No subscription, no setup fees."
                    />
                    <Detail
                      label="PAYMENTS"
                      content="Powered by Stripe. All major cards accepted. Secure PCI-compliant processing."
                    />
                    <Detail
                      label="PAYOUTS"
                      content="Funds are transferred to your connected bank account within 2-7 business days."
                    />
                    <Detail
                      label="DISPUTES"
                      content="If there's a disagreement, both parties can request review. We mediate based on the original agreement."
                    />
                  </div>
                </div>

                {/* CTA */}
                <div className="mt-16 animate-fade-up delay-3">
                  <Link
                    href="/music"
                    className="inline-flex items-center gap-3 text-[12px] font-medium tracking-[0.15em] py-3 px-6 transition-opacity hover:opacity-80"
                    style={{ background: 'var(--green)', color: '#fff' }}
                  >
                    CREATE YOUR FIRST PAYMENT
                    <span>→</span>
                  </Link>
                </div>
              </>
            )}
          </div>
        </main>

        {/* Footer */}
        <footer style={{ borderTop: '0.5px solid var(--faint)' }}>
          <div className="max-w-2xl mx-auto px-6 py-6 flex items-center justify-between">
            <span
              className="text-[9px] tracking-[0.2em]"
              style={{ color: 'var(--ink)', opacity: 0.2 }}
            >
              SYMIONE · PARIS
            </span>
            <div className="flex items-center gap-4">
              <Link
                href="/legal"
                className="text-[9px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.25 }}
              >
                Legal
              </Link>
              <span style={{ color: 'var(--faint)' }}>·</span>
              <Link
                href="/privacy"
                className="text-[9px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.25 }}
              >
                Privacy
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}

function Step({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="flex gap-8">
      <span
        className="font-serif text-[32px] leading-none"
        style={{ color: 'var(--faint)' }}
      >
        {number}
      </span>
      <div>
        <h3
          className="font-serif text-[20px] mb-2"
          style={{ color: 'var(--ink)' }}
        >
          {title}
        </h3>
        <p
          className="text-[14px] leading-relaxed"
          style={{ color: 'var(--ink)', opacity: 0.45 }}
        >
          {description}
        </p>
      </div>
    </div>
  )
}

function Detail({ label, content }: { label: string; content: string }) {
  return (
    <div className="flex flex-col sm:flex-row sm:gap-8">
      <span
        className="text-[9px] font-medium tracking-[0.2em] mb-1 sm:mb-0 sm:w-24 flex-shrink-0"
        style={{ color: 'var(--ink)', opacity: 0.3 }}
      >
        {label}
      </span>
      <p
        className="text-[14px] leading-relaxed"
        style={{ color: 'var(--ink)', opacity: 0.6 }}
      >
        {content}
      </p>
    </div>
  )
}
