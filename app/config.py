
import os
from typing import List
from zoneinfo import ZoneInfo

from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

DB_URL = os.getenv("DB_URL")
#DB_URL = "postgres://postgres:GQU9rp3u46RAjfVm@services.gen4.chabokan.net/jewell"
# DB_URL = "postgres://konkury3_morteza:Pr(^5Nar(Nyc@127.0.0.200:5432/konkury3_zcy"


class Config():
    # DB_URL = 'sqlite://db.sqlite3'

    
    FILE_SAVE_FOLDER = "files/"

    HTTPX_READ_TIMEOUT_SECONDS = 30 # it was 10
    HTTPX_CONNECTION_POOL_SIZE = 256 #30
    BOT_CONCURRENT_UPDATE_MANAGEMENT = 30
    
    

    DB_URL = os.getenv("DB_URL")
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    FASTSAVERAPI_TOKEN = os.getenv("FASTSAVERAPI_TOKEN")
    ONE_API_TOKEN = os.getenv("ONE_API_TOKEN")
    INSTA_SCRAPER_TOKEN = "51e96c4a35msheec2211603aabb8p18128fjsnae2ea43bd9e0"
    
    IN_PRODUCTION = True if os.getenv("IN_PRODUCTION")=="True" else False
    # DB_URL = "postgres://postgres:admin@localhost:5432/instagramdownloader"
    # DB_URL = "postgres://konkury3_morteza:Pr(^5Nar(Nyc@127.0.0.200:5432/konkury3_zcy"

    admins = os.getenv("ADMINS").split('|') # [ "357686176", "1829296015"]
    REPORTS_CHANNEL = os.getenv("REPORTS_CHANNEL")
    MAJOR_ERRORS_CHANNEL = os.getenv("MAJOR_ERRORS_CHANNEL")
    MINOR_ERRORS_CHANNEL = os.getenv("MINOR_ERRORS_CHANNEL")
    MEDIA_BANK_CHANNEL = os.getenv("MEDIA_BANK_CHANNEL")
    FINANCE_CHANNEL = "-1002560504280"

    SOURCE_DEEP_LINK_PREFIX = "DLSS_"
    REFERRAL_DEEP_LINK_PREFIX = "RL_"
    GIFT_DEEP_LINK_PREFIX = "GIFT_"
    

    INSTAGRAM_REQUEST_LINK_REGEX = r"https?://(?:www\.)?instagram\.com/(:?share)?(p|reels?|share|stories|s|stories/highlights|[A-Za-z0-9_.-]+)/?(?:([0-9]+))?/?"

    TIKTOK_REQUEST_LINK_REGEX = r"https?:\/\/(www\.)?(vm\.)?tiktok\.com\/[\w@./%-]+"


    class SERVICE_PROVIDERS:
        ONEAPI = "one_api"
        FASTSAVERAPI = "fastsaverapi"
        INSTASCRAPERAPI = "instascraperapi"
        TIMWM = "tikwm"

    class INSTAGRAM_SUBLINKS:
        STORY = ('stories/')
        POST  = ('p/')
        REEL  = ('reel/', 'reels/') # they are interchangable
        HIGHLIGHT = ('s/', '')
        SHARE = ('share/')

    class INSTAGRAM_REUQEST_TYPES:
        STORY = 'story'
        STORIES = 'stories'
        POST = 'post'
        POSTS = 'posts'
        REEL = 'reel'
        HIGHLIGHT_STORIES = 'highlight'
        USER_HIGHLIGHTS = 'highlights'
        USER_INFO = 'user'
        TV = 'tv'
        JUST_SHARE = "just_share"
        AUDIO = "reel_audio"

    # USED FOR RECREATING ADDRESSES FROM ID/USERNAME OF A REQUEST E.G. IN CALLBACK QUERIES
    INSTAGRAM_BASE_URL_PATTERNS = {
        INSTAGRAM_REUQEST_TYPES.POST: "https://instagram.com/p/{}",
        INSTAGRAM_REUQEST_TYPES.REEL: "https://instagram.com/reel/{}",
        INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES: "https://instagram.com/stories/highlights/{}",
        INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS: "highlights user id:{}",
        INSTAGRAM_REUQEST_TYPES.STORY: "https://instagram.com/stories/{}/{}",
        INSTAGRAM_REUQEST_TYPES.STORIES: "https://instagram.com/stories/{}",
        INSTAGRAM_REUQEST_TYPES.USER_INFO: "https://instagram.com/{}",
        INSTAGRAM_REUQEST_TYPES.TV: "https://instagram.com/tv/{}",
        INSTAGRAM_REUQEST_TYPES.JUST_SHARE: "https://instagram.com/share/{}",
        INSTAGRAM_REUQEST_TYPES.AUDIO: "https://instagram.com/reels/audio/{}",
    }

    class TIKTOK_REQUEST_TYPES:
        PROFILE = "tprofile"
        VIDEO = "tvideo"
        VIDEO_SHORT_LINK1 = "tvidSL1"
        VIDEO_SHORT_LINK2 = "tvidSL2"

    TIKTOK_BASE_URL_PATTERNS = {
        TIKTOK_REQUEST_TYPES.PROFILE: "https://www.tiktok.com/{}",
        TIKTOK_REQUEST_TYPES.VIDEO: "https://www.tiktok.com/{}/video/{}",
        TIKTOK_REQUEST_TYPES.VIDEO_SHORT_LINK1: "https://www.tiktok.com/t/{}",
        TIKTOK_REQUEST_TYPES.VIDEO_SHORT_LINK2: "https://www.tiktok.com/t/{}",
    }
    
    TIKTOK_REGEX_PATTERNS = {
        TIKTOK_REQUEST_TYPES.VIDEO: r"https?:\/\/(?:www\.)?tiktok\.com\/(@[\w.-]+)\/video\/(\d+)(?:\?[\w&%=.-]+)?",
        TIKTOK_REQUEST_TYPES.VIDEO_SHORT_LINK1: r"https?:\/\/(?:www\.)?tiktok\.com\/t\/([\w\d]+)(?:\?[\w&%=.-]+)?",
        TIKTOK_REQUEST_TYPES.VIDEO_SHORT_LINK2: r"https?:(?:www\.)?\/\/vm\.tiktok\.com\/([\w\d]+)(?:\?[\w&%=.-]+)?"
    }

    INSTAGRAM_REGEX_PATTERNS = {
        "share": r"https?://(?:www\.)?instagram\.com/share/(p|reels?)/([A-Za-z0-9_.-]+)/?(?:\?.*)?$",

        INSTAGRAM_REUQEST_TYPES.POST: r"https?://(?:www\.)?instagram\.com/(?:[A-Za-z0-9_-]+/)?p/([A-Za-z0-9_-]+)/?(?:\?.*)?",
        INSTAGRAM_REUQEST_TYPES.AUDIO:r"https?://(?:www\.)?instagram\.com/reels/audio/([A-Za-z0-9_:\-]+)/?(?:\?.*)?",
        INSTAGRAM_REUQEST_TYPES.REEL: r"https?://(?:www\.)?instagram\.com/(?:[A-Za-z0-9_-]+/)?reels?/([A-Za-z0-9_-]+)/?(?:\?.*)?",
        INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES:r"https?://(?:www\.)?instagram\.com/(?:s|stories/highlights)/([A-Za-z0-9_:\-]+)/?(?:\?.*)?",
        INSTAGRAM_REUQEST_TYPES.STORY: r"https?://(?:www\.)?instagram\.com/stories/([A-Za-z0-9_.-]+)/([0-9]+)/?(?:\?.*)?",
        INSTAGRAM_REUQEST_TYPES.STORIES: r"https?://(?:www\.)?instagram\.com/stories/([A-Za-z0-9_.-]+)/?(?:\?.*)?",  # No story ID
        INSTAGRAM_REUQEST_TYPES.USER_INFO: r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.-]+)/?(?:\?.*)?$",
        INSTAGRAM_REUQEST_TYPES.TV: r"https?://(?:www\.)?instagram\.com/tv/([A-Za-z0-9_.-]+)/?(?:\?.*)?$",
        INSTAGRAM_REUQEST_TYPES.JUST_SHARE: r"https?://(?:www\.)?instagram\.com/share/([A-Za-z0-9_.-]+)/?(?:\?.*)?$",

        

        #fake regex (not a real type -> gets converted into others)
        
    }

    # PREFERED_SERVICE_PROVIDERS:dict[str, list] = {
    #     INSTAGRAM_REUQEST_TYPES.POST: [SERVICE_PROVIDERS.ONEAPI, SERVICE_PROVIDERS.FASTSAVERAPI],
    #     INSTAGRAM_REUQEST_TYPES.REEL: [SERVICE_PROVIDERS.ONEAPI, SERVICE_PROVIDERS.FASTSAVERAPI],
    #     INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES: [SERVICE_PROVIDERS.FASTSAVERAPI, SERVICE_PROVIDERS.ONEAPI],
    #     INSTAGRAM_REUQEST_TYPES.STORY: [],
    #     INSTAGRAM_REUQEST_TYPES.STORIES: [SERVICE_PROVIDERS.ONEAPI, SERVICE_PROVIDERS.FASTSAVERAPI],  # No story ID
    #     INSTAGRAM_REUQEST_TYPES.USER_INFO: [SERVICE_PROVIDERS.ONEAPI, SERVICE_PROVIDERS.FASTSAVERAPI],
    #     INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS: [SERVICE_PROVIDERS.ONEAPI],

    #     #fake regex (not a real type -> gets converted into others)
    #     "share": [SERVICE_PROVIDERS.FASTSAVERAPI]
    # }
    PREFERED_SERVICE_PROVIDERS:dict[str, list] = {
        INSTAGRAM_REUQEST_TYPES.POST: [SERVICE_PROVIDERS.FASTSAVERAPI, SERVICE_PROVIDERS.ONEAPI],
        INSTAGRAM_REUQEST_TYPES.REEL: [SERVICE_PROVIDERS.FASTSAVERAPI, SERVICE_PROVIDERS.ONEAPI],
        INSTAGRAM_REUQEST_TYPES.TV: [SERVICE_PROVIDERS.FASTSAVERAPI,],
        INSTAGRAM_REUQEST_TYPES.JUST_SHARE: [SERVICE_PROVIDERS.FASTSAVERAPI,],

        INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES: [SERVICE_PROVIDERS.FASTSAVERAPI, SERVICE_PROVIDERS.ONEAPI],
        INSTAGRAM_REUQEST_TYPES.STORIES: [SERVICE_PROVIDERS.FASTSAVERAPI, SERVICE_PROVIDERS.ONEAPI],  # No story ID
        INSTAGRAM_REUQEST_TYPES.STORY: [SERVICE_PROVIDERS.FASTSAVERAPI],

        INSTAGRAM_REUQEST_TYPES.USER_INFO: [SERVICE_PROVIDERS.ONEAPI],
        INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS: [SERVICE_PROVIDERS.ONEAPI],
        
        INSTAGRAM_REUQEST_TYPES.AUDIO: [SERVICE_PROVIDERS.INSTASCRAPERAPI],

        #fake regex (not a real type -> gets converted into others)
        "share": [SERVICE_PROVIDERS.FASTSAVERAPI],


        TIKTOK_REQUEST_TYPES.VIDEO: [SERVICE_PROVIDERS.TIMWM, SERVICE_PROVIDERS.FASTSAVERAPI],
        TIKTOK_REQUEST_TYPES.VIDEO_SHORT_LINK1: [SERVICE_PROVIDERS.TIMWM, SERVICE_PROVIDERS.FASTSAVERAPI],
        TIKTOK_REQUEST_TYPES.VIDEO_SHORT_LINK2: [SERVICE_PROVIDERS.TIMWM, SERVICE_PROVIDERS.FASTSAVERAPI],
    }
    INSTAGRAM_USERNAME_REGEX =  r'^@(?=.{1,30}$)(?![_.])(?!.*[_.]{2})[A-Za-z0-9._]+(?<![_.])$'


    #INSTAGRAM CACHE TIME IN SECONDS
    CACHE_ACTIVE = False
    CACHE_TIME = {
        INSTAGRAM_REUQEST_TYPES.STORY: 600,
        INSTAGRAM_REUQEST_TYPES.STORIES: 600,
        INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES: 86400,
        INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS: 86400,
        INSTAGRAM_REUQEST_TYPES.POST: 31536000,
        INSTAGRAM_REUQEST_TYPES.REEL: 31536000,
        INSTAGRAM_REUQEST_TYPES.USER_INFO: 86400,
        INSTAGRAM_REUQEST_TYPES.TV: 31536000,
        INSTAGRAM_REUQEST_TYPES.JUST_SHARE: 31536000,
        INSTAGRAM_REUQEST_TYPES.AUDIO: 31536000,
    }

    INSTAGRAM_BASE_URL = "https://www.instagram.com/"


    class ERRORS:
        class API:
            SUCCESS = 200

        class SENDING_MESSAGE:
            TOO_MANY_TRIES = "TMT"
            FORBIDDEN = "FORBIDDEN"
            NO_MEDIA = "NOMEDIA"
            PROBLEMATIC_LINK_OR_INABILITY_TO_CHECK_SIZE = "PLOATCS"
            UNKNOWN_ERROR = "UNKNOWN_ERROR"
            


    class CURRENCY_TYPES:
        GEM = "G"
        GOLD_COIN = "C"

        GEM_TO_COIN_RATIO = 30

    class TRANSACTION_REASONS:
        INSTAGRAM_DOWNLOAD = "I"
        REFERRAL = "R"
        LOYALTY_GIFT = "L"
        GIFT = "G"

    class TRANSACTION_AMOUNTS:
        LOYALTY_GIFT_COINS = 200
        
        START_GIFT_COINS = 400
        START_GIFT_GEMS = 10

        GIFT_BTN_COINS = 600
        INSTAGRAM_REQUEST_COINS = 50
        REFERRAL_GIFT = 1000

    TIMEZONE = ZoneInfo("Asia/Tehran")
    
    class CALENDAR:
        JALALI = "jalali"
        GEORGIAN = "georgian"


    class SubscriptionPlanTimes:
        """IN SECONDS"""
        ONE_MONTH = 86400 * 30
        TWO_MONTHS = 86400 * 60
        THREE_MONTHS = 86400 * 90
        
        INFINITE = 3155695200 # 100 years

    TIME_LIMIT_OPTIONS_FOR_SUBSCRIPTIONS = [0,5,10,15,30,45,60]

    DEFAULT_CAPTION = "@instafiler_bot"

    class REQ_STATUS:
        SUCCESS = 200

    MAX_RECURSION_TRIES = 3
    # MAX_LENGTH_FOR_CAPTION = 1000 # in fact 1024 characters

    class TELEGRAM_LIMIT_FOR_SENDING_MESSAGES:
        PRIVATE = 1 # 1 MESSAGE PER SECOND


    

