# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routers import user, dashboard, journal # Import your routers
from core.db import db_manager # Import the db connection manager

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Actions to perform on startup
    await db_manager.connect_db()
    # Initialize other resources like Gemini client if needed
    # print("Gemini Client Initialized...") # Placeholder
    yield # The application runs while yielded
    # Actions to perform on shutdown
    await db_manager.close_db()
    # print("Gemini Client Closed...") # Placeholder

# --- FastAPI App Creation ---
app = FastAPI(
    title="Echo V2 API",
    description="API for journaling, reflections, and user data.",
    version="0.1.0",
    lifespan=lifespan # Use the lifespan context manager
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins (adjust for production)
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods
    allow_headers=["*"], # Allow all headers
)

# --- Routers ---
app.include_router(user.router, prefix="/api", tags=["User"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(journal.router, prefix="/api", tags=["Journal"]) # Assuming journal endpoints are under /api

# --- Root Endpoint (Optional Health Check) ---
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint for basic health check."""
    return {"status": "ok", "message": "Welcome to Echo V2 API!"}

# --- Run with Uvicorn (for local development) ---
# You would typically run this using: uvicorn api.main:app --reload
# Example run block (optional, usually run via command line)
# if __name__ == "__main__":
#     import uvicorn
#     from core.config import settings
#     # Note: settings.host and settings.port are examples,
#     # ensure they are defined in your Settings model if you use them here.
#     uvicorn.run(
#         "api.main:app",
#         host=getattr(settings, 'host', "127.0.0.1"),
#         port=getattr(settings, 'port', 8000),
#         reload=True # Enable auto-reload for development
#     )