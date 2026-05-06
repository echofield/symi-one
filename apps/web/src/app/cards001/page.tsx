'use client'

import { useMemo, useState } from 'react'

type Mode = 'read' | 'build'

type Agreement = {
  builder: string
  deliverable: string
  deadline: string
  amount: string
  proof: string
}

const emptyAgreement: Agreement = {
  builder: '',
  deliverable: '',
  deadline: '',
  amount: '',
  proof: '',
}

const nextCards = [
  ['002', 'Sponsor an Essay Series'],
  ['003', 'Sponsor an Open-Source Tool'],
  ['004', 'Verify a Public Artifact'],
  ['005', 'Resolve a Disputed Delivery'],
]

const artifactLinks = [
  ['intent-card.json', '/cards001/intent-card.json'],
  ['agent.manifest.json', '/cards001/agent.manifest.json'],
  ['symione.contract.template.json', '/cards001/symione.contract.template.json'],
  ['proof.schema.json', '/cards001/proof.schema.json'],
  ['links.json', '/cards001/links.json'],
]

function buildExecutionPayload(rawBrief: string) {
  return {
    contract_kind: 'sponsor_funded_output',
    intent_card_id: 'sponsor-public-build',
    intent_card_version: '0.1.0',
    raw_brief: rawBrief,
    sponsor: '<sponsor id>',
    builder: '<parsed builder>',
    deliverable: '<parsed public deliverable>',
    acceptance_criteria: [
      'public URL exists',
      'artifact matches agreed deliverable',
      'artifact is delivered before the deadline',
    ],
    deadline: '<parsed ISO 8601 deadline>',
    amount: { value: '<parsed amount>', currency: 'EUR' },
    proof_schema: 'public_artifact_v1',
    settlement: 'pay_on_valid_proof',
    payment_rail: 'stripe_service_payment',
    executor_agent: 'sponsor-compose-agent',
    verifier_agent: 'public-artifact-verifier',
    next_cards: ['sponsor-essay-series', 'sponsor-open-source-tool', 'verify-public-artifact'],
    created_at: new Date().toISOString(),
    signature: 'ed25519:<pending>',
  }
}