class DEFAULT_DB_RECORDS:
    class DEFAULT_SUBSCRIPTION_PLAN:
        """this is used in bot_installer.py to create the default subscription plan in the database when the bot is installed"""
        PERMITTED_DOWNLOADS = [
            Config.INSTAGRAM_REUQEST_TYPES.STORY,
            Config.INSTAGRAM_REUQEST_TYPES.STORIES,
            Config.INSTAGRAM_REUQEST_TYPES.POST,
            Config.INSTAGRAM_REUQEST_TYPES.POSTS,
            Config.INSTAGRAM_REUQEST_TYPES.REEL,
            Config.INSTAGRAM_REUQEST_TYPES.HIGHLIGHT_STORIES,
            Config.INSTAGRAM_REUQEST_TYPES.USER_HIGHLIGHTS,
            Config.INSTAGRAM_REUQEST_TYPES.USER_INFO,
            Config.INSTAGRAM_REUQEST_TYPES.TV,
            Config.INSTAGRAM_REUQEST_TYPES.JUST_SHARE,
            Config.INSTAGRAM_REUQEST_TYPES.AUDIO,
        ]





TORTOISE_ORM = {
    "connections": {
        "default": Config.DB_URL,  # Your DB URL
    },
    "apps": {
        "models": {
            "models": ["db.models", "aerich.models"],  # Your models module
            "default_connection": "default",
        },
    },
}

