from __future__ import annotations

from app.config import settings
from app.db import SessionLocal
from app.models import ConsentRecord, CreditLedger, Organization, Team, TeamMember, User
from app.security import PLANS, hash_password, slugify


def seed() -> None:
    db = SessionLocal()
    try:
        email = settings.admin_email.strip().lower()
        if db.query(User).filter(User.email == email).one_or_none():
            return
        slug = slugify("Infinity X Labs")
        if db.query(Organization).filter(Organization.slug == slug).one_or_none():
            slug = slug + "-dev"
        org = Organization(
            name="Infinity X Labs",
            slug=slug,
            plan="free",
            credits_balance=PLANS["free"]["credits"],
            is_fixture=True,
        )
        db.add(org)
        db.flush()
        user = User(
            org_id=org.id,
            email=email,
            password_hash=hash_password(settings.admin_password),
            full_name=settings.admin_name,
            role="owner",
            is_fixture=True,
        )
        db.add(user)
        db.flush()
        team = Team(org_id=org.id, name="Core investigations", is_fixture=True)
        db.add(team)
        db.flush()
        db.add(TeamMember(team_id=team.id, user_id=user.id, member_role="lead"))
        db.add(CreditLedger(org_id=org.id, delta=PLANS["free"]["credits"], reason="development fixture free plan allowance"))
        db.add(
            ConsentRecord(
                org_id=org.id,
                user_id=user.id,
                purpose="Development fixture account terms",
                lawful_basis="contract",
                subject_type="account",
                text_version="account-v1",
            )
        )
        db.commit()
    finally:
        db.close()
