# core/db.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings # Import settings from config.py

class Database:
    """Handles MongoDB connection and provides access to the database."""
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

    async def connect_db(self):
        """Establish database connection."""
        print("Connecting to MongoDB...")
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.mongodb_db_name]
        # Optional: Ping the server to confirm connection
        try:
             await self.client.admin.command('ping')
             print("Successfully connected to MongoDB!")
        except Exception as e:
             print(f"MongoDB connection failed: {e}")
             # Decide how to handle connection failure - exit, retry, etc.
             # For now, we'll let it proceed but db might be None

    async def close_db(self):
        """Close database connection."""
        if self.client:
            print("Closing MongoDB connection...")
            self.client.close()
            print("MongoDB connection closed.")

    def get_database(self) -> AsyncIOMotorDatabase | None:
        """Returns the database instance."""
        # Ensure connection is established or handle appropriately
        if not self.db:
             print("Warning: Database not connected.")
             # Optionally raise an error or attempt reconnection
        return self.db

# Create a single instance of the Database class
db_manager = Database()

# Convenience function to get the database instance
# Use this in your services/handlers
async def get_db() -> AsyncIOMotorDatabase:
    """
    Dependency function to get the database instance.
    Ensures the database is connected before returning.
    """
    if db_manager.db is None:
        # This might happen if connection failed initially.
        # Consider reconnecting or raising an appropriate error.
        # For simplicity now, we raise an error.
        # In a real app, you might want more robust handling.
        await db_manager.connect_db() # Attempt connection if not connected
        if db_manager.db is None:
             raise RuntimeError("Database connection is not available.")
    return db_manager.db


# Example of getting a specific collection (can be defined here or used directly in handlers)
# async def get_user_collection() -> AsyncIOMotorCollection:
#     db = await get_db()
#     return db["users"] # Assuming collection name is 'users'