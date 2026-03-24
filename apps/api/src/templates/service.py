"""
Template marketplace service.

Hardcoded registry of SYMIONE protocol templates.
Free templates = maximum distribution. Paid = credibility signal + revenue.
"""
import stripe
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings

settings = get_settings()
stripe.api_key = settings.stripe_secret_key


@dataclass
class Template:
    id: str
    name: str
    description: str
    long_description: str
    icon: str
    price: int  # cents, 0 = free
    is_pro: bool
    repo_url: Optional[str]
    deploy_url: Optional[str]
    stack: list[str]
    use_cases: list[str]
    features: list[str]


# Template Registry - hardcoded, no database needed for 4 templates
TEMPLATES: dict[str, Template] = {
    "reliable": Template(
        id="reliable",
        name="Reliable",
        description="Peer challenges with real stakes. Solo, Duel, and Cell modes.",
        long_description="Turn any promise into a commitment with real money on the line. "
                        "Create challenges against yourself (Solo), a friend (Duel), or "
                        "a group (Cell). Both parties stake, winner takes all. Built-in "
                        "proof validation, dispute resolution, and instant settlement.",
        icon="⚡",
        price=0,
        is_pro=False,
        repo_url="https://github.com/echofield/reliable-template",
        deploy_url="https://vercel.com/new/clone?repository-url=https://github.com/echofield/reliable-template",
        stack=["Next.js", "Tailwind", "Stripe Connect", "SYMIONE SDK"],
        use_cases=[
            "Fitness accountability apps",
            "Friend bets",
            "Group challenges",
            "Quit-smoking pacts",
            "Study groups",
        ],
        features=[
            "Solo, Duel, and Cell challenge modes",
            "Real-time stake tracking",
            "Proof submission and validation",
            "Automatic settlement on resolution",
            "Mobile-responsive dark UI",
        ],
    ),
    "escrow": Template(
        id="escrow",
        name="Escrow",
        description="Freelancer proof-of-delivery. Pay when conditions are met.",
        long_description="Secure payments for freelancers and contractors. Client deposits "
                        "funds into escrow, freelancer delivers work, both sign off, "
                        "funds release. If there's a dispute, the protocol handles arbitration. "
                        "No more chasing invoices or worrying about non-payment.",
        icon="🔒",
        price=0,
        is_pro=False,
        repo_url="https://github.com/echofield/escrow-template",
        deploy_url="https://vercel.com/new/clone?repository-url=https://github.com/echofield/escrow-template",
        stack=["Next.js", "Tailwind", "Stripe Connect", "SYMIONE SDK"],
        use_cases=[
            "Contractor payments",
            "Milestone escrow",
            "Design delivery",
            "API development contracts",
            "Consulting engagements",
        ],
        features=[
            "Milestone-based payments",
            "File upload for deliverables",
            "Mutual sign-off requirement",
            "Automatic release on approval",
            "Dispute resolution flow",
        ],
    ),
    "accord": Template(
        id="accord",
        name="Accord",
        description="Bilateral agreements with mutual signature and conditional release.",
        long_description="Formalize any agreement between two parties with money backing it. "
                        "Both parties define terms, both sign, funds are held until conditions "
                        "are met. Perfect for handshake deals that need teeth.",
        icon="🤝",
        price=0,
        is_pro=False,
        repo_url="https://github.com/echofield/accord-template",
        deploy_url="https://vercel.com/new/clone?repository-url=https://github.com/echofield/accord-template",
        stack=["Next.js", "Tailwind", "Stripe Connect", "SYMIONE SDK"],
        use_cases=[
            "Handshake deals",
            "Roommate agreements",
            "Co-founder vesting",
            "Service exchanges",
            "Conditional donations",
        ],
        features=[
            "Bilateral agreement creation",
            "Mutual signature requirement",
            "Conditional fund release",
            "Time-based triggers",
            "Amendment workflow",
        ],
    ),
    "creator-pro": Template(
        id="creator-pro",
        name="Creator Pro",
        description="Run a challenge business for your audience. Your brand, your fees, your revenue.",
        long_description="Everything in Reliable, plus the tools to run challenges as a business. "
                        "Add your branding, set your own fees on top of the platform fee, "
                        "track your revenue, manage your audience. Perfect for fitness coaches, "
                        "content creators, and community leaders who want to monetize accountability.",
        icon="👑",
        price=14900,  # €149 in cents
        is_pro=True,
        repo_url=None,  # Delivered after purchase
        deploy_url=None,  # Delivered after purchase
        stack=["Next.js", "Tailwind", "Stripe Connect", "SYMIONE SDK"],
        use_cases=[
            "Fitness coaching platforms",
            "Creator community challenges",
            "Corporate team accountability",
            "Coaching programs",
            "Membership communities",
        ],
        features=[
            "Everything in Reliable, plus:",
            "Creator dashboard with revenue analytics",
            "Custom branding (logo, colors, domain)",
            "Configurable creator fee on top of platform fee",
            "Audience management and email capture",
            "Referral tracking and attribution",
            "Priority support via SYMI Intelligence",
        ],
    ),
}


