/**
 * Thin operator/debug surface: the product primitive is the v1 execution API.
 * Human flows remain under /create, /a/[token], /submit/[token].
 */
export default function DebugPage() {
  return (
    <main className="mx-auto max-w-lg p-8 font-sans text-sm text-zinc-200">
      <h1 className="mb-2 text-lg font-semibold text-white">Operator / debug</h1>
      <p className="mb-4 text-zinc-400">
        Integrations should use the execution API:{" "}
        <code className="rounded bg-zinc-800 px-1 py-0.5">POST /api/v1/executions</code> with an API key
        and <code className="rounded bg-zinc-800 px-1 py-0.5">Idempotency-Key</code>. See{" "}
        <code className="rounded bg-zinc-800 px-1 py-0.5">apps/api/docs/AGENT_API.md</code> and OpenAPI
        at the API root.
      </p>
      <ul className="list-inside list-disc space-y-1 text-zinc-400">
        <li>
          <a href="/create" className="text-emerald-400 underline">
            Create agreement (human)
          </a>
        </li>
        <li>
          <a href="/admin" className="text-emerald-400 underline">
            Admin reviews
          </a>
        </li>
      </ul>
    </main>
  );
}
