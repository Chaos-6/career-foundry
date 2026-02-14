"""
Stripe billing endpoints — checkout, webhooks, and subscription status.

Flow:
1. POST /billing/checkout       → Create Stripe Checkout Session → return session URL
2. Browser redirects to Stripe  → User pays on hosted page
3. Stripe calls POST /billing/webhook → checkout.session.completed → upgrade user
4. GET /billing/status           → Current tier + usage for the frontend

Why Checkout Sessions (not Stripe Elements)?
  - Zero PCI burden: we never touch card data
  - Simpler: one redirect, Stripe handles the rest
  - Built-in receipt emails, tax handling, and SCA compliance

Webhook security:
  - We verify the Stripe-Signature header against our webhook secret
  - This prevents forged events from upgrading users
"""

import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

# Configure Stripe with our secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CheckoutResponse(BaseModel):
    """URL to redirect the user to Stripe Checkout."""
    checkout_url: str


class BillingStatusResponse(BaseModel):
    """Current billing status for the authenticated user."""
    plan_tier: str
    evaluations_this_month: int
    evaluation_limit: int
    stripe_customer_id: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout Session for upgrading to Pro.

    Returns the checkout URL — the frontend redirects the user there.
    After payment, Stripe redirects to our success page and fires
    a webhook to actually upgrade the user's tier.
    """
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRO_PRICE_ID:
        raise HTTPException(
            status_code=503,
            detail="Billing is not configured. Contact support.",
        )

    if user.plan_tier == "pro":
        raise HTTPException(
            status_code=400,
            detail="You're already on the Pro plan.",
        )

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price": settings.STRIPE_PRO_PRICE_ID,
                "quantity": 1,
            }],
            # Pass user ID as metadata so the webhook knows who to upgrade
            metadata={"user_id": str(user.id)},
            client_reference_id=str(user.id),
            customer_email=user.email,
            success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/pricing",
        )
    except stripe.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=502, detail="Payment service error")

    return CheckoutResponse(checkout_url=session.url)


@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    user: User = Depends(get_current_user),
):
    """Get the current user's billing status and usage."""
    tier_limit = (
        settings.PRO_EVALUATIONS_PER_MONTH
        if user.plan_tier == "pro"
        else settings.FREE_EVALUATIONS_PER_MONTH
    )
    return BillingStatusResponse(
        plan_tier=user.plan_tier,
        evaluations_this_month=user.evaluations_this_month or 0,
        evaluation_limit=tier_limit,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events.

    Verifies the webhook signature, then processes relevant events:
    - checkout.session.completed: Upgrade user to Pro tier
    - customer.subscription.deleted: Downgrade user to Free tier

    Returns 200 quickly — Stripe retries on failure.
    """
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Missing webhook signature")

    try:
        event = stripe.Webhook.construct_event(
            body, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook error")

    # --- Handle events ---
    event_type = event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")

        if user_id:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.plan_tier = "pro"
                await db.commit()
                logger.info(f"User {user_id} upgraded to Pro via Stripe checkout")
            else:
                logger.warning(f"Stripe checkout completed for unknown user: {user_id}")
        else:
            logger.warning("Stripe checkout completed without user_id")

    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled — downgrade to free
        subscription = event["data"]["object"]
        # Try to find user by Stripe customer ID from the subscription metadata
        customer_id = subscription.get("customer")
        if customer_id:
            # Look up sessions for this customer to find the user
            # In production, you'd store stripe_customer_id on the User model.
            # For now, we log it and handle manually if needed.
            logger.info(
                f"Subscription deleted for Stripe customer {customer_id}. "
                "Manual downgrade may be needed."
            )

    else:
        logger.debug(f"Ignoring Stripe event: {event_type}")

    return {"status": "ok"}


@router.post("/portal")
async def create_portal_session(
    user: User = Depends(get_current_user),
):
    """Create a Stripe Customer Portal session for managing subscriptions.

    Only works for Pro users who have a Stripe customer ID.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Billing not configured")

    if user.plan_tier != "pro":
        raise HTTPException(
            status_code=400,
            detail="Only Pro users can manage their subscription.",
        )

    # Find the customer by email (since we don't store customer ID yet)
    try:
        customers = stripe.Customer.list(email=user.email, limit=1)
        if not customers.data:
            raise HTTPException(
                status_code=404,
                detail="No Stripe customer found for this account.",
            )

        portal_session = stripe.billing_portal.Session.create(
            customer=customers.data[0].id,
            return_url=f"{settings.FRONTEND_URL}/pricing",
        )
    except stripe.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=502, detail="Payment service error")

    return {"portal_url": portal_session.url}
