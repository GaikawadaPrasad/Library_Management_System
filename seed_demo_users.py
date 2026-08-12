import asyncio
from sqlalchemy import select

# Import all models to resolve SQLAlchemy mapper relationships
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.book import Book
from app.models.borrowing import Borrowing, BorrowingStatus
from app.models.notification import Notification
from app.core.security import hash_password
from app.database.connection import AsyncSessionLocal

async def seed():
    async with AsyncSessionLocal() as db:
        users_to_seed = [
            ("admin@library.com", "AdminPassword123!", UserRole.ADMIN, "System Admin"),
            ("librarian@library.com", "LibrarianPass123!", UserRole.LIBRARIAN, "Chief Librarian"),
            ("member@library.com", "MemberPass123!", UserRole.MEMBER, "Sample Member"),
        ]

        for email, password, role, name in users_to_seed:
            existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if not existing:
                db.add(User(
                    full_name=name,
                    email=email,
                    password_hash=hash_password(password),
                    role=role,
                    is_active=True,
                ))
                print(f"Created user: {email} ({role.value})")
            else:
                print(f"User already exists: {email}")

        await db.commit()
        print("Demo users successfully verified in database!")

if __name__ == "__main__":
    asyncio.run(seed())
