'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

export default function LegalPage() {
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
              <div className="animate-fade-up">
                {/* Title */}
                <div className="mb-12">
                  <p
                    className="text-[9px] font-medium tracking-[0.2em] mb-4"
                    style={{ color: 'var(--green)', opacity: 0.7 }}
                  >
                    TERMS OF SERVICE
                  </p>
                  <h1
                    className="font-serif text-[36px] leading-[1.2] tracking-[-0.02em] mb-4"
                    style={{ color: 'var(--ink)' }}
                  >
                    Legal terms
                  </h1>
                  <p
                    className="text-[13px]"
                    style={{ color: 'var(--ink)', opacity: 0.4 }}
                  >
                    Last updated: March 2026
                  </p>
                </div>

                {/* Content */}
                <div className="space-y-10">
                  <Section title="Service overview">
                    <p>
                      SYMIONE provides a conditional payment service that allows service providers ("Creators")
                      to create payment links for their clients ("Payers"). Payments are held securely and
                      released upon confirmation of service delivery.
                    </p>
                  </Section>

                  <Section title="How it works">
                    <p>
                      When a Creator sets up a payment link, they define the service and price. When a Payer
                      completes payment, funds are authorized but not captured. Upon the Creator confirming
                      delivery, the payment is captured and transferred to the Creator's account, minus the
                      platform fee.
                    </p>
                  </Section>

                  <Section title="Fees">
                    <p>
                      SYMIONE charges a 5% fee on successful transactions. This fee is deducted from the
                      payment amount before transfer to the Creator. There are no subscription fees, setup
                      fees, or fees for failed transactions.
                    </p>
                  </Section>

                  <Section title="Payment processing">
                    <p>
                      All payments are processed by Stripe. By using SYMIONE, you agree to Stripe's
                      Terms of Service and Privacy Policy. SYMIONE is not a bank and does not hold funds
                      directly — all funds are held by Stripe until release conditions are met.
                    </p>
                  </Section>

                  <Section title="Creator responsibilities">
                    <p>As a Creator, you agree to:</p>
                    <ul className="list-disc pl-5 mt-3 space-y-2">
                      <li>Provide accurate descriptions of your services</li>
                      <li>Deliver services as described in the agreement</li>
                      <li>Only confirm delivery when work has been genuinely completed</li>
                      <li>Respond to disputes in good faith</li>
                      <li>Comply with all applicable laws and regulations</li>
                    </ul>
                  </Section>

                  <Section title="Payer rights">
                    <p>As a Payer, you have the right to:</p>
                    <ul className="list-disc pl-5 mt-3 space-y-2">
                      <li>Receive the service as described in the agreement</li>
                      <li>Dispute a payment if services were not delivered as agreed</li>
                      <li>Request a refund if the Creator fails to deliver</li>
                    </ul>
                  </Section>

                  <Section title="Disputes">
                    <p>
                      If a dispute arises between Creator and Payer, both parties may request review.
                      SYMIONE will review the original agreement and any evidence provided. We reserve
                      the right to refund the Payer or release funds to the Creator based on our assessment.
                      Our decision is final.
                    </p>
                  </Section>

                  <Section title="Prohibited use">
                    <p>You may not use SYMIONE for:</p>
                    <ul className="list-disc pl-5 mt-3 space-y-2">
                      <li>Illegal goods or services</li>
                      <li>Fraudulent transactions</li>
                      <li>Money laundering</li>
                      <li>Any activity that violates Stripe's acceptable use policy</li>
                    </ul>
                  </Section>

                  <Section title="Limitation of liability">
                    <p>
                      SYMIONE provides the platform "as is" and makes no warranties regarding the outcome
                      of any transaction. We are not responsible for the quality of services provided by
                      Creators or disputes between parties. Our maximum liability is limited to the fees
                      collected on the disputed transaction.
                    </p>
                  </Section>

                  <Section title="Termination">
                    <p>
                      We reserve the right to suspend or terminate accounts that violate these terms,
                      engage in fraudulent activity, or pose a risk to our platform or users.
                    </p>
                  </Section>

                  <Section title="Changes to terms">
                    <p>
                      We may update these terms from time to time. Continued use of the service after
                      changes constitutes acceptance of the new terms.
                    </p>
                  </Section>

                  <Section title="Governing law">
                    <p>
                      These terms are governed by French law. Any disputes shall be resolved in the
                      courts of Paris, France.
                    </p>
                  </Section>

                  <Section title="Contact">
                    <p>
                      For legal inquiries:{' '}
                      <a
                        href="mailto:legal@symione.com"
                        className="transition-opacity hover:opacity-60"
                        style={{ color: 'var(--green)' }}
                      >
                        legal@symione.com
                      </a>
                    </p>
                  </Section>
                </div>

                {/* Company info */}
                <div className="mt-16 pt-8" style={{ borderTop: '0.5px solid var(--faint)' }}>
                  <p
                    className="text-[9px] font-medium tracking-[0.2em] mb-4"
                    style={{ color: 'var(--ink)', opacity: 0.3 }}
                  >
                    COMPANY INFORMATION
                  </p>
                  <div
                    className="text-[13px] leading-relaxed space-y-1"
                    style={{ color: 'var(--ink)', opacity: 0.45 }}
                  >
                    <p>SYMIONE SAS</p>
                    <p>Paris, France</p>
                    <p>contact@symione.com</p>
                  </div>
                </div>
              </div>
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
                href="/privacy"
                className="text-[9px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.25 }}
              >
                Privacy
              </Link>
              <span style={{ color: 'var(--faint)' }}>·</span>
              <Link
                href="/how-it-works"
                className="text-[9px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.25 }}
              >
                How it works
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="pt-8" style={{ borderTop: '0.5px solid var(--faint)' }}>
      <h2
        className="font-serif text-[20px] mb-4"
        style={{ color: 'var(--ink)' }}
      >
        {title}
      </h2>
      <div
        className="text-[14px] leading-relaxed"
        style={{ color: 'var(--ink)', opacity: 0.55 }}
      >
        {children}
      </div>
    </div>
  )
}
