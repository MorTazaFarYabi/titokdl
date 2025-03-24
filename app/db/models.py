
import random
import string
from pydantic import BaseModel
from tortoise.models import Model
from tortoise import fields

from config import Config


# Sample User model
class User(Model):
    ROOT_USER = 'R'
    ADMIN_USER = 'A'
    SADEGH_ADMINS = 'P'
    NORMAL_USER = 'N'
    GROUP_ANONYMOUS_BOT = 'G'
    ROLE_CHOICES = [
        (ROOT_USER, 'Root'),
        (ADMIN_USER, 'Admin'),
        (NORMAL_USER, 'Normal'),
        (GROUP_ANONYMOUS_BOT, 'Normal'),
        (SADEGH_ADMINS, 'Sadegh Admins')
    ]

    id = fields.CharField(max_length=50, pk = True)
    first_name = fields.CharField(max_length=255)
    last_name = fields.CharField(max_length=255)
    is_bot = fields.BooleanField(default=False)
    
    state = fields.TextField(default = 'start')
    role = fields.CharField(max_length = 1, choices = ROLE_CHOICES, default = NORMAL_USER)
    

    created_at = fields.DatetimeField(auto_now_add=True)
    last_interaction_at = fields.DatetimeField(auto_now_add=True)

    has_blocked_the_bot = fields.BooleanField(default = False)
    has_started = fields.BooleanField(default = False)     # has the user been added into the database by /start or sth else

    is_from_accepter = fields.BooleanField(default=False)
    is_from_joining_a_chat = fields.BooleanField(default=False)


    # user_subscription_plan = fields.ReverseRelation["models.UserSubscriptionPlan"]

    # bot = fields.ManyToManyField(Bot, related_name = 'users')

class Bot(Model):

    class RateLimitForMessages(BaseModel):
        """
            unit: message(s) per second
        """
        private: int = 1

    class PydanticModelForSettings(BaseModel):
        is_bot_active:bool
        deep_link_prefix:str
        referral_link_prefix:str
        non_repetitive_message_interval_seconds:float
        # LIMIT_FOR_MESSAGES: RateLimitForMessages
    


    
    bot_token = fields.CharField(255, pk = True)
    bot_username = fields.CharField(max_length=100)
    created_at = fields.DatetimeField(auto_now_add=True)
    admin = fields.ForeignKeyField('models.User', on_delete = fields.CASCADE, default = None, null = True)

    settings:PydanticModelForSettings = fields.JSONField(decoder=PydanticModelForSettings.model_validate_json)
    

        

class Channel(Model):

    id = fields.CharField(max_length = 255, pk = True)
    title = fields.CharField(max_length = 255)
    created_at = fields.DatetimeField(auto_now_add=True)
    admin = fields.ForeignKeyField('models.User', on_delete = fields.CASCADE, default = None, null = True, related_name = "channels")
    is_bot_admin = fields.BooleanField(default = True)
    is_comment_active = fields.BooleanField(default =True)

    is_chatmember_tracking_active = fields.BooleanField(default=False)
    acceptor_message = fields.ForeignKeyField('models.Message', on_delete = fields.CASCADE, default = None, null = True)




class Group(Model):

    id = fields.CharField(max_length = 255, pk = True)
    title = fields.CharField(max_length = 255)
    created_at = fields.DatetimeField(auto_now_add=True)
    admin = fields.ForeignKeyField('models.User', on_delete = fields.CASCADE, default = None, null = True, related_name="groups")
    is_bot_admin = fields.BooleanField(default = True)
    is_comment_active = fields.BooleanField(default = True)

    
class Message(Model):

    class MEDIA_TYPES:
        IMAGE = "image"
        VIDEO = "video"
        GIF = "gif"
        AUDIO = "audio"
        DOCUMENT = "document"
        NONE = ""

    class REPLY_MARKUP_TYPES:
        INLINE = "I"


    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    is_forwarded = fields.BooleanField()
    telegram_message_id = fields.IntField(default = 0)
    origin_chat_id = fields.IntField(default = 0)

    # not forwarded
    media_type = fields.CharField(max_length=10, default = MEDIA_TYPES.NONE)
    media_url = fields.TextField(default = "")
    media_id = fields.TextField(default = "")

    text = fields.TextField() # text / caption
    parse_mode = fields.CharField(max_length=50, default = "")

    reply_markup_type = fields.CharField(max_length=1, default = REPLY_MARKUP_TYPES.INLINE)
    keyboard = fields.JSONField(default = "[]", null = True)
    entities = fields.JSONField(default = "[]", null = True)


