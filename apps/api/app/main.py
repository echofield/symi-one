from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from src.agreements.router import router as agreements_router, public_router
from src.payments.router import router as payments_router, webhook_router
from src.submissions.router import router as submissions_router
from src.storage.router import router as storage_router
from src.reviews.router import router as reviews_router
from src.decisions.router import router as decisions_router
from src.executions.router import router as executions_router
from src.webhooks.router import router as outbound_webhooks_router
from src.internal.router import router as internal_router
from src.arbitration.router import router as arbitration_router

settings = get_settings()

app = FastAPI(
    title="SYMIONE PAY API",
    description=(
        "**Execution primitive (v1):** `POST /api/v1/executions` with `Idempotency-Key`; advance via "
        "`/fund`, `/proof`, `/retry`, `/cancel`. Responses include `status` and `next_action`.\n\n"
        "**Outbound webhooks:** register URLs at `POST /api/v1/webhooks/endpoints` (signed with "
        "`Symione-Signature`). **Reconciliation:** poll `GET /api/v1/executions/{id}` or consume "
        "`execution.updated` events.\n\n"
        "Legacy agreement-centric routes remain for the human UI."
    ),
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "symione-pay-api"}


# v1 execution primitive (API key auth)
app.include_router(executions_router, prefix="/api/v1/executions", tags=["executions-v1"])
app.include_router(outbound_webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks-outbound"])
app.include_router(arbitration_router, prefix="/api/v1", tags=["arbitration-disputes"])

# Internal bootstrap (admin token)
app.include_router(internal_router, prefix="/api/internal", tags=["internal"])

# Legacy / human UI routes
app.include_router(agreements_router, prefix="/api/agreements", tags=["internal-legacy-agreements"])
app.include_router(payments_router, prefix="/api/agreements", tags=["internal-legacy-payments"])
app.include_router(submissions_router, prefix="/api/agreements", tags=["internal-legacy-submissions"])
app.include_router(storage_router, prefix="/api/agreements", tags=["internal-legacy-storage"])
app.include_router(reviews_router, prefix="/api/admin/reviews", tags=["internal-legacy-reviews"])
app.include_router(decisions_router, prefix="/api/admin/decisions", tags=["internal-legacy-decisions"])

# Public routes
app.include_router(public_router, prefix="/api/public", tags=["public"])

# Stripe webhook (inbound)
app.include_router(webhook_router, prefix="/api/stripe", tags=["stripe-webhook-inbound"])
