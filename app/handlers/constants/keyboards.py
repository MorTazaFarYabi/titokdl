from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.constants.buttons import BTN
from handlers.constants.callback_data import CD

class Keyboards:

    # ADD_CHANNEL_KEYBOARD = [
    #     [
    #         InlineKeyboardButton("تعیین پیام خوشامدگویی", callback_data=CD.SET_WELCOME_MESSAGE),
    #     ],
    #     [InlineKeyboardButton("تعیین پیام خداحافظی", callback_data=CD.SET_GOODBYE_MESSAGE)],

    #     [InlineKeyboardButton("تعیین تاخیر قبل از قبولی", callback_data=CD.SET_DELAY)],
    #     [InlineKeyboardButton("تنظیم CAPTCHA", callback_data=CD.SET_CAPTCHA)],
    # ]

    ADMIN_START_KEYBOARD= [
        [BTN.AS_STATS, BTN.AS_SEND_TO_ALL,],
        [BTN.AS_FORCED_JOIN,],
        [BTN.AS_MEMBERSHIP_CONTROL,],
        [BTN.AS_MESSAGE_MANAGEMENT, BTN.AS_COMMAND_MANAGEMENT,],
        # [BTN.AS_WEBSERVICE_CONTROL, BTN.AS_SETTING_DOWNLOAD_LIMIT],
        # [BTN.AS_ACCOUNTING, BTN.AS_CONTACTING_THE_PROGRAMMER],
        [BTN.AS_SOURCE_LINK, #BTN.AS_ADMIN_CONTROL
        BTN.AS_CHANNEL_MANAGEMENT],
    ]

    CONTROL_FORCE_JOIN = [
        [BTN.AP_ADD_FORCED_CHANNEL, BTN.AP_LIST_FORCED_CHANNELS],
        [BTN.AP_GET_BACK_TO_START_PAGE_OF_ADMIN_PANNEL]
    ]


    SUBSCRIPTION_PANNEL = [
        [BTN.AP_SUBSCRIPTION_PLAN_CONTROL, BTN.AP_SUBSCRIPTION_OPTIONS_CONTROL],
        [BTN.AP_GET_BACK_TO_START_PAGE_OF_ADMIN_PANNEL]
    ]

    SUBSCRIPTION_PLAN_CONTROL = [
        [BTN.AP_SUBSCRIPTION_PLAN_ADD, BTN.AP_SUBSCRIPTION_PLAN_LIST],
        [BTN.AP_GET_BACK_TO_START_PAGE_OF_ADMIN_PANNEL]
    ]


    STATS_KEYBOARD = [
        [
            InlineKeyboardButton(text= "آمار درخواست ها و API", callback_data=CD.API_STATS), 
            InlineKeyboardButton(text= "آمار سلامت سرویس", callback_data=CD.API_HEALTH_STATS)
        ],
        
        [
            InlineKeyboardButton(text= "آمار نوع درخواست ها", callback_data=CD.REQUEST_TYPE_STATS),
            InlineKeyboardButton(text= "📈📊", callback_data=CD.STATS_CHARTS)
        ],
        [
            InlineKeyboardButton(text= "💏 آمار وفاداری", callback_data=CD.LOYALTY_STATS),
            InlineKeyboardButton(text= "👥 آمار زیرمجموعه گیری", callback_data=CD.REFERRAL_STATISTICS),
            
        ]
    ]
    BACK_TO_STATS = [[InlineKeyboardButton(text="برگشت به آمار", callback_data=CD.STATISTICS)]]

    CANCEL_CONV = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            text= "❌ کنسل کردن",
        callback_data= CD.CANCEL_CONV
        )]]
    )