class BroadCastRequest(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    message = fields.ForeignKeyField('models.Message', on_delete = fields.CASCADE)

    messages_per_second = fields.IntField()
    n_of_successfully_sent_messages = fields.IntField(default = 0) # only includes those who actually received the message
    n_of_users_already_covered = fields.IntField(default = 0) # it includes those who didn't receive the message because of errors
    n_of_users_to_be_sent_to = fields.IntField(default = 0) # 0 means to all the users 

    is_underway = fields.BooleanField(default=False)
    is_finished = fields.BooleanField(default=False)
    





class ChannelMembership(Model):
    """
        everytime sb join a channel an instance of this object will be inserted into the database
        we can track fakes members that join a channel in one period and then leave after that
        we can calculate how long users from a certain link stay in the channel
    """
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    JOINED_FROM_LINK = 'L'
    JOINED_FROM_ID = 'I'
    JOIN_FROM_UNKNOWN_SOURCE = 'N'
    JOINED_FROM_CHOICES = [
        (JOINED_FROM_LINK, 'link'),
        (JOINED_FROM_ID, 'id'),
        (JOIN_FROM_UNKNOWN_SOURCE, 'unknown')
    ]

    channel = fields.ForeignKeyField('models.Channel', on_delete = fields.CASCADE)
    user = fields.ForeignKeyField('models.User', on_delete = fields.CASCADE)

    joined_at = fields.DatetimeField(default = None, null = True)
    left_at = fields.DatetimeField(default = None, null = True)

    joined_from = fields.CharField(max_length = 10, choices = JOINED_FROM_CHOICES, default = JOINED_FROM_ID)
    joined_from_link = fields.CharField(max_length=100, default = None, null = True)





class ForcedJoinChannelOrder(Model):

    id = fields.IntField(pk = True)
    channel_id = fields.CharField(max_length = 255, default = "")
    created_at = fields.DatetimeField(auto_now_add=True)

    title = fields.CharField(max_length = 255)
    link = fields.CharField(max_length = 255)
    is_fake_force = fields.BooleanField(default=False)
    
    
    # their orders
    number_of_ordered_members = fields.IntField(default = 0) # if 0 the number is not tracked by bot and the order is fixed
    # if==True ==> I needed members have been forcejoined to the channel
    completion_status = fields.BooleanField(default=False)


class Settings(Model):

    id = fields.IntField(pk = True)
    max_forced_channels = fields.IntField(default= 3)
    default_language = fields.CharField(max_length=255, default= "fa")
    is_bot_active = fields.BooleanField(default=True)

    cache_times = fields.JSONField(default = {})

    
    



class MediaItem(Model):

    id = fields.IntField(pk = True)
    created_at = fields.DatetimeField(auto_now_add=True)
    published_at = fields.DatetimeField(auto_now_add=True)

    requester = fields.ManyToManyField('models.User', on_delete = fields.CASCADE, default = None, null = True) # on delete roo chi bezaram
    link = fields.TextField() # 500 mishe aslan?
    
    type = fields.CharField(max_length = 255) # vid, reels, story, etc..., user profile
    uploader_insta_account = fields.CharField(max_length = 255)  # change this to foreign key
    
    data_extracted_from_one_api = fields.TextField()
    
    
    # their existence in the forced join list is not restricted by the needed number/completion status
    # it should be set True for my own channel but false for orders


# class Settings(Model):

#     id = fields.IntField(pk = True)
#     max_forced_channels = fields.IntField(default= 3)
#     default_language = fields.CharField(max_length=255, default= "fa")
#     is_bot_active = fields.BooleanField(default=True)
    

    
# class MediaItem(Model):
#     id = fields.IntField(pk=True)
#     type = fields.CharField(max_length=10)  # "photo" or "video"
#     url = fields.TextField()  # Media URL
#     cover = fields.TextField(null=True)  # Optional cover image

#     post = fields.ForeignKeyField("models.InstagramPostResult", related_name="media")

class HdProfilePicInfo(Model):
    id = fields.IntField(pk=True)
    url = fields.TextField()  # HD profile picture URL

class InstagramAccount(Model):

    created_at = fields.DatetimeField(auto_now_add=True)  # Set only at creation
    updated_at = fields.DatetimeField(auto_now=True) 

    id = fields.CharField(pk=True, max_length=50)  # Instagram user ID (string)
    username = fields.CharField(max_length=60, unique=True)
    bio = fields.TextField(null=True)  # Nullable bio field
    full_name = fields.CharField(max_length=150, null=True)  # Full name (optional)
    type = fields.CharField(max_length=10)  # "Public" or "Private"
    profile = fields.TextField()  # Profile picture URL
    profile_hd = fields.TextField()  # HD profile picture URL
    posts = fields.IntField()  # Number of posts
    followers = fields.IntField()  # Number of followers
    following = fields.IntField()  # Number of following
    is_verified = fields.BooleanField()  # Verification status
    is_business = fields.BooleanField()  # Business account status


# class InstagramCon(Model):
#     id = fields.IntField(pk=True)
#     caption = fields.TextField(null=True)  # Optional caption
#     owner = fields.ForeignKeyField("models.Owner", related_name="posts")

# class InstagramPostResponse(Model):
#     id = fields.IntField(pk=True)
#     status = fields.IntField()  # API response status
#     result = fields.OneToOneField("models.InstagramPostResult", related_name="response")


class InstagramRequest(Model):
    # class REQUEST_TYPES:
        
    #     POST = "IP"
    #     REEL = "IR"
    #     USER = "IU"
    #     USER_STORY = "IUS"
    #     USER_STORIES = "IUSS"
    #     USER_HIGHLIGHT = "IUH"
    #     USER_HIGHLIGHTS = "IUHS"

    

    created_at = fields.DatetimeField(auto_now_add=True)

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(model_name='models.User', related_name='requests')

    request_type = fields.CharField(max_length=255)
    request_status = fields.IntField()
    
    parameters = fields.JSONField(default={})
    
    api_request = fields.ForeignKeyField('models.APIReq', on_delete = fields.CASCADE, related_name='bot_requests')


class APIReq(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    service_provider = fields.CharField(max_length=50)

    url = fields.TextField()
    parameters = fields.TextField()
    status = fields.IntField()
    response = fields.JSONField(default={})
    


class SubscriptionPlan(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    name = fields.CharField(max_length= 50)
    permitted_downloads = fields.JSONField()
    request_per_second_limit = fields.IntField()
    does_see_forced_joins = fields.BooleanField()
    default_plan = fields.BooleanField(default = False)

    


# class SubscriptionPlanOrderOptions(Model):
#     """ for example Gold SubscriptionPlan can have three SubscriptionPlanOrderOptions for 1 month 200 tuman 2 month 300 tuman"""
#     id = fields.IntField(pk=True)
#     created_at = fields.DatetimeField(auto_now_add=True)

#     subscription_plan = fields.ForeignKeyField(model_name="models.SubscriptionPlan", on_delete=fields.CASCADE, related_name="order_options")
#     duration_in_seconds = fields.IntField()
#     price_in_tumans = fields.IntField()

class UserSubscriptionPlan(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    ends_at = fields.DatetimeField()

    # what would I do if a subscription plan order option was deleted?
    subscription_plan = fields.ForeignKeyField(model_name="models.SubscriptionPlan", related_name="users_subscription_order")
    user = fields.OneToOneField(model_name="models.User", on_delete=fields.CASCADE, related_name="user_subscription_plan")

    async def can_download(self, content_type):
        return
        
    
    async def is_subscription_expired():
        return




class Referral(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    referrer = fields.ForeignKeyField(
        "models.User", 
        related_name="referrals_made", 
        on_delete=fields.CASCADE
    )
    referred = fields.OneToOneField(
        "models.User", 
        related_name="referred_by", 
        on_delete=fields.CASCADE
    )

class Source(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    # name = fields.CharField(max_length=100)
    def generate_random_string(length = 10) -> str:
    # Generates a random string of 10 letters
        return ''.join(random.choices(string.ascii_letters, k=length))

    identifier = fields.CharField(max_length=40, default = generate_random_string) # a string that identifies the source

class SourceClick(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    user = fields.ForeignKeyField(
        "models.User", 
        on_delete=fields.CASCADE
    )
    source = fields.ForeignKeyField(
        "models.Source", 
        related_name="clicks", 
        on_delete=fields.CASCADE
    )


class DynamicCommand(Model):

    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    command_name = fields.CharField(max_length=100) # without /: e.g. help -> /help
    messages = fields.ManyToManyField(
        "models.Message", 
        on_delete=fields.CASCADE
        )
    
    # later on I will add a feature that there are several predetermined funcions that each of the commands using this field can call
    extra_actions = fields.JSONField(default = [])
    

class UserBalance(Model):

    CURRENCY_TYPES = Config.CURRENCY_TYPES

    user = fields.OneToOneField(model_name='models.User', on_delete=fields.CASCADE, related_name="balance")
    gold_coin = fields.IntField(default = 500)
    gem = fields.IntField(default = 0)


class Transactions(Model):

    REASONS = Config.TRANSACTION_REASONS

    class TYPES:
        INCREASE = "I"
        DECREASE = "D"

    id = fields.IntField(pk=True)
    
    user = fields.ForeignKeyField(model_name='models.User', on_delete=fields.CASCADE)
    currency_type = fields.CharField(max_length=2)
    reason = fields.CharField(max_length=2)
    amount = fields.IntField()


class ForcedJoinRecord(Model):

    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    user = fields.ForeignKeyField(model_name='models.User', on_delete=fields.CASCADE)
    orders = fields.ManyToManyField(model_name='models.ForcedJoinChannelOrder', on_delete=fields.CASCADE)

    user_joined_in_all = fields.BooleanField(default= False)