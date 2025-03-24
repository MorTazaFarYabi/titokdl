
from datetime import UTC, datetime, timedelta
from math import ceil
from typing import List
from config import Config
from db.models import Referral, UserBalance, User as DBUser, SubscriptionPlan, UserSubscriptionPlan, Transactions, ForcedJoinRecord
from telegram import User as TGUser
from telegram.ext import ContextTypes
from tortoise.transactions import atomic


from pydantic import BaseModel as PydanticBaseModel

class Balance():

    currency = "coin"
    
    
    def __init__(self, user:DBUser, balance:UserBalance|None = None) -> None:
        self.user = user
        self.db_balance = balance

    @classmethod
    async def create(cls, user:DBUser, balance:UserBalance|None = None):

        instance = Balance(user=user, balance=balance)

        if not user.balance:
            balance = await cls.get_or_create_db_balance(user)
            instance.db_balance = balance
        else:
            instance.db_balance = user.balance
        
        
        return instance


    @staticmethod
    async def get_or_create_db_balance(user: DBUser):
        balance, _ = await UserBalance.get_or_create(user = user)
        return balance

    @staticmethod
    async def create_db_balance(user: DBUser):
        balance = UserBalance()
        balance.user = user
        await balance.save()
        return balance
    
    def convert_gem_to_gold_coin(self, gold_coin:int):

        gem_needed = ceil(gold_coin/Config.CURRENCY_TYPES.GEM_TO_COIN_RATIO)
        has_enough_gem = gem_needed <= self.db_balance.gem

        if not has_enough_gem:
            return False # nashod
        
        self.db_balance.gem -= gem_needed
        self.db_balance.gold_coin += gem_needed * Config.CURRENCY_TYPES.GEM_TO_COIN_RATIO
        
        return True


    @atomic()
    async def _do_transaction(
        self, 
        currency_type:str,
        reason:str,
        amount:int,
        direction: bool # whether or not the balance should be increase
    ):
        
        not_enough_balance = Exception('not enough balance')
        
        if direction == False:
            if not self.is_enough(currency_type=currency_type, amount=amount):
                if currency_type == UserBalance.CURRENCY_TYPES.GOLD_COIN:
                    if not self.convert_gem_to_gold_coin(gold_coin=amount):
                        raise not_enough_balance
                    else:
                        pass # convert was done now lets continue the transaction
                else:
                    raise not_enough_balance
            amount = 0-amount

        

        if currency_type == UserBalance.CURRENCY_TYPES.GEM:
            self.db_balance.gem += amount
        elif currency_type == UserBalance.CURRENCY_TYPES.GOLD_COIN:
            self.db_balance.gold_coin +=amount

        transaction = Transactions()
        transaction.user = self.user
        transaction.currency_type = currency_type
        transaction.reason = reason
        transaction.amount = amount

        
        s1= await transaction.save()
        s2= await self.db_balance.save()

        return s1 and s2

    
    async def increase(
        self, 
        currency_type: str,
        reason: str,
        amount: int
        ):

        return await self._do_transaction(currency_type,reason,amount, direction=True)

        

    async def decrease(
        self, 
        currency_type: str,
        reason: str,
        amount: int
        ):

        return await self._do_transaction(currency_type,reason,amount, direction=False)
        

    def is_enough(
            self,
            currency_type,
            amount
            ):
        
        if currency_type == UserBalance.CURRENCY_TYPES.GEM:
            currency_balance = self.db_balance.gem
        elif currency_type == UserBalance.CURRENCY_TYPES.GOLD_COIN:
            currency_balance = self.db_balance.gold_coin

        is_currency_enough = amount >= currency_balance

        return is_currency_enough
        


class Subscription():
    def __init__(
            self, 
            user: DBUser, 
            # user_subscription_plan:UserSubscriptionPlan | None, 
            # subscription_plan:SubscriptionPlan | None
            ) -> None:
        
        
        self.user = user
        self.db_subscription_plan = None
        self.db_user_subscription_plan = None

    
    @classmethod
    async def create(
        cls,
        user: DBUser, 
        # user_subscription_plan:UserSubscriptionPlan | None, 
        # subscription_plan:SubscriptionPlan | None
    ):

        instance = cls(user)#, user_subscription_plan, subscription_plan)
        
        subp:SubscriptionPlan = user.user_subscription_plan
        # usubp:UserSubscriptionPlan = user.user_subscription_plan.subscription_plan

        if not subp:
            user_subscription_plan, subscription_plan = await cls.create_db_subscription()
            instance.db_subscription_plan = subscription_plan
            instance.db_user_subscription_plan = user_subscription_plan

        return instance

    @staticmethod
    async def create_db_subscription(
        user: DBUser, 
        user_subscription_plan:UserSubscriptionPlan | None, 
        subscription_plan:SubscriptionPlan | None
    ):
        
        default_subscription_plan = subscription_plan
        if not default_subscription_plan:
            default_subscription_plan = await SubscriptionPlan.filter(default_plan=True).first()

        usp = UserSubscriptionPlan()
        usp.subscription_plan = default_subscription_plan
        usp.user = user
        usp.ends_at = datetime.now(tz=UTC) + timedelta(days=365000)

        return usp, default_subscription_plan
        
    
    async def change_to(self, subscription_plan_id):

        self.db_user_subscription_plan.subscription_plan_id = subscription_plan_id
        return await self.db_user_subscription_plan.save()
        

    def has_ended()-> bool:
        pass
    def allows_downloading(self, download_type)-> bool:

        return download_type in self.db_subscription_plan.permitted_downloads
        pass
    
    

    

