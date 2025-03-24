

from typing import Any, Dict, List, Self
import aiohttp
from handlers.utils.pydanticmodels import InstaScraperErrorResponse, InstaScraperSuccessResponse, InstagramScraperResponse, OneAPIResponse


class API_STATUS_CODES:
    SUCCESS = 200
    BAD_REQUEST = 400  # The request contains invalid parameters.
    UNAUTHORIZED = 401  # The authentication token is not provided.
    API_COULDNT_DOWNLOAD_THIS = 402
    FORBIDDEN = 403  # The request could not be completed due to insufficient credit.
    RESTRICTED_OR_REMOVED = 404 #
    PATH_DOESNT_EXIST = 409  # The requested path does not exist.
    SERVER_ERROR = 500  # The server returned an empty response. Please try again later.


class OneAPIRequest:
    API_BASE_URL = "https://api.one-api.ir/"
    
    class REQUEST_STATUS:
        SUCCESS = 200
        LACK_OF_BALANCE = 403

    def __init__(self, token: str) -> None:
        self.TOKEN = token
        self.api_request_url = ""  # To be set in subclasses
        self.parameters = {}

    async def fetch(self) -> OneAPIResponse | str:
        """
        Send a GET request to OneAPI.
        """
        if not self.api_request_url:
            raise ValueError("API request URL is not set.")
        
        headers = {
            "accept": "application/json",
            "one-api-token": self.TOKEN
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_request_url, headers=headers, params=self.parameters) as response:
                self.request_status = response.status
                if response.status == 200:
                    res = await response.json()
                    print(res)
                    return OneAPIResponse(**res)  # Convert to JSON
                else:
                    return {"error": f"Request failed with status {response.status}"}

class InstagramAPI(OneAPIRequest):

    # the names of methods should mimic those in Config.INSTAGRAM_REGEX_PATTERNS for them to be called if url matched the pattern

    def __init__(self, token: str) -> None:
        super().__init__(token)
        self.API_BASE_URL = "https://api.one-api.ir/instagram/v1/"


    def user(self, username: str) -> Self:
        """Set API URL for an Instagram reel download."""
        self.api_request_url = self.API_BASE_URL + "user/"
        self.parameters = {"username": username}
        return self



    def post(self, shortcode: str) ->Self:
        """Set API URL for an Instagram post download."""
        self.api_request_url = self.API_BASE_URL + "post/"

        self.parameters = {"shortcode": shortcode}
        return self
    
    def reel(self, shortcode: str) ->Self:
        """Set API URL for an Instagram reel download."""
        self.api_request_url = self.API_BASE_URL + "post/"
        self.parameters = {"shortcode": shortcode}
        return self



    # def posts(self, username: str):
    #     """Set API URL for fetching multiple posts from a user."""
    #     self.api_request_url = self.API_BASE_URL + "posts/"
    #     self.parameters = {"username": username}
    #     return self  # Allows chaining

    

    # def stories(self, user_id: str) -> Self:
        
    #     """gets user's stories"""
    #     self.api_request_url = self.API_BASE_URL + "user/stories/"
    #     self.parameters = {"id": user_id}
    #     return self


    def stories(self, user_id: str) -> Self:
        """gets user's stories"""
        self.api_request_url = self.API_BASE_URL + "user/stories/"
        self.parameters = {"id": user_id}
        return self


    def highlight(self, highlight_id: int) -> Self:
        """gets highlights stories"""
        self.api_request_url = self.API_BASE_URL + "highlight/"
        self.parameters = {"id": highlight_id}
        return self
    

    def highlights(self, user_id: int) -> Self:
        """gets users highlights lists"""

        self.api_request_url = self.API_BASE_URL + "user/highlights/"
        self.parameters = {"id": user_id}
        return self


    async def get_it_using_request_info(self, method_tuple) -> OneAPIResponse:
        """
        Calls the appropriate method based on the tuple input.

        :param method_tuple: Tuple containing (method_name, arguments)
        :return: Self instance with method set, or None if invalid
        """
        method_name, *arguments = method_tuple  # Extract method name and arguments

        method = getattr(self, method_name, None)  # Get method dynamically

        if callable(method):  # Check if the method exists and is callable
            return await method(*arguments).fetch()  # Unpack arguments dynamically
        else:
            raise ValueError(f"Method '{method_name}' does not exist in InstagramDownloader.")


class YoutubeDownloader(OneAPIRequest):

    def post():
        return 
    
    

