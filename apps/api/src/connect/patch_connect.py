with open('service.py', 'r') as f:
    content = f.read()

old_code = '''async def create_payment_intent_for_challenge(
    amount_cents: int,
    currency: str,
    connected_account_id: str,
    challenge_id: str,
    party_role: str,
    application_fee_cents: int = 0,
) -> stripe.PaymentIntent:
    """
    Create a PaymentIntent to charge a party for a challenge stake.

    Uses Stripe's "destination charges" model:
    - Payment goes to platform (SYMIONE)
    - Platform fee is retained
    - Rest is transferred to connected account

    For challenges:
    - We collect from both parties
    - Hold until resolution
    - Transfer winnings to winner
    """
    payment_intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency.lower(),
        capture_method="manual",  # Authorize only, capture later
        payment_method_types=["card"],
        metadata={
            "challenge_id": challenge_id,
            "party_role": party_role,
            "type": "challenge_stake",
        },
        # We don't use transfer_data here because we need to hold funds
        # until resolution. Instead, we'll manually transfer after resolution.
    )

    return payment_intent'''

new_code = '''async def create_payment_intent_for_challenge(
    amount_cents: int,
    currency: str,
    connected_account_id: str,
    challenge_id: str,
    party_role: str,
    apply_protocol_fee: bool = True,
) -> stripe.PaymentIntent:
    """
    Create a PaymentIntent to charge a party for a challenge stake.

    Funds are collected to platform and held until resolution.
    The 5% protocol fee is applied during transfer to winner (not here).

    For challenges:
    - We collect from both parties
    - Hold funds on platform until resolution
    - Transfer winnings to winner with 5% protocol fee deducted
    """
    # Calculate protocol fee for metadata tracking
    protocol_fee_cents = int(amount_cents * PROTOCOL_FEE_PERCENT / 100) if apply_protocol_fee else 0

    payment_intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency.lower(),
        capture_method="manual",  # Authorize only, capture later
        payment_method_types=["card"],
        metadata={
            "challenge_id": challenge_id,
            "party_role": party_role,
            "type": "challenge_stake",
            "connected_account_id": connected_account_id,
            "protocol_fee_percent": str(PROTOCOL_FEE_PERCENT),
            "protocol_fee_cents": str(protocol_fee_cents),
        },
        # Funds collected to platform, transferred to winner after resolution
        # with protocol fee deducted via transfer_to_winner()
    )

    return payment_intent'''

content = content.replace(old_code, new_code)

with open('service.py', 'w') as f:
    f.write(content)

print('Patched connect/service.py successfully')
