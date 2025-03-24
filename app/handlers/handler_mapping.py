

from telegram.ext import Application, filters
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler, 
    ChatMemberHandler, ConversationHandler, ChatJoinRequestHandler
    )

from config import Config
from handlers.accepter import accepter_handler
from handlers.constants.callback_data import CD
from handlers.constants.conversations import CONV, SUBP
from handlers.user_membership_in_chats import track_chat_members
from handlers.utils.access_handler import AccessHandler
from handlers.utils.state_filter import StateFilter

from handlers.core import start, error_handler, there_is_no_such_command
from handlers.bot_membership import track_bot_membership
from handlers.callback_query import callback_query_handler
from handlers.others import instagram_downloader, this_bot_doesnt_support_edited_txts, my_balance, referral_info

from handlers.admin_panel_handlers import (
    add_the_new_msg_to_db, admin_stats, broadcast_management, channel_management, forced_join_control, 
    get_back_to_admin_panel_main_page, 
    is_auto_generated_link, message_management, send_forced_channel_info,
    list_forced_channels_orders,
    is_order_fake_link, set_btn_type, set_order_tracking_type, set_order_type_get_title, 
    set_order_title, set_order_link, set_order_channel_info, source_link_management,
    command_management, add_the_new_command_to_db,
    set_btn_title, set_btn_link,
    create_channel_in_db
    )

from handlers.subscription import (
    subscription_pannel, 
    Subscription_plan_control, adding_subscription_plan, set_name_for_subscription_plan,
    Subscription_plan_list, set_subscription_plan_name)

from handlers.p_specific.tiktokdownloader import TiktokDownloader

from handlers.dynamic_command import dynamic_command

from handlers.constants.buttons import BTN
from db.models import User
from telegram import Update
from telegram.ext import ContextTypes



