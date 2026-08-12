import asyncio
from sqlalchemy import select
from app.models.user import User
from app.models.category import Category
from app.models.book import Book
from app.models.borrowing import Borrowing
from app.models.notification import Notification
from app.database.connection import AsyncSessionLocal

async def seed_books():
    async with AsyncSessionLocal() as db:
        # Get category IDs
        cs_cat = (await db.execute(select(Category).where(Category.name == "Computer Science & IT"))).scalar_one_or_none()
        fiction_cat = (await db.execute(select(Category).where(Category.name == "Fiction & Literature"))).scalar_one_or_none()
        science_cat = (await db.execute(select(Category).where(Category.name == "Science & Technology"))).scalar_one_or_none()

        books_data = [
            {
                "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
                "author": "Robert C. Martin",
                "category_id": cs_cat.id if cs_cat else None,
                "total_copies": 5,
                "available_copies": 5,
                "isbn": "978-0132350884",
                "publisher": "Prentice Hall",
                "publication_year": 2008,
                "cover_image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=600&auto=format&fit=crop&q=60",
                "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees.",
            },
            {
                "title": "The Pragmatic Programmer",
                "author": "Andrew Hunt & David Thomas",
                "category_id": cs_cat.id if cs_cat else None,
                "total_copies": 4,
                "available_copies": 4,
                "isbn": "978-0135957059",
                "publisher": "Addison-Wesley",
                "publication_year": 2019,
                "cover_image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=60",
                "description": "Illustrates the best approaches and major pitfalls of many aspects of software development.",
            },
            {
                "title": "To Kill a Mockingbird",
                "author": "Harper Lee",
                "category_id": fiction_cat.id if fiction_cat else None,
                "total_copies": 3,
                "available_copies": 3,
                "isbn": "978-0061120084",
                "publisher": "Harper Perennial",
                "publication_year": 1960,
                "cover_image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop&q=60",
                "description": "A Pulitzer Prize-winning masterpiece exploring honor, injustice, and racism in the American South.",
            },
        ]

        for bdata in books_data:
            if not bdata["category_id"]:
                continue
            existing = (await db.execute(select(Book).where(Book.title == bdata["title"]))).scalar_one_or_none()
            if not existing:
                db.add(Book(**bdata))
                print(f"Created book: {bdata['title']}")
            else:
                print(f"Book already exists: {bdata['title']}")

        await db.commit()
        print("Sample books successfully verified in database!")

if __name__ == "__main__":
    asyncio.run(seed_books())