class FastSaverAPI:
    API_BASE_URL = "https://fastsaverapi.com/get-info"
    
    class REQUEST_STATUS:
        SUCCESS = 200
        LACK_OF_BALANCE = 403

    def __init__(self, token: str) -> None:
        self.TOKEN = token
        self.api_request_url = ""  # To be set in subclasses
        self.parameters = {token:token}

    async def fetch(self) -> OneAPIResponse | str:
        """
        Send a GET request to OneAPI.
        """
        if not self.api_request_url:
            raise ValueError("API request URL is not set.")
        
        headers = {
            "accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_request_url, headers=headers, params=self.parameters) as response:
                self.request_status = response.status

                res = await response.json()
                if res == None:
                    res = {}
                res = {"status":response.status, "result":{**res}}
                return OneAPIResponse(**res)
                
class InstagramFastSaverAPI(FastSaverAPI):
    def __init__(self, token: str) -> None:
        super().__init__(token)


    def get(self, url: str) -> Self:
        """Set API URL for an Instagram reel download."""
        self.api_request_url = self.API_BASE_URL
        self.parameters = {"url": url, "token":self.TOKEN}
        return self
    

class InstagramAPI(OneAPIRequest):

    # the names of methods should mimic those in Config.INSTAGRAM_REGEX_PATTERNS for them to be called if url matched the pattern

    def __init__(self, token: str) -> None:
        super().__init__(token)
        self.API_BASE_URL = "https://api.one-api.ir/instagram/v1/"


    def user(self, username: str) -> Self:
        """Set API URL for an Instagram reel download."""
        self.api_request_url = self.API_BASE_URL + "user/"
        self.parameters = {"username": username}
        return self



    def post(self, shortcode: str) ->Self:
        """Set API URL for an Instagram post download."""
        self.api_request_url = self.API_BASE_URL + "post/"

        self.parameters = {"shortcode": shortcode}
        return self
    
    def reel(self, shortcode: str) ->Self:
        """Set API URL for an Instagram reel download."""
        self.api_request_url = self.API_BASE_URL + "post/"
        self.parameters = {"shortcode": shortcode}
        return self



    # def posts(self, username: str):
    #     """Set API URL for fetching multiple posts from a user."""
    #     self.api_request_url = self.API_BASE_URL + "posts/"
    #     self.parameters = {"username": username}
    #     return self  # Allows chaining

    

    # def stories(self, user_id: str) -> Self:
        
    #     """gets user's stories"""
    #     self.api_request_url = self.API_BASE_URL + "user/stories/"
    #     self.parameters = {"id": user_id}
    #     return self


    def stories(self, user_id: str) -> Self:
        """gets user's stories"""
        self.api_request_url = self.API_BASE_URL + "user/stories/"
        self.parameters = {"id": user_id}
        return self


    def highlight(self, highlight_id: int) -> Self:
        """gets highlights stories"""
        self.api_request_url = self.API_BASE_URL + "highlight/"
        self.parameters = {"id": highlight_id}
        return self
    

    def highlights(self, user_id: int) -> Self:
        """gets users highlights lists"""

        self.api_request_url = self.API_BASE_URL + "user/highlights/"
        self.parameters = {"id": user_id}
        return self


    async def get_it_using_request_info(self, method_tuple) -> OneAPIResponse:
        """
        Calls the appropriate method based on the tuple input.

        :param method_tuple: Tuple containing (method_name, arguments)
        :return: Self instance with method set, or None if invalid
        """
        method_name, *arguments = method_tuple  # Extract method name and arguments

        method = getattr(self, method_name, None)  # Get method dynamically

        if callable(method):  # Check if the method exists and is callable
            return await method(*arguments).fetch()  # Unpack arguments dynamically
        else:
            raise ValueError(f"Method '{method_name}' does not exist in InstagramDownloader.")


class YoutubeDownloader(OneAPIRequest):

    def post():
        return 
    
    

class BaseInstagramScraperAPI:
    API_BASE_URL = "https://instagram-scraper-api2.p.rapidapi.com"
    
    class REQUEST_STATUS:
        SUCCESS = 200
        LACK_OF_BALANCE = 403

    def __init__(self, token: str) -> None:
        self.TOKEN = token
        self.api_request_url = ""  # To be set in subclasses
        self.parameters = {}
        

    async def fetch(self) -> InstagramScraperResponse:
        """
        Send a GET request to OneAPI.
        """
        if not self.api_request_url:
            raise ValueError("API request URL is not set.")
        
        headers = {
            'x-rapidapi-key': self.TOKEN,
            'x-rapidapi-host': "instagram-scraper-api2.p.rapidapi.com"
        }

        params = {
            key: str(value).lower() if isinstance(value, bool) else value
            for key, value in self.parameters.items()
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_request_url, headers=headers, params=params) as response:
                self.request_status = response.status

                # print(self.api_request_url)
                # print(headers)
                # print(self.parameters)
                # print(self.request_status)


                res = await response.json()
                # print(res)
                # return
                if self.request_status == 200:
                    res = InstaScraperSuccessResponse(**res)
                else:
                    res = InstaScraperErrorResponse(**res)

                return InstagramScraperResponse(**{"status":self.request_status, 'result':res})
                
class InstagramScraperAPI(BaseInstagramScraperAPI):
    def __init__(self, token: str) -> None:
        super().__init__(token)


    def get_user_profile_info(self, username_or_id_or_url: str) -> Self:
        """Set API URL for an Instagram reel download."""
        self.api_request_url = self.API_BASE_URL + "/v1/info"
        self.parameters = {"username_or_id_or_url": username_or_id_or_url}
        print(self.api_request_url)
        return self
    
    def get_info(self, code_or_id_or_url: str, url_embed_safe: bool = True) -> Self: #used for single story/post/reel/tv/share
        """Set API URL for an Instagram reel download.
        
        if url_embed_safe==True: there would be no problem with instagram CORS
        
        """
        self.api_request_url = self.API_BASE_URL + "/v1/post_info"
        self.parameters = {
            "code_or_id_or_url": code_or_id_or_url,
            # "url_embed_safe": url_embed_safe #
            }
        print(self.api_request_url)
        return self
    
    def highlight_info(self, highlight_id: str, url_embed_safe: bool = False) -> Self: #used for single story/post/reel/tv/share
        """Set API URL for an Instagram reel download.
        
        if url_embed_safe==True: there would be no problem with instagram CORS
        
        """
        self.api_request_url = self.API_BASE_URL + "/v1/highlight_info"
        self.parameters = {
            "highlight_id": highlight_id,
            # "url_embed_safe": url_embed_safe #
            }
        print(self.api_request_url)
        return self
    
    def audio_info(self, audio_id: str, url_embed_safe: bool = False) -> Self: #used for single story/post/reel/tv/share
        """Set API URL for an Instagram reel download.
        
        if url_embed_safe==True: there would be no problem with instagram CORS
        
        """
        self.api_request_url = self.API_BASE_URL + "/v1/audio_info"
        self.parameters = {
            "audio_id": audio_id,
            # "url_embed_safe": url_embed_safe #
            }
        print(self.api_request_url)
        return self
    
    def highlights(self, username_or_id_or_url: str, url_embed_safe: bool = False) -> Self: #used for single story/post/reel/tv/share
        """Set API URL for an Instagram reel download.
        
        if url_embed_safe==True: there would be no problem with instagram CORS
        
        """
        self.api_request_url = self.API_BASE_URL + "/v1/highlights"
        self.parameters = {
            "username_or_id_or_url": username_or_id_or_url,
            # "url_embed_safe": url_embed_safe #
            }
        print(self.api_request_url)
        return self
    



class TikWM:
    API_BASE_URL = "https://www.tikwm.com/api/"
    
    class REQUEST_STATUS:
        SUCCESS = 200
        LACK_OF_BALANCE = 403

    def __init__(self, token: str) -> None:
        self.TOKEN = token
        self.api_request_url = ""  # To be set in subclasses
        self.parameters = {token:token}

    async def fetch(self) -> OneAPIResponse | str:
        """
        Send a GET request to OneAPI.
        """
        if not self.api_request_url:
            raise ValueError("API request URL is not set.")
        
        headers = {
            "accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_request_url, headers=headers, params=self.parameters) as response:
                self.request_status = response.status

                res = await response.json()
                if res == None:
                    res = {}
                res = {"status":response.status, "result":{**res}}
                return OneAPIResponse(**res)
                
class TikWMFileSaver(TikWM):
    def __init__(self, token: str) -> None:
        super().__init__(token)


    def get(self, url: str) -> Self:
        """Set API URL for an Instagram reel download."""
        self.api_request_url = self.API_BASE_URL
        self.parameters = {"url": url, "hd": 1}
        return self