def get_all_templates() -> list[Template]:
    """Return all templates."""
    return list(TEMPLATES.values())


def get_template(template_id: str) -> Optional[Template]:
    """Get a specific template by ID."""
    return TEMPLATES.get(template_id)


async def create_purchase_payment_intent(
    template_id: str,
    email: str,
) -> stripe.PaymentIntent:
    """
    Create a PaymentIntent for a paid template purchase.

    Returns the PaymentIntent with client_secret for frontend Stripe Elements.
    """
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Template {template_id} not found")

    if template.price == 0:
        raise ValueError(f"Template {template_id} is free, no payment required")

    payment_intent = stripe.PaymentIntent.create(
        amount=template.price,
        currency="eur",
        receipt_email=email,
        payment_method_types=["card"],
        metadata={
            "type": "template_purchase",
            "template_id": template_id,
            "template_name": template.name,
            "buyer_email": email,
        },
    )

    return payment_intent


async def verify_purchase_and_deliver(
    payment_intent_id: str,
    email: str,
) -> dict:
    """
    Verify payment succeeded and return delivery info.

    For MVP, delivery is manual - we log the sale and return instructions.
    The buyer will be added as a GitHub collaborator manually.
    """
    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

    if payment_intent.status != "succeeded":
        raise ValueError(f"Payment not successful. Status: {payment_intent.status}")

    template_id = payment_intent.metadata.get("template_id")
    if not template_id:
        raise ValueError("Invalid payment: missing template_id in metadata")

    template = get_template(template_id)
    if not template:
        raise ValueError(f"Template {template_id} not found")

    # For MVP: manual delivery
    # In production, this would:
    # 1. Add buyer as GitHub collaborator via GitHub API
    # 2. Generate unique deploy link
    # 3. Send delivery email via notification service

    return {
        "template_id": template_id,
        "template_name": template.name,
        "buyer_email": email,
        "delivery_method": "manual",
        "instructions": (
            "Thank you for purchasing Creator Pro! "
            "You'll receive access to the private repository within 1 hour. "
            "We'll add you as a collaborator on GitHub and send deployment instructions "
            "to your email. Questions? Contact support@symione.com"
        ),
        # These would be populated after manual delivery
        "repo_url": None,
        "deploy_url": None,
    }


async def handle_purchase_webhook(payment_intent: stripe.PaymentIntent) -> dict:
    """
    Handle successful purchase from Stripe webhook.

    Logs the sale for manual fulfillment.
    In production, would trigger automated delivery.
    """
    if payment_intent.metadata.get("type") != "template_purchase":
        return {"handled": False, "reason": "Not a template purchase"}

    template_id = payment_intent.metadata.get("template_id")
    buyer_email = payment_intent.metadata.get("buyer_email")

    # Log for manual fulfillment
    # In production: send to notification service, add to fulfillment queue
    print(f"[TEMPLATE PURCHASE] {template_id} purchased by {buyer_email}")
    print(f"[TEMPLATE PURCHASE] PaymentIntent: {payment_intent.id}")
    print(f"[TEMPLATE PURCHASE] Amount: {payment_intent.amount / 100} EUR")

    # TODO: Send admin notification
    # TODO: Queue for automatic GitHub invite

    return {
        "handled": True,
        "template_id": template_id,
        "buyer_email": buyer_email,
        "amount": payment_intent.amount,
    }
