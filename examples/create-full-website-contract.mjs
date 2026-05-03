#!/usr/bin/env node
import { randomUUID } from "node:crypto";
import symioneSdk from "symione-sdk";

const { Symione, buildWebsiteContractExecution } = symioneSdk;

const env = process.env;
const dryRun = process.argv.includes("--dry-run");

function readList(value) {
  return (value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function readInteger(name, fallback, min, max) {
  const raw = env[name];
  if (!raw) return fallback;

  const parsed = Number.parseInt(raw, 10);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    throw new Error(`${name} must be an integer between ${min} and ${max}.`);
  }

  return parsed;
}

function readContractInput() {
  const projectName = env.WEBSITE_CONTRACT_PROJECT_NAME ?? "Full website delivery";
  const amount = env.WEBSITE_CONTRACT_AMOUNT ?? (dryRun ? "5000.00" : undefined);
  const currency = env.WEBSITE_CONTRACT_CURRENCY ?? "eur";
  const deadlineAt = env.WEBSITE_CONTRACT_DEADLINE_AT;
  const allowedDomains = readList(env.WEBSITE_CONTRACT_ALLOWED_DOMAINS);
  const minLighthouseScore = readInteger("WEBSITE_CONTRACT_MIN_LIGHTHOUSE", 85, 0, 100);
  const validationTier = env.WEBSITE_CONTRACT_VALIDATION_TIER ?? "premium";

  if (!amount) {
    throw new Error("Set WEBSITE_CONTRACT_AMOUNT before creating a live contract.");
  }

  const validationBrief =
    env.WEBSITE_CONTRACT_VALIDATION_BRIEF ??
    [
      "Validate the submitted URL as a complete production website, not a placeholder.",
      "Required: polished homepage, clear navigation, responsive mobile and desktop layout, real project content, contact or conversion path, SEO title and meta description, and no visible build/runtime errors.",
      "Core sections or pages should cover the offer or services, proof/about content, and contact details.",
      "Reject blank pages, starter templates, password-gated pages, broken primary navigation, or materially incomplete delivery.",
    ].join(" ");

  return {
    title: projectName,
    amount,
    currency,
    payerEmail: env.WEBSITE_CONTRACT_PAYER_EMAIL,
    payeeEmail: env.WEBSITE_CONTRACT_PAYEE_EMAIL,
    deadlineAt,
    allowedDomains,
    minLighthouseScore,
    validationTier,
    validationBrief,
  };
}

async function main() {
  const contractInput = readContractInput();
  const executionInput = buildWebsiteContractExecution(contractInput);
  const baseUrl = env.SYMIONE_API_BASE_URL ?? env.SYMIONE_BASE_URL ?? "http://localhost:8000";
  const idempotencyKey = env.WEBSITE_CONTRACT_IDEMPOTENCY_KEY ?? `website-contract-${randomUUID()}`;

  if (dryRun) {
    console.log(
      JSON.stringify(
        {
          mode: "dry-run",
          base_url: baseUrl,
          idempotency_key: idempotencyKey,
          contract_input: contractInput,
          create_execution_body: executionInput,
        },
        null,
        2
      )
    );
    return;
  }

  if (!env.SYMIONE_API_KEY) {
    throw new Error("Set SYMIONE_API_KEY before creating a live contract.");
  }

  const client = new Symione({
    baseUrl,
    apiKey: env.SYMIONE_API_KEY,
  });

  const execution = await client.contracts.website.create(contractInput, idempotencyKey);
  console.log(
    JSON.stringify(
      {
        execution,
        idempotency_key: idempotencyKey,
        next_step: "Fund the execution through the SYMIONE fund endpoint or web UI before submitting the final website URL as proof.",
      },
      null,
      2
    )
  );
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
