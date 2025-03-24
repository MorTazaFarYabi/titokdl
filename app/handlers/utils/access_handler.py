
import datetime
import time
from typing import Any, Coroutine, Optional, Tuple
from telegram import Update
from telegram._utils.defaultvalue import DEFAULT_TRUE
from telegram.ext import Application, BaseHandler, ChatJoinRequestHandler
from telegram.ext._utils.types import HandlerCallback
from telegram.ext._utils.types import CCT, ConversationDict, ConversationKey
from db.models import Settings, SubscriptionPlan, User, UserSubscriptionPlan
import re

from handlers.utils.user_info import UserFunctionalities
_CheckUpdateType = Tuple[object, ConversationKey, BaseHandler[Update, CCT], object]



class AccessHandler(BaseHandler):


    

    def __init__(self, handlers: dict, block = True):
        self.handlers = handlers
        self.roles = handlers.keys()
        self.block = block
        
    def check_update(self, update: object) -> bool | object | None:
         
        return True
    async def handle_update(  # type: ignore[override]
            self,
            update: Update,
            application: "Application[Any, CCT, Any, Any, Any, Any]",
            check_result,
            context: CCT,
        ) -> Optional[object]:        
        
        if not update:
            return
        
        # print(update)
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        # print(update_str)
        # /start command
        if check:=self.handlers['S'].check_update(update):
            return await self.handlers['S'].handle_update(update, application, check, context)

        # handling updates that have no attr effective_user
        handlers = self.handlers.get('UPDATE_WITH_NO_USERS', False)
        if not update.effective_user:
            if not handlers:
                return
            for candidate, filter in handlers:
                check = candidate.check_update(update)
                if check:
                  handler = candidate
                  return await handler.handle_update(update, application, check, context)
            return
        

        if (update.chat_join_request) or (update.chat_member and not update.my_chat_member):
            # user.is_from_accepter = True
            # context.application.create_task(
            #     user.save()
            # )
            user = None
            user_functionalities = None
            user_role = User.NORMAL_USER
        else:
            
            last_user_fetch = context.user_data.get('last_user_fetch')
            if not last_user_fetch or datetime.datetime.now(datetime.UTC) - last_user_fetch > datetime.timedelta(minutes=2):
            
                user_functionalities:UserFunctionalities = await UserFunctionalities.create(
                    tg_user= update.effective_user,
                    context= context
                    )
                
                context.user_data['last_user_fetch'] = datetime.datetime.now(datetime.UTC)
                context.user_data['user_functionalities'] = user_functionalities
            
            else:
                user_functionalities = context.user_data['user_functionalities']
            
            context.application.create_task(user_functionalities.update_last_interaction())
        
            user = user_functionalities.db_user
            user_role = user.role
            

        # if :
        #     print("chatmember handler instance")
        #     user.is_from_joining_a_chat= True
        #     context.application.create_task(
        #         user.save()
        #     )
        
        
        
        # if the update had no user associated with it
            


        
             
             
        if user_role not in self.roles:
            print(user_role)
            print("the user role has not handlers registered")
            return


        handlers = self.handlers[user_role] + self.handlers.get('SHARED_HANDLERS', [])
        handler = None
        for candidate, filter in handlers:
            check = candidate.check_update(update)
            #if filer_data:=filter(user.state) and check:

            if check:
                handler = candidate
                break
        
        
        if not handler:
            
            print("not matching handler found")
            print(self.handlers[user_role])
            # print(update)
            print(f"user role : {user_role}")
            print(update.effective_user)
            print(update)
            return
        

        
        context.bot_data['settings'] = await Settings.first()

        context.update({
            #user database object
            'UDO': user,
            # 'user_functionalities': user_functionalities,
            # filter_data
            'filter_data': None #filer_data,
            
        })

        

        

        return await handler.handle_update(update, application, check, context)
        

      