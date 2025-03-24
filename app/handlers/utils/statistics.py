
import asyncio
from datetime import datetime, timedelta, UTC, timezone
from zoneinfo import ZoneInfo
from tortoise.expressions import Q
from tortoise.queryset import QuerySet
from tortoise.functions import Count

from config import Config
from db.models import APIReq, ChannelMembership, InstagramRequest, Referral, User

from handlers.constants.messages import Messages
import jdatetime


async def get_statistics():
    """
    Fetches user statistics, including total users and users joined in specific time periods.
    """

    
    
    now = datetime.now(Config.TIMEZONE)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # print((today_start))

    yesterday_start = today_start - timedelta(days=1)
    pesterday_start = yesterday_start - timedelta(days=1)

    last_7_days = today_start - timedelta(days=7)
    last_30_days = today_start - timedelta(days=30)
    last_60_days = today_start - timedelta(days=60)
    last_24_hours = now - timedelta(hours=24)
    last_48_hours = last_24_hours - timedelta(hours=24)
    last_72_hours = last_48_hours - timedelta(hours=24)

    stats_sections = {}

    users_with_interaction_with_bot = User.filter(
        has_started = True, 
        is_from_joining_a_chat = False,
        is_from_accepter = False
        )
    accepter_users = User.filter(is_from_accepter = True)
    accepter_users_who_started = User.filter(is_from_accepter = True, has_started = True)
    users_who_blocked = User.filter(has_blocked_the_bot = True)
    forced_joins = ChannelMembership.filter(
                joined_at__isnull = False,
                left_at__isnull = True,
                )


    stats_titles = [
        'کاربرانی که مستقیما ربات را استارت کردند',
        'کاربران اکسپتر',
        'کاربران اکسپتر که استارت زدن',
        'بلاک کننده ها',
        'آمار ممبر جوین اجباری'
    ]
    
    stats_coroutines = [
        get_query_stats_within_different_timeframes(db_query= users_with_interaction_with_bot),
        get_query_stats_within_different_timeframes(db_query= accepter_users),
        get_query_stats_within_different_timeframes(db_query= accepter_users_who_started),
        get_query_stats_within_different_timeframes(db_query= users_who_blocked),
        get_query_stats_within_different_timeframes(db_query= forced_joins)
    ]

    unique_requests = [
        InstagramRequest.filter(created_at__gte=today_start).annotate(count=Count("user_id", distinct=True)).values("count"),
        InstagramRequest.filter(created_at__gte = yesterday_start, created_at__lte=today_start).annotate(count=Count("user_id", distinct=True)).values("count"),
        InstagramRequest.filter(created_at__gte = pesterday_start, created_at__lte=yesterday_start).annotate(count=Count("user_id", distinct=True)).values("count"),
        # InstagramRequest.filter(created_at__gte = today_start, user__created_at__gte=today_start).annotate(count=Count("user_id", distinct=True)).values("count"),
        ]
    
    unique_requests = await asyncio.gather(*unique_requests)
    unique_requests = [ur[0]['count'] for ur in unique_requests]
    unique_today_requesters, unique_last_48_requesters, unique_last_72_requesters = unique_requests
    fresh_users = len(await InstagramRequest.filter(created_at__gte = today_start, user__created_at__gte=today_start).distinct().values("user_id"))


    stats_sections.update(dict(zip(stats_titles, await asyncio.gather(*stats_coroutines))))
    stats_sections['درخواست دهنده های اینستاگرام'] = f"""
🔹 تازه نفس امروز: {fresh_users}
🔹 امروز: {unique_today_requesters}
🔹 دیروز: {unique_last_48_requesters}
🔹 پریروز: {unique_last_72_requesters}
"""

    # unique_today_requesters = len(await InstagramRequest.filter(created_at__gte = today_start).distinct().values("user_id"))
    # unique_last_48_requesters = len(await InstagramRequest.filter(created_at__gte = yesterday_start, created_at__lte=today_start).distinct().values("user_id"))
    # unique_last_72_requesters = len(await InstagramRequest.filter(created_at__gte = pesterday_start, created_at__lte=yesterday_start).distinct().values("user_id"))
    # fresh_users = len(await InstagramRequest.filter(created_at__gte = today_start, user__created_at__gte=today_start).distinct().values("user_id"))




    # Format the message
    
    stats_message = ""
    for section_title, section_message in stats_sections.items():
        stats_message += f"📊📊 {section_title} \n{section_message}\n\n"
        
    return stats_message


