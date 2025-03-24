from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class MusicInfo(BaseModel):
    id: str
    title: str
    play: HttpUrl
    cover: HttpUrl
    author: str
    original: bool
    duration: int
    album: Optional[str]

class CommerceInfo(BaseModel):
    adv_promotable: bool
    auction_ad_invited: bool
    branded_content_type: int
    with_comment_filter_words: bool

class Author(BaseModel):
    id: str
    unique_id: str
    nickname: str
    avatar: HttpUrl

class Data(BaseModel):
    id: str
    region: str
    title: str
    cover: HttpUrl
    ai_dynamic_cover: HttpUrl
    origin_cover: HttpUrl
    duration: int
    play: HttpUrl
    wmplay: HttpUrl
    hdplay: HttpUrl
    size: int
    wm_size: int
    hd_size: int
    music: HttpUrl
    # music_info: MusicInfo
    
    # play_count: int
    # digg_count: int
    # comment_count: int
    # share_count: int
    # download_count: int
    # collect_count: int
    # create_time: int
    # anchors: Optional[List[str]]
    # anchors_extras: str
    # is_ad: bool
    # commerce_info: CommerceInfo
    # commercial_video_info: str
    # item_comment_settings: int
    # mentioned_users: str
    # author: Author

class TikWMResponseModel(BaseModel):
    code: int
    msg: str
    processed_time: float
    data: Data