class UserChannels():
    async def __init__(self) -> None:
        
    
        pass
    async def get_by_id(self) -> None:
        
    
        pass
    async def remove_by_id(self) -> None:
        pass

    async def activate_member_tracking_by_id(self, id:str):
        pass


class ForcedJoinInfo():


    

    def __init__(
            self,
            db_user:DBUser
            ) -> None:
        
            self.user = db_user
            self.join_orders = None
            self.last_force_join_record = None
    
    @classmethod
    async def create(cls, db_user:DBUser):

        instance = cls(db_user)
        
        instance.join_orders = await ForcedJoinRecord.filter(user_id = db_user.id).limit(10).prefetch_related('orders')
        if instance.join_orders:
            instance.last_force_join_record = instance.join_orders[-1]
        else:
            instance.last_force_join_record = None

        return instance
        
    async def has_been_forced(self, in_the_last_x_hours = 24) -> bool:
        
        now = datetime.now(tz=UTC)
        x_hours_ago = now - timedelta(hours=in_the_last_x_hours)

        has_or_not:bool = self.last_force_join_record.created_at >= x_hours_ago
        
        return has_or_not and self.last_force_join_record.user_joined_in_all

    async def user_joined_in_all(self):
        
        self.last_force_join_record.user_joined_in_all = True
        return await self.last_force_join_record.save()


class ReferralManager():

    def __init__(self, db_user) -> None:
        self.db_user = db_user
            
    async def get_referrals_count(self):
        return await Referral.filter(referrer = self.db_user).count()

class UsageHistoryRecordPydantic(PydanticBaseModel):
    id:int
    date: datetime
    details: list | dict

class UsageHistoryPydantic(PydanticBaseModel):
    records : List[UsageHistoryRecordPydantic] | list

    

