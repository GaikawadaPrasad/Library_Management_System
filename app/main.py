from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, books, categories, borrowings, notifications, users

app = FastAPI(
    title="Library Management System API",
    description=(
        "Production-ready REST API for managing a physical library — "
        "inventory, members, borrowings, fines, and notifications."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ---------------------------------------------------------------------------
# CORS Middleware (Supports Web on any port, Mobile, and LAN IPs)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(categories.router)
app.include_router(borrowings.router)
app.include_router(notifications.router)
app.include_router(users.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "configured",
    }