async def get_API_statistics():

    now = datetime.now(Config.TIMEZONE)  # Current UTC time
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    last_60_days = now - timedelta(days=60)

    # today
    today_instagram_requests = await InstagramRequest.filter(created_at__gte=today_start).count()
    today_API_requests = await APIReq.filter(created_at__gte=today_start).count()
    today_cached_responses = today_instagram_requests - today_API_requests
    today_ONE_API_requests = await APIReq.filter(created_at__gte=today_start, service_provider=Config.SERVICE_PROVIDERS.ONEAPI).count()
    today_fastsaverapi_requests = await APIReq.filter(created_at__gte=today_start, service_provider=Config.SERVICE_PROVIDERS.FASTSAVERAPI).count()

    # yesterday
    yesterday_instagram_requests = await InstagramRequest.filter(created_at__gte=yesterday_start, created_at__lt=today_start).count()
    yesterday_API_requests = await APIReq.filter(created_at__gte=yesterday_start, created_at__lt=today_start).count()
    yesterday_cached_responses = yesterday_instagram_requests - yesterday_API_requests
    yesterday_ONE_API_requests = await APIReq.filter(created_at__gte=yesterday_start, created_at__lt=today_start, service_provider=Config.SERVICE_PROVIDERS.ONEAPI).count()
    yesterday_fastsaverapi_requests = await APIReq.filter(created_at__gte=yesterday_start, created_at__lt=today_start, service_provider=Config.SERVICE_PROVIDERS.FASTSAVERAPI).count()


    # last 30 days
    this_month_instagram_requests = await InstagramRequest.filter(created_at__gte=last_30_days).count()
    this_month_requests = await APIReq.filter(created_at__gte=last_30_days).count()
    this_month_responses = today_instagram_requests - today_API_requests
    this_month_ONE_API_requests = await APIReq.filter(created_at__gte=last_30_days, service_provider=Config.SERVICE_PROVIDERS.ONEAPI).count()
    this_month_fastsaverapi_requests = await APIReq.filter(created_at__gte=last_30_days, service_provider=Config.SERVICE_PROVIDERS.FASTSAVERAPI).count()

    return Messages.API_STATISTICS.format(
        today_instagram_requests,
        today_API_requests,
        today_cached_responses,
        today_ONE_API_requests,
        today_fastsaverapi_requests,
        yesterday_instagram_requests,
        yesterday_API_requests,
        yesterday_cached_responses,
        yesterday_ONE_API_requests,
        yesterday_fastsaverapi_requests,
        this_month_instagram_requests,
        this_month_requests,
        this_month_responses,
        this_month_ONE_API_requests,
        this_month_fastsaverapi_requests
    )


async def get_referral_statistics():

    referrals = Referral.all()
    
    stats = await get_query_stats_within_different_timeframes(
        db_query= referrals
        )
    message= f"+++ آمار ممبر جوین اجباری\n {stats}"

    return message    

