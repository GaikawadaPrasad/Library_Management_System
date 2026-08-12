import asyncio
from sqlalchemy import select
from app.models.user import User
from app.models.category import Category
from app.models.book import Book
from app.models.borrowing import Borrowing
from app.models.notification import Notification
from app.database.connection import AsyncSessionLocal

async def seed_categories():
    async with AsyncSessionLocal() as db:
        categories_data = [
            ("Computer Science & IT", "Software engineering, algorithms, programming languages, and AI"),
            ("Fiction & Literature", "Novels, classic literature, and creative storytelling"),
            ("Science & Technology", "Physics, chemistry, biology, astronomy, and modern engineering"),
            ("History & Biography", "Historical accounts, memoirs, and biographies of notable figures"),
            ("Business & Economics", "Finance, management, entrepreneurship, and market economics"),
        ]

        for name, desc in categories_data:
            existing = (await db.execute(select(Category).where(Category.name == name))).scalar_one_or_none()
            if not existing:
                db.add(Category(name=name, description=desc))
                print(f"Created category: {name}")
            else:
                print(f"Category already exists: {name}")

        await db.commit()
        print("Default categories successfully verified in database!")

if __name__ == "__main__":
    asyncio.run(seed_categories())
