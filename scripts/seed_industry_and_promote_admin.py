"""Utility script to seed an industry track and promote a user to admin.

Run with::

    python scripts/seed_industry_and_promote_admin.py --email user@example.com --username AdminUser

If no arguments are supplied, defaults are used. The script is idempotent:
- Creates (or reuses) the default Software Engineering industry track.
- Updates the specified user to have the desired username and admin role.
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

# Ensure project root is on the import path when run as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.database.industry_models import IndustryTrack
from app.database.user_models import User, UserRole

TRACK_SLUG = "software-engineering-default"
TRACK_NAME = "Software Engineering"
TRACK_DESCRIPTION = "Seeded software engineering industry track."
DEFAULT_USER_EMAIL = "admin@example.com"
DEFAULT_USERNAME = "AdminUser"


async def ensure_industry_track(session) -> IndustryTrack:
    """Create the default industry track if it does not already exist."""
    result = await session.execute(
        select(IndustryTrack).where(IndustryTrack.slug == TRACK_SLUG)
    )
    track = result.scalar_one_or_none()

    if track:
        print(
            f"✓ Industry track already exists (id={track.id}, slug='{TRACK_SLUG}')."
        )
        return track

    now = datetime.utcnow()
    track = IndustryTrack(
        name=TRACK_NAME,
        description=TRACK_DESCRIPTION,
        slug=TRACK_SLUG,
        color_theme="#1F6FEB",
        difficulty_levels=["beginner", "intermediate", "advanced"],
        methodologies_focus=["agile", "scrum"],
        learning_objectives=[
            "Build production-ready software",
            "Collaborate effectively across teams",
            "Apply modern development practices",
        ],
        prerequisite_skills=["Problem solving", "Basic programming"],
        career_outcomes=["Software Engineer", "Backend Developer", "Tech Lead"],
        total_projects=0,
        total_learners=0,
        average_completion_rate=None,
        is_active=True,
        is_featured=False,
        meta_description="Default software engineering learning track",
        created_at=now,
        updated_at=now,
    )

    session.add(track)
    await session.commit()
    await session.refresh(track)
    print(f"✓ Created industry track (id={track.id}, slug='{TRACK_SLUG}').")
    return track


async def promote_user_to_admin(session, *, email: str, username: str) -> None:
    """Promote the target user to admin and adjust their username."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise RuntimeError(
            f"User with email '{email}' does not exist. Create the user first."
        )

    updates = []
    if user.username != username:
        updates.append(f"username '{user.username}' → '{username}'")
        user.username = username
    if user.role != UserRole.ADMIN:
        updates.append(f"role '{user.role.value}' → '{UserRole.ADMIN.value}'")
        user.role = UserRole.ADMIN

    if updates:
        await session.commit()
        print("✓ Updated user:")
        for update in updates:
            print(f"   - {update}")
    else:
        print("✓ User already has desired username and admin role.")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed default industry track and promote a user to admin."
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_USER_EMAIL,
        help="Email of the user to promote (default: %(default)s)",
    )
    parser.add_argument(
        "--username",
        default=DEFAULT_USERNAME,
        help="Username to assign to the promoted admin (default: %(default)s)",
    )
    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
        try:
            await ensure_industry_track(session)
            await promote_user_to_admin(session, email=args.email, username=args.username)
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
