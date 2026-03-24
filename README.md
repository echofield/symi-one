# SYMIONE

Conditional payment protocol. Release payments when conditions are true.

## Products

### Reliable (apps/web/)
Stake-based challenges. Put your money where your mouth is.
- **Solo** — Challenge yourself with real stakes
- **Duel** — 1v1 challenges with a friend
- **Cell** — Group challenges

### Template Marketplace (/templates)
Fork and deploy conditional payment apps in 90 seconds.
- **Reliable** — Free, peer challenges
- **Escrow** — Free, freelancer payments
- **Accord** — Free, bilateral agreements
- **Creator Pro** — €149, challenge business for creators

## Structure

```
apps/
├── api/                    # Backend (FastAPI, Cloud Run)
│   ├── src/challenges/     # Challenge creation, proof, resolution
│   ├── src/connect/        # Stripe Connect Express accounts
│   ├── src/templates/      # Template marketplace
│   ├── src/executions/     # Core execution primitive
│   └── src/arbitration/    # Dispute resolution
│
└── web/                    # Frontend (Next.js, Vercel)
    └── src/app/
        ├── challenge/      # Reliable challenge UI
        ├── templates/      # Template marketplace
        └── connect/        # Stripe onboarding

packages/
├── intent-core/            # Intent schema, signing, canonicalization
├── intent-eval/            # JSONLogic evaluator, validators
├── sdk-js/                 # JavaScript SDK
└── sdk-python/             # Python SDK
```

## Protocol Economics

| Fee | Rate | Visibility |
|-----|------|------------|
| Platform fee | 10% | Visible to users |
| Protocol fee | 5% | Invisible (infrastructure) |
| **Total** | **15%** | |

The 5% protocol fee is non-negotiable and baked into every transfer.
The 10% platform fee is configurable (for creator rev-share in future).

## Deploy

### Backend (Cloud Run)
```bash
cd apps/api
gcloud run deploy symione-api --source .
```

### Frontend (Vercel)
1. Import repo from github.com/echofield/symii
2. Set "Root Directory" to: `apps/web`
3. Framework preset: Next.js
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`

## Environment

See `.env.example` for all required variables.

## Quick Start

```bash
# Backend
cd apps/api
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # configure
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd apps/web
npm install
cp .env.example .env.local  # configure
npm run dev
```

## API

### Challenges
| Action | Endpoint |
|--------|----------|
| Create | `POST /api/v1/challenges` |
| Accept | `POST /api/v1/challenges/{id}/accept` |
| Fund | `POST /api/v1/challenges/{id}/fund` |
| Proof | `POST /api/v1/challenges/{id}/proof` |
| Resolve | `POST /api/v1/challenges/{id}/resolve` |

### Connect
| Action | Endpoint |
|--------|----------|
| Create account | `POST /api/v1/connect` |
| Onboarding link | `POST /api/v1/connect/onboarding-link` |
| Check status | `GET /api/v1/connect/accounts/{id}/status` |

### Templates
| Action | Endpoint |
|--------|----------|
| List | `GET /api/v1/templates` |
| Detail | `GET /api/v1/templates/{id}` |
| Purchase | `POST /api/v1/templates/purchase` |

## License

MIT License. See [LICENSE](LICENSE).
