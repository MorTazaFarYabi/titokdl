from db.models import Settings, SubscriptionPlan, UserSubscriptionPlan
from config import Config
import asyncio



async def set_defaults():
    
    instagram_request_types = [
        value for key, value in Config.INSTAGRAM_REUQEST_TYPES.__dict__.items()
        if not key.startswith("__") and not callable(value)
    ]

    if await SubscriptionPlan.all().count() ==0:
        default_plan = SubscriptionPlan()
        default_plan.name = "رایگان"
        default_plan.permitted_downloads = instagram_request_types
        default_plan.request_per_second_limit = 30
        default_plan.does_see_forced_joins = True
        default_plan.default_plan = True
        await default_plan.save()

    if not await Settings.first():
        setting = Settings()
        setting.max_forced_channels = 3
        setting.default_language = "fa"
        setting.is_bot_active = True
        setting.cache_times= Config.CACHE_TIME
        await setting.save()
    # create admins in db
    # ....
