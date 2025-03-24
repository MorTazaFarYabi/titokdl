
from telegram.ext.filters import UpdateFilter
from telegram import Update
import re
      
    
class StateFilter():
     
    ALL = lambda state : True
    
    def RE(regex):
        
        return lambda state : re.search(regex, state)
    
    def STARTS_WITH(beggining):
        return lambda state : state.startswith(beggining)