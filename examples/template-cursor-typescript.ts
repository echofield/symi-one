/**
 * Drop-in pattern for Cursor / Claude / Node agents using symione-sdk.
 * Set SYMIONE_BASE_URL and SYMIONE_API_KEY in the environment.
 */
import { Symione } from "symione-sdk";

const client = new Symione({
  baseUrl: process.env.SYMIONE_BASE_URL ?? "http://localhost:8000",
  apiKey: process.env.SYMIONE_API_KEY!,
});

const run = async () => {
  const idem = `task-${Date.now()}`;
  const ex = await client.createExecution(
    {
      title: "Agent task",
      description: "Pay on proof",
      amount: "100.00",
      currency: "usd",
      proof_type: "url",
      validation_config: { require_status_200: true },
    },
    idem
  );
  const latest = await client.getExecution(ex.execution_id);
  console.log(latest.status, latest.next_action);
};

void run();