export default function Cards001Page() {
  const [mode, setMode] = useState<Mode>('read')
  const [agreement, setAgreement] = useState<Agreement>(emptyAgreement)
  const [showSummary, setShowSummary] = useState(false)
  const [rawBrief, setRawBrief] = useState('')
  const [showPayload, setShowPayload] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)

  const payload = useMemo(() => buildExecutionPayload(rawBrief), [rawBrief])

  function updateAgreement(field: keyof Agreement, value: string) {
    setAgreement((current) => ({ ...current, [field]: value }))
    setShowSummary(false)
  }

  function loadReadExample() {
    setAgreement({
      builder: 'Lila Moreau',
      deliverable:
        'A 7-essay series on attention economics, one essay per week, each over 1,500 words, published on her public blog.',
      deadline: 'June 24, 2026',
      amount: '300',
      proof:
        'Seven public essays exist at lilamoreau.com/essays, each dated, each over 1,500 words.',
    })
    setShowSummary(false)
  }

  function composeAgreement() {
    const allFields = Object.values(agreement).every((value) => value.trim().length > 0)
    if (!allFields) {
      window.alert('Fill in every field. Vague briefs become disputed deliveries.')
      return
    }
    setShowSummary(true)
  }

  function loadBuildExample() {
    setRawBrief(
      'I will fund Lila Moreau 300 EUR to ship a 7-essay series on attention economics by June 24, 2026. Proof = seven essays public on her blog, each over 1,500 words.'
    )
    setShowPayload(false)
  }

  function generatePayload() {
    if (!rawBrief.trim()) {
      window.alert('Type a brief first, or load the example.')
      return
    }
    setShowPayload(true)
  }

  async function copyText(label: string, text: string) {
    await navigator.clipboard.writeText(text)
    setCopied(label)
    window.setTimeout(() => setCopied(null), 1400)
  }

  return (
    <main className="min-h-screen bg-[#f8f8f4] text-[#111111]">
      <div className="mx-auto max-w-[780px] px-6 py-10 sm:px-10 lg:px-14">
        <header className="grid grid-cols-[1fr_auto_1fr] items-center border-b border-[#d6d6ce] pb-4 text-[10px] uppercase text-[#6f6f68]">
          <div>SYMIONE / PROTOCOL</div>
          <div className="font-serif text-sm normal-case text-[#111111]">Intent Card</div>
          <div className="text-right">001 / V0.1</div>
        </header>

        <div className="mt-8 flex justify-center">
          <div className="inline-flex border border-[#c9c9bf]">
            <button
              type="button"
              onClick={() => setMode('read')}
              className={`px-5 py-2 text-[11px] uppercase transition-colors ${
                mode === 'read'
                  ? 'bg-[#111111] text-[#f8f8f4]'
                  : 'bg-transparent text-[#66665f] hover:bg-[#eeeeE7]'
              }`}
            >
              Read
            </button>
            <button
              type="button"
              onClick={() => setMode('build')}
              className={`border-l border-[#c9c9bf] px-5 py-2 text-[11px] uppercase transition-colors ${
                mode === 'build'
                  ? 'bg-[#111111] text-[#f8f8f4]'
                  : 'bg-transparent text-[#66665f] hover:bg-[#eeeeE7]'
              }`}
            >
              Build
            </button>
          </div>
        </div>

        <section className="py-10 text-center">
          <div className="mx-auto mb-7 grid h-20 w-20 place-items-center rounded-full border border-[#7f261a] bg-white">
            <div className="text-center text-[#7f261a]">
              <div className="font-serif text-2xl italic leading-none">S</div>
              <div className="mt-1 text-[9px]">001</div>
            </div>
          </div>

          <p className="mb-5 text-[11px] uppercase text-[#7f261a]">Sponsorship / Public Build</p>
          <h1 className="font-serif text-5xl font-normal leading-none text-[#111111] sm:text-6xl">
            Sponsor a <span className="italic text-[#7f261a]">Public</span> Build
          </h1>
          <p className="mx-auto mt-5 max-w-[560px] font-serif text-xl italic leading-snug text-[#303029]">
            Commission work that ships in public. Payment resolves when the artifact exists and the proof matches the agreement.
          </p>
        </section>

        <section className="border-y border-[#d6d6ce] py-6 text-center">
          <p className="mx-auto max-w-[520px] font-serif text-lg leading-relaxed">
            Intent Cards <span className="italic text-[#7f261a]">define</span> the work.
            <br />
            Agents <span className="italic text-[#7f261a]">perform</span> the work.
            <br />
            SYMIONE <span className="italic text-[#7f261a]">makes</span> the work payable.
          </p>
        </section>

        {mode === 'read' ? (
          <>
            <CardSection number="01" title="What this card does">
              <p className="section-copy">
                You want to see something exist: an essay series, an open-source tool, a research note, a useful agent.
                This card turns that intent into a clean service order with proof-based settlement.
              </p>

              <div className="mt-6 overflow-hidden border border-[#d6d6ce] bg-white">
                {[
                  ['You', 'name what you want to fund'],
                  ['The builder', 'commits to deliver it by a date'],
                  ['The payment', 'is tied to a defined service order'],
                  ['The work ships', 'the builder is paid on valid proof'],
                  ['It misses', 'the agreement moves to refund, rework, or dispute'],
                ].map(([label, value]) => (
                  <div key={label} className="grid grid-cols-[140px_1fr] border-b border-[#d6d6ce] last:border-b-0">
                    <div className="flex items-center border-r border-[#d6d6ce] bg-[#eeeeE7] px-4 py-4 text-[11px] uppercase text-[#6f6f68]">
                      {label}
                    </div>
                    <div className="flex items-center px-5 py-4 font-serif text-lg">{value}</div>
                  </div>
                ))}
              </div>

              <p className="mt-4 font-serif text-sm italic text-[#66665f]">
                This is service commerce, not a contest. You are paying for a public output that can be verified.
              </p>
            </CardSection>

            <CardSection number="02" title="What people sponsor">
              <Example
                label="Writing"
                text="Fund a 7-essay series on attention economics, one essay per week, each over 1,500 words, on a public blog."
              />
              <Example
                label="Open Source"
                text="Fund an MIT-licensed CLI tool for PDF table extraction, with a public repository and passing tests."
              />
              <Example
                label="Agents"
                text="Fund a public agent build: manifest, execution template, proof schema, and demo run published by a fixed date."
              />
            </CardSection>

            <CardSection number="03" title="Compose your sponsorship">
              <p className="section-copy">
                Fill in the service order. The card produces a plain-language agreement that can later become a SYMIONE execution.
              </p>

              <div className="mt-5 space-y-4">
                <Field label="Who you are funding">
                  <input
                    value={agreement.builder}
                    onChange={(event) => updateAgreement('builder', event.target.value)}
                    className="card-input"
                    placeholder="Their name or handle"
                  />
                </Field>
                <Field label="What they will ship">
                  <textarea
                    value={agreement.deliverable}
                    onChange={(event) => updateAgreement('deliverable', event.target.value)}
                    className="card-input min-h-[110px]"
                    placeholder="The public artifact that must exist when the work is done."
                  />
                </Field>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="By when">
                    <input
                      value={agreement.deadline}
                      onChange={(event) => updateAgreement('deadline', event.target.value)}
                      className="card-input"
                      placeholder="June 24, 2026"
                    />
                  </Field>
                  <Field label="Amount EUR">
                    <input
                      value={agreement.amount}
                      onChange={(event) => updateAgreement('amount', event.target.value)}
                      className="card-input"
                      placeholder="300"
                      inputMode="decimal"
                    />
                  </Field>
                </div>
                <Field label="Proof of delivery">
                  <textarea
                    value={agreement.proof}
                    onChange={(event) => updateAgreement('proof', event.target.value)}
                    className="card-input min-h-[110px]"
                    placeholder="What URL, repository, or artifact proves the work shipped?"
                  />
                </Field>
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" onClick={composeAgreement} className="card-button">
                  Compose Agreement
                </button>
                <button type="button" onClick={loadReadExample} className="card-button card-button-ghost">
                  Load Example
                </button>
              </div>

              {showSummary ? (
                <div className="mt-7 border border-[#7f261a] bg-white p-6">
                  <p className="mb-5 font-serif text-2xl leading-snug">
                    You will fund <span className="italic text-[#7f261a]">{agreement.builder}</span> EUR {agreement.amount} to ship
                    a public artifact by <span className="italic text-[#7f261a]">{agreement.deadline}</span>.
                  </p>
                  <SummaryRow label="Builder" value={agreement.builder} />
                  <SummaryRow label="Deliverable" value={agreement.deliverable} />
                  <SummaryRow label="Deadline" value={agreement.deadline} />
                  <SummaryRow label="Amount" value={`EUR ${agreement.amount}`} />
                  <SummaryRow label="Proof rule" value={agreement.proof} />
                  <SummaryRow label="Settlement" value="Pay on valid proof. Refund, rework, or dispute on miss." />
                  <div className="mt-5 flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={() =>
                        copyText(
                          'agreement',
                          `Sponsor Public Build\nBuilder: ${agreement.builder}\nDeliverable: ${agreement.deliverable}\nDeadline: ${agreement.deadline}\nAmount: EUR ${agreement.amount}\nProof: ${agreement.proof}\nSettlement: Pay on valid proof. Refund, rework, or dispute on miss.`
                        )
                      }
                      className="card-button"
                    >
                      {copied === 'agreement' ? 'Copied' : 'Copy Agreement'}
                    </button>
                    <button type="button" onClick={() => setShowSummary(false)} className="card-button card-button-ghost">
                      Edit
                    </button>
                  </div>
                </div>
              ) : null}
            </CardSection>
          </>
        ) : (
          <>
            <CardSection number="01" title="The intent">
              <p className="section-copy">
                A sponsorship is a service-commerce contract in which a sponsor commissions a public deliverable. Settlement is
                conditional on proof that the artifact exists and matches the agreement.
              </p>

              <div className="mt-5">
                <Field label="Raw intent">
                  <textarea
                    value={rawBrief}
                    onChange={(event) => {
                      setRawBrief(event.target.value)
                      setShowPayload(false)
                    }}
                    className="card-input min-h-[130px] font-mono text-sm"
                    placeholder="I will fund [builder] [amount] EUR to ship [deliverable] by [deadline]. Proof = [public artifact]."
                  />
                </Field>
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" onClick={generatePayload} className="card-button">
                  Generate Payload
                </button>
                <button type="button" onClick={loadBuildExample} className="card-button card-button-ghost">
                  Load Example
                </button>
              </div>
            </CardSection>

            <CardSection number="02" title="The structure">
              <p className="section-copy">
                The card is portable. The public page is only one surface; the contract template and agent manifest are plain JSON.
              </p>

              <CodePanel
                label="contract.template.json"
                code={`{
  "contract_kind": "sponsor_funded_output",
  "intent_card_id": "sponsor-public-build",
  "acceptance_criteria": [
    "public URL exists",
    "artifact matches deliverable",
    "delivered before deadline"
  ],
  "proof_schema": "public_artifact_v1",
  "settlement": "pay_on_valid_proof",
  "executor_agent": "sponsor-compose-agent",
  "verifier_agent": "public-artifact-verifier"
}`}
              />

              {showPayload ? (
                <div className="mt-6">
                  <CodePanel label="symione.execution.payload" code={JSON.stringify(payload, null, 2)} />
                  <button
                    type="button"
                    onClick={() => copyText('payload', JSON.stringify(payload, null, 2))}
                    className="card-button mt-4"
                  >
                    {copied === 'payload' ? 'Copied' : 'Copy Payload'}
                  </button>
                </div>
              ) : null}
            </CardSection>

            <CardSection number="03" title="Protocol artifacts">
              <div className="grid gap-3">
                {artifactLinks.map(([name, href]) => (
                  <a
                    key={name}
                    href={href}
                    className="flex items-center justify-between border border-[#d6d6ce] bg-white px-4 py-3 text-sm transition-colors hover:border-[#7f261a]"
                  >
                    <span className="font-mono">{name}</span>
                    <span className="text-[#6f6f68]">open</span>
                  </a>
                ))}
              </div>
            </CardSection>
          </>
        )}

        <CardSection number={mode === 'read' ? '04' : '04'} title="What happens, in order">
          <ol className="space-y-0">
            {[
              ['The agreement is composed', 'The sponsor names the builder, deliverable, deadline, amount, and proof rule.'],
              ['The payment is authorized', 'The service order is funded through a compliant payment rail for service commerce.'],
              ['The builder ships', 'The builder publishes the artifact at the agreed public location.'],
              ['Proof is checked', 'The artifact is verified against the agreement and proof schema.'],
              ['Settlement resolves', 'On valid proof, the builder is paid. On a miss, the flow moves to refund, rework, or dispute.'],
            ].map(([title, body], index) => (
              <li key={title} className="grid grid-cols-[34px_1fr] gap-4 border-b border-[#d6d6ce] py-4 last:border-b-0">
                <div className="pt-1 font-mono text-xs text-[#7f261a]">{String(index + 1).padStart(2, '0')}</div>
                <div>
                  <div className="font-serif text-lg">{title}</div>
                  <p className="mt-1 text-sm leading-relaxed text-[#44443e]">{body}</p>
                </div>
              </li>
            ))}
          </ol>
        </CardSection>

        <CardSection number={mode === 'read' ? '05' : '05'} title="The card">
          <div className="grid gap-5 sm:grid-cols-2">
            <Meta label="Identifier" value="sponsor-public-build" />
            <Meta label="Version" value="0.1.0" />
            <Meta label="Contract kind" value="sponsor_funded_output" />
            <Meta label="Settlement" value="pay_on_valid_proof" />
            <Meta label="Use this card if" value="You want to fund work that ships in public" />
            <Meta label="Do not use it for" value="Bets, contests, stake pools, or wagering" />
          </div>
        </CardSection>

        <CardSection number={mode === 'read' ? '06' : '06'} title="The series">
          <p className="section-copy">
            Each card links to the next one. Together they form a complete economy for funding public work.
          </p>
          <div className="mt-5 grid gap-3">
            {nextCards.map(([number, name]) => (
              <a
                href="#"
                key={number}
                className="grid grid-cols-[48px_1fr_auto] items-center gap-4 border border-[#d6d6ce] bg-white px-5 py-4 text-[#111111] transition-transform hover:translate-x-0.5 hover:border-[#7f261a]"
              >
                <span className="font-mono text-xs text-[#7f261a]">{number}</span>
                <span className="font-serif text-lg">{name}</span>
                <span className="text-[#6f6f68]">next</span>
              </a>
            ))}
          </div>
        </CardSection>

        <footer className="mt-16 border-t border-[#d6d6ce] pt-8 text-center">
          <p className="font-serif text-sm italic leading-relaxed text-[#66665f]">
            The first card in a series of executable workflows.
            <br />
            Each one defines work. Each one is payable. Each one links to the next.
          </p>
          <div className="mt-4 text-[10px] uppercase text-[#6f6f68]">SYMIONE / INTENT / 001</div>
        </footer>
      </div>

      <style jsx global>{`
        .section-copy {
          font-size: 1rem;
          line-height: 1.75;
          color: #44443e;
        }

        .card-input {
          width: 100%;
          border: 1px solid #c9c9bf;
          background: #ffffff;
          padding: 0.9rem 1rem;
          color: #111111;
          outline: none;
          transition: border-color 0.15s ease;
        }

        .card-input:focus {
          border-color: #7f261a;
        }

        .card-input::placeholder {
          color: #82827b;
        }

        .card-button {
          background: #111111;
          color: #f8f8f4;
          border: 1px solid #111111;
          padding: 0.75rem 1.1rem;
          font-size: 0.72rem;
          text-transform: uppercase;
          transition: background-color 0.15s ease, border-color 0.15s ease;
        }

        .card-button:hover {
          background: #7f261a;
          border-color: #7f261a;
        }

        .card-button-ghost {
          background: transparent;
          color: #111111;
          border-color: #c9c9bf;
        }

        .card-button-ghost:hover {
          background: #eeeeE7;
          color: #111111;
          border-color: #111111;
        }
      `}</style>
    </main>
  )
}

