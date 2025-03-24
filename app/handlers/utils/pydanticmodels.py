
from pydantic import BaseModel, HttpUrl, TypeAdapter, root_validator
from typing import Any, Dict, List, Optional, Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.constants.callback_data import CD


class MediaItem(BaseModel):
    """ a model for a story/post/reels media
    
    by default the fields are named the way one api names them
    """
    type: str  # "photo" or "video"
    url: str
    original_url:Optional[str] = None
    cover: Optional[str] = None  # Some media might not have a cover [only used for some posts/reels]
    length: Optional[int] = None

    @root_validator(pre=True)
    def unify_fields(cls, values):
        """
        A pre-validator that normalizes field names coming from FastsaverAPI.
        """

        # If "download_url" exists (API #2), rename it to "url" if "url" doesn't exist
        if "download_url" in values and "url" not in values:
            values["url"] = values["download_url"]

        # If "thumb" exists (API #2), rename it to "cover" if "cover" doesn't exist
        if "thumb" in values and "cover" not in values:
            values["cover"] = values["thumb"]

        # If 'type' is 'image' in API #2, convert it to 'photo'
        if values.get("type") == "image":
            values["type"] = "photo"

        return values

class HdProfilePicInfo(BaseModel):
    url: str

class Owner(BaseModel):
    username: str
    profile_pic_url: str
    is_private: bool
    is_verified: bool
    id: str
    hd_profile_pic_url_info: HdProfilePicInfo
    full_name: Optional[str] = None  # Full name might be missing

class InstagramPost(BaseModel):
    media: List[MediaItem]
    caption: Optional[str] = None  # Caption might be empty or missing
    owner: Optional[Owner] = None

    @root_validator(pre=True)
    def unify_fields(cls, values):
        """
        A pre-validator that normalizes field names coming from FastsaverAPI.
        """

        # If "download_url" exists (API #2), rename it to "url" if "url" doesn't exist
        if "medias" in values and "media" not in values:
            values["media"] = values["medias"]

        # If "thumb" exists (API #2), rename it to "cover" if "cover" doesn't exist
        if "thumb" in values and "cover" not in values:
            values["cover"] = values["thumb"]

        # If 'type' is 'image' in API #2, convert it to 'photo'
        if values.get("type") == "image":
            values["type"] = "photo"
        
        if "download_url" in values and "medias" not in values:
            values['media'] = [{"type": values.get("type"), "url":values.get("download_url")}]

        return values


######### stories ###########
    


class StoriesResponse(BaseModel):
    status: int
    result: List[MediaItem]

######## OneAPIResponse ##########
class OneAPIResponse(BaseModel):
    status: int
    message: Optional[str] = None  # Some responses may contain only 'message'
    result: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None  
    # 'result' can now be either a dictionary or a list of dictionaries

    @root_validator(pre=True)
    def unify_fields(cls, values):
        """if fastsaverapi encounters an error it will return no status parameter so we make a status field ourself"""
        if values.get("result")!= None and "message" in values.get("result"):
            values['message'] = values.get("result").get('message')
        return values

######## user
class InstaUserProfile(BaseModel):
    id: str
    username: str
    bio: Optional[str] = None
    full_name: Optional[str] = None
    type: str  # "Public" or "Private"
    profile: str  # Profile picture URL
    profile_hd: str  # HD profile picture URL
    posts: int
    followers: int
    following: int
    is_verified: bool
    is_business: bool




#### highlight stories
class Story(BaseModel):
    """Represents a media item in a highlight story."""
    type: str  # "photo" or "video"
    url: str


class Highlight(BaseModel):
    id: str
    title: str
    cover: Optional[HttpUrl] = None # URL for the cover image


class FastServerAPIResultForPostsAndStories(BaseModel):
    error: bool
    hosting: str
    shortcode: str
    caption: Optional[str] = None
    # 'type', 'download_url', 'thumb' appear in the single-media response
    type: Optional[str] = None
    download_url: Optional[str] = None
    thumb: Optional[str] = None
    
    # 'medias' appears in the multi-media response
    medias: Optional[List[MediaItem]] = None

    @property
    def media(self) -> Union[MediaItem, List[MediaItem], None]:
        """
        - If 'download_url' is present, return a single MediaItem.
        - If 'medias' is present, return a list of MediaItem.
        - Otherwise, return None.
        """
        if self.download_url:
            # Single item response
            return [MediaItem(
                type=self.type or "unknown",
                url=self.download_url
            )]
        elif self.medias:
            # Multi-media response
            return TypeAdapter(List[MediaItem]).validate_python(self.medias)
        return None



class InstaScraperSuccessResponse(BaseModel):
    data: list | dict
    pagination_token: Optional[str] = None

class InstaScraperErrorResponse(BaseModel):
    detail: str

from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class AvatarStatus(BaseModel):
    has_avatar: bool

class BiographyEntities(BaseModel):
    entities: List
    raw_text: str

class HdProfilePicInfo(BaseModel):
    height: int
    url: HttpUrl
    width: int

class HdProfilePicVersions(BaseModel):
    height: int
    url: HttpUrl
    width: int

class FanClubInfo(BaseModel):
    fan_club_id: Optional[int]
    fan_club_name: Optional[str]
    subscriber_count: Optional[int]

class LocationData(BaseModel):
    address_street: str
    city_id: int
    city_name: str
    instagram_location_id: str
    latitude: float
    longitude: float
    zip: str

class InstagramScraperUserData(BaseModel):
    about: Optional[str | None] = ""
    # account_badges: List
    account_category: str|None = ""
    # account_type: int
    # avatar_status: AvatarStatus
    biography: str
    # biography_with_entities: BiographyEntities
    # category: str
    # category_id: int
    follower_count: int
    following_count: int
    full_name: str
    # has_highlight_reels: bool
    # has_igtv_series: bool
    hd_profile_pic_url_info: HdProfilePicInfo
    # hd_profile_pic_versions: List[HdProfilePicVersions]
    id: str
    is_private: bool
    is_verified: bool
    # location_data: LocationData
    media_count: Optional[int] = 0
    profile_pic_url: str
    profile_pic_url_hd: str
    username: str

class InstagramScraperResponse(BaseModel):
    status: int
    message: Optional[str] = None  # Some responses may contain only 'message'
    result: InstaScraperSuccessResponse | InstaScraperErrorResponse
    # 'result' can now be either a dictionary or a list of dictionaries


class InlineKeyboardBTN(BaseModel):
    text:str
    callback_data: str | None = None
    url:str|None = None

class MessageKeyboard(BaseModel):
    rows: List[List[InlineKeyboardBTN]] | List = []

        