def set_handlers(application: Application):
    application.add_handler(AccessHandler({
        'S': CommandHandler("start", start, filters=filters.ChatType.PRIVATE),

        User.ROOT_USER:[],
        User.ADMIN_USER:[            
            # buttons
            ## adding a forced join link

            
            

            [ConversationHandler(
                entry_points=[MessageHandler(filters.Text(BTN.AP_ADD_FORCED_CHANNEL), is_order_fake_link)],
                states={
                    
                    CONV.GET_ORDER_TYPE: [MessageHandler(None, set_order_type_get_title)],
                    CONV.GET_ORDER_TITLE: [MessageHandler(None, set_order_title)],
                    # send_forced_channel_info
                    
                    CONV.GET_ORDER_LINK: [MessageHandler(None, set_order_link)],
                    CONV.GET_ORDER_MEMBER_TRAKING_TYPE: [MessageHandler(None, set_order_tracking_type)],
                    CONV.SET_CHANNEL_INFO:[MessageHandler(None, set_order_channel_info)],
                    CONV.IS_AUTO_GENERATED_LINK:[MessageHandler(None, is_auto_generated_link)],
                },
                fallbacks=[CallbackQueryHandler(callback_query_handler, pattern=f"^{CD.CANCEL_CONV}$")],
            ), StateFilter.ALL],

            ## adding a forced join link
            [MessageHandler(filters.Text(BTN.AS_SEND_TO_ALL), broadcast_management), StateFilter.ALL],
            # [ConversationHandler(
                    

            #     entry_points=[MessageHandler(filters.Text(BTN.AS_SEND_TO_ALL), broadcast)],
            #     states={
            #         CONV.CHOOSE_MESSAGE_ID: [MessageHandler(None, broadcast)],
            #         CONV.GET_RATE: [MessageHandler(None, set_order_type_get_title)],
            #         CONV.USERS_TO_BE_SENT_TO: [MessageHandler(None, set_order_type_get_title)],
            #         # CONV.GET_ORDER_TITLE: [MessageHandler(None, set_order_title)],
            #         # # send_forced_channel_info
                    
            #         # CONV.GET_ORDER_LINK: [MessageHandler(None, set_order_link)],
            #         # CONV.GET_ORDER_MEMBER_TRAKING_TYPE: [MessageHandler(None, set_order_tracking_type)],
            #         # CONV.SET_CHANNEL_INFO:[MessageHandler(None, set_order_channel_info)],
            #         # CONV.IS_AUTO_GENERATED_LINK:[MessageHandler(None, is_auto_generated_link)],
            #     },
            #     fallbacks=[CommandHandler("Cancel", start)],
            # ), StateFilter.ALL],

            [ConversationHandler(
                entry_points=[CallbackQueryHandler(callback_query_handler, pattern= f"^{CD.NEW_BTN}")],
                states={
                    CONV.SET_BTN_TITLE: [MessageHandler(None, set_btn_title)],
                    CONV.SET_BTN_TYPE: [MessageHandler(None, set_btn_type)],
                    CONV.SET_BTN_LINK: [MessageHandler(None, set_btn_link)],
                },
                fallbacks=[CommandHandler("Cancel", start)],
            ), StateFilter.ALL],

            [ConversationHandler(
                entry_points=[CallbackQueryHandler(callback_query_handler, pattern= f"^{CD.ADD_CHANNEL}$")],
                states={
                    CONV.GET_CHANNEL_MSG: [MessageHandler(None, create_channel_in_db)],
                },
                fallbacks=[CommandHandler("Cancel", start)],
            ), StateFilter.ALL],
            ## adding a forced join link
            [ConversationHandler(
                    

                entry_points=[CallbackQueryHandler(callback_query_handler, pattern= f"^{CD.ADDING_NEW_MESSAGE}$")],
                states={
                    CONV.GETTING_A_NEW_MESSAGE: [MessageHandler(None, add_the_new_msg_to_db)],
                    # CONV.GET_RATE: [MessageHandler(None, set_order_type_get_title)],
                    # CONV.USERS_TO_BE_SENT_TO: [MessageHandler(None, set_order_type_get_title)],
                    # CONV.GET_ORDER_TITLE: [MessageHandler(None, set_order_title)],
                    # # send_forced_channel_info
                    
                    # CONV.GET_ORDER_LINK: [MessageHandler(None, set_order_link)],
                    # CONV.GET_ORDER_MEMBER_TRAKING_TYPE: [MessageHandler(None, set_order_tracking_type)],
                    # CONV.SET_CHANNEL_INFO:[MessageHandler(None, set_order_channel_info)],
                    # CONV.IS_AUTO_GENERATED_LINK:[MessageHandler(None, is_auto_generated_link)],
                },
                fallbacks=[CommandHandler("Cancel", start)],
            ), StateFilter.ALL],

            [ConversationHandler(
                entry_points=[CallbackQueryHandler(callback_query_handler, pattern= f"^{CD.ADDING_NEW_COMMAND}$")],
                states={
                    CONV.GETTING_A_NEW_COMMAND: [MessageHandler(None, add_the_new_command_to_db)],
                },
                fallbacks=[CommandHandler("Cancel", start)],
            ), StateFilter.ALL],

            

            [MessageHandler(filters.Text(BTN.AS_MESSAGE_MANAGEMENT), message_management), StateFilter.ALL],
            # [MessageHandler(filters.Text(BTN.AP_ADD_FORCED_CHANNEL), get_order_info), StateFilter.ALL],
            [MessageHandler(filters.Text(BTN.AS_STATS), admin_stats), StateFilter.ALL],
            [MessageHandler(filters.Text(BTN.AS_FORCED_JOIN), forced_join_control), StateFilter.ALL],

            [MessageHandler(filters.Text(BTN.AS_SOURCE_LINK), source_link_management), StateFilter.ALL],
            [MessageHandler(filters.Text(BTN.AS_COMMAND_MANAGEMENT), command_management), StateFilter.ALL],
            [MessageHandler(filters.Text(BTN.AS_CHANNEL_MANAGEMENT), channel_management), StateFilter.ALL],
            
            
            
            [MessageHandler(filters.Text(BTN.AP_LIST_FORCED_CHANNELS), list_forced_channels_orders), StateFilter.ALL],
            [MessageHandler(filters.Text(BTN.AP_GET_BACK_TO_START_PAGE_OF_ADMIN_PANNEL), get_back_to_admin_panel_main_page), StateFilter.ALL],
            [MessageHandler(filters.Text(BTN.AS_MEMBERSHIP_CONTROL), subscription_pannel), StateFilter.ALL],
            [MessageHandler(filters.Text(BTN.AP_SUBSCRIPTION_PLAN_CONTROL), Subscription_plan_control), StateFilter.ALL],

            [CommandHandler("set_subscription_plan_name", set_subscription_plan_name), StateFilter.ALL],
            
            ## adding a subscription plan
            [ConversationHandler(
                entry_points=[MessageHandler(filters.Text(BTN.AP_SUBSCRIPTION_PLAN_ADD), adding_subscription_plan)],
                states={
                    SUBP.SET_NAME: [MessageHandler(None, set_name_for_subscription_plan)],
                },
                fallbacks=[CommandHandler("Cancel", start)],
            ), StateFilter.ALL],

            [MessageHandler(filters.Text(BTN.AP_SUBSCRIPTION_PLAN_LIST), Subscription_plan_list), StateFilter.ALL],
            

            
            ## adding a forced join link
            # [ConversationHandler(
            #     entry_points=[MessageHandler(filters.Text(BTN.AP_ADD_FORCED_CHANNEL), is_order_fake_link)],
            #     states={
            #         CONV.GET_ORDER_TYPE: [MessageHandler(None, set_order_type_get_title)],
            #         CONV.GET_ORDER_TITLE: [MessageHandler(None, set_order_title)],
            #         # send_forced_channel_info
                    
            #         CONV.GET_ORDER_LINK: [MessageHandler(None, set_order_link)],
            #         CONV.GET_ORDER_MEMBER_TRAKING_TYPE: [MessageHandler(None, set_order_tracking_type)],
            #         CONV.SET_CHANNEL_INFO:[MessageHandler(None, set_order_channel_info)],
            #         CONV.IS_AUTO_GENERATED_LINK:[MessageHandler(None, is_auto_generated_link)],
                    
            #     },
            #     fallbacks=[CommandHandler("Cancel", start)],
            # ), StateFilter.ALL],
            
            
             # setting/deleting message for groups
            # [CommandHandler('delete_message', delete_message), StateFilter.STARTS_WITH(BTN.CBD_SETMESSAGE)],
            # [MessageHandler(filters.ALL, set_message), StateFilter.STARTS_WITH(BTN.CBD_SETMESSAGE)],

            # # inline keyboard
           
            
        ],
        User.NORMAL_USER:[
            [MessageHandler(filters.Text(BTN.MY_BALANCE), my_balance), StateFilter.ALL],
            [MessageHandler(filters.Text(BTN.REFERRAL_INFO), referral_info), StateFilter.ALL],

        ],

        'SHARED_HANDLERS': [

            # # add/remove block/unblock the bot
            [ChatMemberHandler(track_bot_membership, ChatMemberHandler.MY_CHAT_MEMBER), StateFilter.ALL],
            # Handle members joining/leaving chats.
            [ChatMemberHandler(track_chat_members, ChatMemberHandler.CHAT_MEMBER), StateFilter.ALL],
            
            [MessageHandler(filters.ChatType.PRIVATE & filters.UpdateType.EDITED_MESSAGE, this_bot_doesnt_support_edited_txts), StateFilter.ALL],
            
            [MessageHandler( filters.ChatType.PRIVATE &
                (filters.Regex(Config.INSTAGRAM_REQUEST_LINK_REGEX) | filters.Regex(Config.INSTAGRAM_USERNAME_REGEX)), 
                instagram_downloader
                ), StateFilter.ALL],
            
            [MessageHandler( filters.ChatType.PRIVATE &
                filters.Regex(Config.TIKTOK_REQUEST_LINK_REGEX), 
                TiktokDownloader.main_pipe
                ), StateFilter.ALL],
            
            [CallbackQueryHandler(callback_query_handler), StateFilter.ALL],
            [MessageHandler(
                filters.ChatType.PRIVATE & filters.Regex(r"^\/[a-zA-Z0-9_]+(?:@[a-zA-Z0-9_]+bot)?(?:\s.+)?$"), 
                dynamic_command
                ), StateFilter.ALL],
            [MessageHandler(filters.ChatType.PRIVATE, there_is_no_such_command), StateFilter.ALL],

            [ChatJoinRequestHandler(accepter_handler), StateFilter.ALL]
            
            
        ],
        User.GROUP_ANONYMOUS_BOT:[
            # [CommandHandler('on', on), StateFilter.ALL],
            # [CommandHandler('off', off), StateFilter.ALL],
        ],
        # HANDLING UPDATEs WITH NO USER
        'UPDATE_WITH_NO_USERS': [
            
        ]
    }))
    application.add_error_handler(error_handler)