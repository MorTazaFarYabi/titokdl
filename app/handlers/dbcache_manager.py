import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlite3
import threading
from db.models import Settings, ForcedJoinChannelOrder

class DBCache:
    """Singleton class to cache and periodically update data."""

    _instance = None  # Stores the single instance



    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBCache, cls).__new__(cls)

            cls._instance.settings = {}
            cls._instance.forced_channels = {}

            cls._instance.cached_data = {}  # Store fetched data
            cls._instance.scheduler = AsyncIOScheduler()
            cls._instance.scheduler.add_job(cls._instance.fetch_data, "interval", minutes=10)  # Run every 10 minutes
            cls._instance.scheduler.start()
            # Schedule the initial fetch_data call asynchronously
            asyncio.create_task(cls._instance.fetch_data())
        return cls._instance  # Always return the same instance

    async def fetch_data(self):
        """Fetches fresh data from the database."""
        self.settings = await Settings.first()
        self.forced_channels = await ForcedJoinChannelOrder.filter(
            completion_status = False
            ).limit(self.settings.max_forced_channels
            ).order_by('-is_fake_force').all()
        
    


        