class UserActivity():

    def __init__(
        self, 
        db_user: DBUser, 
        user_data: dict,

        # usage_history_model: PydanticBaseModel
        ) -> None:
        
        self.db_user = db_user
        self.previous_interaction = db_user.last_interaction_at
        
        # usage_history = user_data.get('usage_history')
        # if usage_history:
        #     self.usage_history = usage_history_model(**usage_history)
        # else:
        #     self.usage_history = None
        
        
    def is_this_todays_first_interaction(self):
       todays_start = datetime.now(Config.TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
       return self.previous_interaction < todays_start
    
    def is_limited() -> bool:

        return

class UserFunctionalities():

    """
        uses lazy loading + @property to load the data about a user that is needed
    
    
    """
    def __init__(
            self,
            context: ContextTypes.DEFAULT_TYPE,
            tg_user:TGUser = None,
            db_user:DBUser = None,

            ) -> None:
        
        self.db_user = db_user
        self.tg_user = tg_user
        self.context = context
        self.balance_manager = None
        self.subscription_manager = None
        self.activity_manager = None
        self.forced_join_manager = None
        self.is_limited = None     

        self.is_a_new_comer = False
        # self.has_just_started = False

    @classmethod
    async def create(
        cls,
        context: ContextTypes.DEFAULT_TYPE,
        tg_user: TGUser = None,
        db_user: DBUser = None,

        newly_created = False
    ):

        balance = None
        subp = None
        usubp = None

        if not tg_user and not db_user:
            raise Exception("either DB_user or TG_user must be provided for UserFunctionalities class")

        if not db_user:
            db_user, newly_created = await cls.get_or_create_db_user(tg_user)


        instance = cls(db_user=db_user, context=context)
        instance.is_a_new_comer = newly_created
        await instance._initialize_managers()

        return instance

    async def _initialize_managers(self):

        """
            >>>>>>> use lazy loading using @property to get the following properties of a user
            Ask chatgpt for info about it
        """
        db_user = self.db_user

        # subp:SubscriptionPlan = db_user.user_subscription_plan
        # usubp:UserSubscriptionPlan = db_user.user_subscription_plan.subscription_plan
        # balance:UserBalance = db_user.balance

        self.balance_manager:Balance = await Balance.create(
            user=db_user,
            # balance=balance,
            )
        self.subscription_manager:Subscription = await Subscription.create(
            user=db_user,
            # subscription_plan=subp,
            # user_subscription_plan=usubp

            )
        
        

        # self.is_limited = self.activity_manager.is_limited()

        self.activity_manager = UserActivity(
            db_user=db_user,
            user_data= self.context.user_data
        )


        # self.channels = UserChannels()
        # self.channel = ""
        self.forced_join_manager:ForcedJoinInfo = await ForcedJoinInfo.create(db_user=db_user)
        self.referral_manager:ReferralManager = ReferralManager(db_user=db_user)
        # pass
        
    # async def get_balance_manager(self) -> Balance:

    #     if not self._balance:
    #         self._balance = await Balance(user=self.db_user)

    #     return self._balance
    
    
    # async def get_subscription_manager(self) -> Balance:

    #     if not self._subscription:
    #         self._subscription = await Subscription(user=self.db_user)

    #     return self._subscription
        

    # @property
    # def activity_manager(self):

    #     if self.activity_manager is None:
    #         raise Exception("activity manager is not property initialized. use get_activity_manager()")

    #     return self.activity_manager

    # async def get_activity_manager(self, ):
    #     self.activity_manager = UserActivity()

    @staticmethod
    async def get_db_user(tg_user:TGUser = None, user_id = None):


        if not tg_user and not user_id:
            raise Exception("at least one argument should be provided")
        
        if tg_user:
            user_id = tg_user.id

        db_user = await DBUser.filter(id = user_id).prefetch_related('balance').first()

        if not db_user:
            return db_user
        
        await db_user.fetch_related('user_subscription_plan__subscription_plan')
        return db_user

    @staticmethod
    async def get_or_create_db_user(
        tg_user: TGUser, 
        has_started = False, 
        is_from_accepter = False,
        is_from_joining_a_chat = False
    ):
        
        
        db_user = await UserFunctionalities.get_db_user(tg_user=tg_user)
        newly_created = False

        if db_user:
            return db_user, newly_created

        newly_created = True
        create_new_db_user = await UserFunctionalities.create_db_user(
            tg_user, 
            has_started, 
            is_from_accepter,
            is_from_joining_a_chat
        )
        
        

        return create_new_db_user, newly_created


    @atomic()
    @staticmethod
    async def create_db_user(
        tg_user: TGUser, 
        has_started = False, 
        is_from_accepter = False,
        is_from_joining_a_chat = False
        ) -> DBUser:
        ef = tg_user
        
        user = DBUser(
                id=ef.id,
                first_name=ef.first_name,
                last_name=ef.last_name or '',
                is_bot=ef.is_bot,
                state='',
                is_from_joining_a_chat = is_from_joining_a_chat,
                has_started=has_started,
                is_from_accepter = is_from_accepter,
                role=(
                    DBUser.ADMIN_USER if UserFunctionalities.is_admin(ef)
                    else DBUser.GROUP_ANONYMOUS_BOT if (ef.is_bot and ef.username == "GroupAnonymousBot")
                    else DBUser.NORMAL_USER
                )
            )
        await user.save()


        default_subscription_plan = await SubscriptionPlan.filter(default_plan=True).first()
        usp = UserSubscriptionPlan(
                ends_at=datetime.now(UTC) + timedelta(days=36500),
                user=user,
                subscription_plan=default_subscription_plan
        )
        await usp.save()

        ubalance = UserBalance()
        ubalance.user = user
        ubalance.gold_coin = Config.TRANSACTION_AMOUNTS.START_GIFT_COINS
        ubalance.gem = Config.TRANSACTION_AMOUNTS.START_GIFT_GEMS
        await ubalance.save()

        user = await UserFunctionalities.get_db_user(tg_user=tg_user)
        return user
    
    @staticmethod
    async def get_or_create_user_in_db_for_start(tg_user:TGUser):

        return await UserFunctionalities.get_or_create_db_user(
            tg_user = tg_user,
            has_started = True
        )
    
    @staticmethod
    async def get_or_create_user_in_db_for_accepter(tg_user:TGUser):
        return await UserFunctionalities.get_or_create_db_user(
            is_from_accepter = True,
            tg_user = tg_user,
        )
    
    @staticmethod
    async def get_or_create_user_in_db_for_user_joined_chat(tg_user:TGUser):
        return await UserFunctionalities.get_or_create_db_user(
            is_from_joining_a_chat = True,
            tg_user = tg_user,
        )
    
    @staticmethod
    async def tg_user_exists_in_db(tg_user:TGUser):
        return await DBUser.filter(id = tg_user.id).exists()


    @staticmethod
    def is_admin(tg_user:TGUser = None, user_id:int|str = ''):

        if not tg_user and not user_id:
            raise Exception('at least one of the arguments should be provided')
        
        user_id = user_id if user_id else tg_user.id

        return str(user_id) in Config.admins

    async def update_last_interaction(self):

        user = self.db_user
        user.last_interaction_at = datetime.now(UTC)
        await user.save()

# ufuncs = UserFunctionalities()
# ufuncs.balance_manager.increase(
#     currency_type= UserBalance.CURRENCY_TYPES.GOLD_COIN,
#     reason=Transactions.REASONS.INSTAGRAM_DOWNLOAD,
#     amount=50
# )
# uinfo.channels.activate_member_tracking_by_id(id = "243452344")
# uinfo.subscription.change_to()
# uinfo.forced_join_info.has_been_forced(in_the_last_x_hours=24)
# uinfo.subscription.db_subscription_plan.permitted_downloads
    