async def get_API_health_statistics():
    now = datetime.now(Config.TIMEZONE)  # Current UTC time
    
    # Subtract 24 hours
    twenty_four_hours_ago = now - timedelta(hours=24)
    thirty_days_ago = now - timedelta(days=30)

    # In general
    last24hours_API_requests = await APIReq.filter(
        created_at__gte=twenty_four_hours_ago, 
        ).count() +1
    last24hours_API_successful_requests = await APIReq.filter(
        created_at__gte=twenty_four_hours_ago, 
        status=Config.REQ_STATUS.SUCCESS
        ).count()
    
    last24hours_API_success_rate = last24hours_API_successful_requests/last24hours_API_requests*100
    last30days_API_requests = await APIReq.filter(
        created_at__gte=thirty_days_ago, 
        ).count() +1
    last30days_API_successful_requests = await APIReq.filter(
        created_at__gte=thirty_days_ago, 
        status=Config.REQ_STATUS.SUCCESS
        ).count()
    last30days_API_success_rate = last30days_API_successful_requests/last30days_API_requests*100
    
    # ONE API
    last24hours_ONE_API_requests = await APIReq.filter(
        created_at__gte=twenty_four_hours_ago, 
        service_provider=Config.SERVICE_PROVIDERS.ONEAPI
        ).count() + 1
    last24hours_ONE_API_successful_requests = await APIReq.filter(
        created_at__gte=twenty_four_hours_ago, 
        service_provider=Config.SERVICE_PROVIDERS.ONEAPI,
        status=Config.REQ_STATUS.SUCCESS
        ).count() 
    
    last24hours_ONE_API_success_rate = last24hours_ONE_API_successful_requests/last24hours_ONE_API_requests*100
    
    last30days_ONE_API_requests = await APIReq.filter(
        created_at__gte=thirty_days_ago, 
        service_provider=Config.SERVICE_PROVIDERS.ONEAPI
        ).count() + 1
    last30days_ONE_API_successful_requests = await APIReq.filter(
        created_at__gte=thirty_days_ago, 
        service_provider=Config.SERVICE_PROVIDERS.ONEAPI,
        status=Config.REQ_STATUS.SUCCESS
        ).count()
    
    last30days_ONE_API_success_rate = last30days_ONE_API_successful_requests/last30days_ONE_API_requests*100
    
    # Fast Server API
    last24h_FASESAVER_API_requests = await APIReq.filter(
        created_at__gte=twenty_four_hours_ago, 
        service_provider=Config.SERVICE_PROVIDERS.FASTSAVERAPI
        ).count() + 1
    last24hours_FASESAVER_API_successful_requests = await APIReq.filter(
        created_at__gte=twenty_four_hours_ago, 
        service_provider=Config.SERVICE_PROVIDERS.FASTSAVERAPI,
        status=Config.REQ_STATUS.SUCCESS
        ).count()
    
    last24hours_FASESAVER_API_success_rate = last24hours_FASESAVER_API_successful_requests/last24h_FASESAVER_API_requests*100
    
    last30days_FASESAVER_API_requests = await APIReq.filter(
        created_at__gte=thirty_days_ago, 
        service_provider=Config.SERVICE_PROVIDERS.FASTSAVERAPI
        ).count() + 1
    last30days_FASESAVER_API_successful_requests = await APIReq.filter(
        created_at__gte=thirty_days_ago, 
        service_provider=Config.SERVICE_PROVIDERS.FASTSAVERAPI,
        status=Config.REQ_STATUS.SUCCESS
        ).count()
    
    last30days_FASESAVER_API_success_rate = last30days_FASESAVER_API_successful_requests/last30days_FASESAVER_API_requests*100
    


    return Messages.API_HEALTH.format(
        last24hours_API_requests,
        last24hours_API_successful_requests,
        last24hours_API_success_rate,
        last24hours_ONE_API_requests,
        last24hours_ONE_API_successful_requests,
        last24hours_ONE_API_success_rate,
        last24h_FASESAVER_API_requests,
        last24hours_FASESAVER_API_successful_requests,
        last24hours_FASESAVER_API_success_rate,
        last30days_API_requests,
        last30days_API_successful_requests,
        last30days_API_success_rate,
        last30days_ONE_API_requests,
        last30days_ONE_API_successful_requests,
        last30days_ONE_API_success_rate,
        last30days_FASESAVER_API_requests,
        last30days_FASESAVER_API_successful_requests,
        last30days_FASESAVER_API_success_rate
    )


async def get_stats_by_creation_time(db_query:QuerySet, last_x_days=3) -> list:
    now = datetime.now(Config.TIMEZONE)  # Current UTC time, timezone aware
    stats = []
    for day in range(1, last_x_days+1):
        this_24_start = now - timedelta(hours=24*(day-1))
        previous_24_start = now - timedelta(hours=24*day)
        # print(f"Day {day} range: {previous_24_start} < created_at <= {this_24_start}")
        count = await db_query.filter(
            created_at__lte=this_24_start,
            created_at__gt=previous_24_start
        ).count()
        stats.append(count)
    return stats