function CardSection({
  number,
  title,
  children,
}: {
  number: string
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="mt-12">
      <div className="mb-5 flex items-baseline gap-4 border-b border-[#d6d6ce] pb-3">
        <div className="font-mono text-xs text-[#6f6f68]">S {number}</div>
        <h2 className="font-serif text-2xl font-medium">{title}</h2>
      </div>
      {children}
    </section>
  )
}

function Example({ label, text }: { label: string; text: string }) {
  return (
    <div className="mt-4 border-l-4 border-[#8a6f36] bg-white px-5 py-4">
      <div className="mb-2 text-[10px] uppercase text-[#8a6f36]">{label}</div>
      <p className="font-serif text-lg italic leading-relaxed text-[#303029]">{text}</p>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-2 block text-[10px] uppercase text-[#6f6f68]">{label}</span>
      {children}
    </label>
  )
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-2 border-b border-dashed border-[#d6d6ce] py-3 sm:grid-cols-[140px_1fr]">
      <div className="text-[10px] uppercase text-[#6f6f68]">{label}</div>
      <div className="font-serif text-lg">{value}</div>
    </div>
  )
}

function CodePanel({ label, code }: { label: string; code: string }) {
  return (
    <div className="border border-[#d6d6ce] bg-[#eeeeE7] p-5">
      <div className="mb-3 text-[10px] uppercase text-[#6f6f68]">{label}</div>
      <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-relaxed text-[#303029]">{code}</pre>
    </div>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mb-1 text-[10px] uppercase text-[#6f6f68]">{label}</div>
      <div className="font-serif text-lg">{value}</div>
    </div>
  )
}
