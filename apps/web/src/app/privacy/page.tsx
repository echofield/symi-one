'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

export default function PrivacyPage() {
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
                    PRIVACY POLICY
                  </p>
                  <h1
                    className="font-serif text-[36px] leading-[1.2] tracking-[-0.02em] mb-4"
                    style={{ color: 'var(--ink)' }}
                  >
                    Your data, protected
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
                  <Section title="What we collect">
                    <p>When you use SYMIONE, we collect:</p>
                    <ul className="list-disc pl-5 mt-3 space-y-2">
                      <li>Email address (to send payment links and confirmations)</li>
                      <li>Payment information (processed securely by Stripe — we never see your card details)</li>
                      <li>Service descriptions and amounts (to create your payment agreements)</li>
                      <li>Basic usage data (to improve the service)</li>
                    </ul>
                  </Section>

                  <Section title="How we use it">
                    <p>Your data is used to:</p>
                    <ul className="list-disc pl-5 mt-3 space-y-2">
                      <li>Process payments and transfers</li>
                      <li>Send transaction notifications</li>
                      <li>Provide customer support</li>
                      <li>Improve our service</li>
                    </ul>
                    <p className="mt-4">We do not sell your data. We do not use it for advertising.</p>
                  </Section>

                  <Section title="Payment security">
                    <p>
                      All payment processing is handled by Stripe, a PCI-DSS Level 1 certified payment processor.
                      Your card information never touches our servers. Stripe's security practices are among the
                      most rigorous in the industry.
                    </p>
                  </Section>

                  <Section title="Data retention">
                    <p>
                      We retain transaction records for 7 years as required by financial regulations.
                      You can request deletion of your account and personal data at any time by contacting us.
                    </p>
                  </Section>

                  <Section title="Cookies">
                    <p>
                      We use essential cookies only — no tracking, no analytics cookies, no third-party advertising.
                      Just what's needed to keep you logged in and process payments.
                    </p>
                  </Section>

                  <Section title="Your rights">
                    <p>Under GDPR and similar regulations, you have the right to:</p>
                    <ul className="list-disc pl-5 mt-3 space-y-2">
                      <li>Access your personal data</li>
                      <li>Correct inaccurate data</li>
                      <li>Request deletion of your data</li>
                      <li>Export your data</li>
                      <li>Object to processing</li>
                    </ul>
                  </Section>

                  <Section title="Contact">
                    <p>
                      For privacy-related inquiries:{' '}
                      <a
                        href="mailto:privacy@symione.com"
                        className="transition-opacity hover:opacity-60"
                        style={{ color: 'var(--green)' }}
                      >
                        privacy@symione.com
                      </a>
                    </p>
                  </Section>
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
                href="/legal"
                className="text-[9px] tracking-[0.1em] transition-opacity hover:opacity-60"
                style={{ color: 'var(--ink)', opacity: 0.25 }}
              >
                Legal
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
