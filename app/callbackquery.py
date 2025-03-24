
from telegram import Update
from telegram.ext import ContextTypes
class CallbackQueryHandlerBase():

    def __init__(
            self,
            answer_query_immediately: bool = True,
            ) -> None:
        
        self.answer_query_immediately = answer_query_immediately

    


class CallbackQueryCrud():
    pass


class JoinRecordStatsCQH(CallbackQueryHandlerBase):

    async def see_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, queries:tuple):

        channel = queries[0]

        
        