async def get_query_stats_within_different_timeframes(db_query:QuerySet) -> list:
    now = datetime.now(Config.TIMEZONE)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    the_day_before_yesterday_start = yesterday_start - timedelta(days=1)
    last_7_days = today_start - timedelta(days=7)
    the_week_before_last_week = last_7_days - timedelta(days=7)
    last_30_days = today_start - timedelta(days=30)
    last_60_days = today_start - timedelta(days=60)
    
    one_hundred_year_ago = now - timedelta(days=36500)

    # last_24_hours = now - timedelta(hours=24)
    # last_48_hours = last_24_hours - timedelta(hours=24)
    # last_72_hours = last_48_hours - timedelta(hours=24)

    timeframes = {
        #(start, end)
        'امروز': (today_start, now),
        'دیروز': (yesterday_start, today_start),
        'پریروز':(the_day_before_yesterday_start, yesterday_start),

        'هفت روز گذشته':(last_7_days, now),
        'هفته قبلش':(the_week_before_last_week, last_7_days),

        'سی روز گذشته':(last_30_days, now),
        'سی روز قبلش':(last_60_days, last_30_days),

        'آمار کل':(one_hundred_year_ago, now)
    }

    message = ""

    stats = []
    for title, period in timeframes.items():

        period_start, period_end = period
        
        count = db_query.filter(
            created_at__gt=period_start,
            created_at__lte=period_end,
        ).count()
        stats.append(count)

    counts = await asyncio.gather(*stats)

    title_count = list(zip(timeframes.keys(), counts))
    for title, count in title_count:
        message += f"🔹 {title}: {count}\n"
    return message



async def get_request_type_statistics():

    

    request_types = [
        value
        for key, value in Config.INSTAGRAM_REUQEST_TYPES.__dict__.items()
        if not key.startswith('__')
    ]

    stats= {}
    for request_type in request_types:
        query = InstagramRequest.filter(request_type = request_type)
        stats[request_type] = await get_stats_by_creation_time(db_query=query, last_x_days= 3)
    
    # print(stats)
    message = "📊 آمار درخواست ها: \n\n"
    for request_type, list_of_stats in stats.items():
        message += f"📈 {request_type}\n"
        for n in list_of_stats:
            message+= f"📍 {n} \n"
        message += "\n\n"
    return message


async def get_loyalty_statistics():

    now = datetime.now(Config.TIMEZONE)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    last_60_days = now - timedelta(days=60)

    last_24_hours = now - timedelta(hours=24)

    # fresh_users = len(await InstagramRequest.filter(created_at__gte = last_24_hours, user__created_at__gte=last_24_hours).distinct().values("user_id"))
    # fresh_users = await InstagramRequest.filter(created_at__gte = today_start, user__created_at__gte=today_start).annotate(count=Count("user_id", distinct=True)).values('count')
    fresh_users = len(await InstagramRequest.filter(created_at__gte = today_start, user__created_at__gte=today_start).distinct().values("user_id"))

    # fresh_users = fresh_users[0]['count']
    returning_user = await User.filter(created_at__lt = last_24_hours, last_interaction_at__gt = last_24_hours).count() # over one day loyalty
    two_months_loyalty = await User.filter(created_at__lt = last_60_days, last_interaction_at__gt = last_24_hours).count()
    month_loyalty = await User.filter(created_at__lt = last_30_days, last_interaction_at__gt = last_24_hours).count()
    week_loyalty = await User.filter(created_at__lt = last_7_days, last_interaction_at__gt = last_24_hours).count()
    
    


    message = """ آمار وفاداری کاربرانی که امروز از ربات استفاده کردند
    
🔰 کاربر تازه نفس: {} (توی 24 ساعت اخیر استارت زده و استفاده کرده از ربات)

🗓 کاربر برگشتی: {} (کاربری که قبل 24 ساعت اخیر بات رو استارت زده اما توی 24 ساعت اخیر هم به ربات برگشته)

📆 کاربر وفادار بیش از یک هفته: {}

📅 کاربر وفادار بیش از یک ماه: {}

🍗 کاربر وفادار بالای دو ماه: {}""".format(fresh_users, returning_user, week_loyalty, month_loyalty, two_months_loyalty)
    
    return message

