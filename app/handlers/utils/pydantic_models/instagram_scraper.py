from typing import List, Optional
from pydantic import BaseModel, TypeAdapter, field_validator, root_validator
from typing import Literal

class MediaVersion(BaseModel):
    height: int
    width: int
    url: str
    url_original: str = None
    type: Optional[str] = None  # Automatically populated from MediaData

class MediaVersions(BaseModel):
    items: List[MediaVersion] = None
class MediaData(BaseModel):
    media_format: str
    image_versions: List[MediaVersion] = None
    video_versions: List[MediaVersion] = None


    @field_validator("image_versions", "video_versions", mode="before")
    def populate_media_versions(cls, value, values):
        
        if isinstance(value, dict) and "items" in value:
            value = value["items"]  # Convert to list

        if not value:
            value = []

        if value and "media_format" in values.data:
            for item in value:
                item['type'] = values.data["media_format"]
        return value


def get_media_list_for_story(data):
    story = MediaData(**data)
    if story.media_format =="video":
        return [story.video_versions[0]]
    return [story.image_versions[0]]

def get_media_list_for_post_reel(data):
    if isinstance(data, (list, dict)):
        post = MediaData(**data)
        
    else:
        post = data
    if post.media_format =="video":
        return [post.video_versions[0]]
    return [post.image_versions[0]]


class CarouselMedia(BaseModel):
    
    # carousel_media: List[MediaData] = []
    # carousel_media_count: int = 0
    pass
    

class InstagramScraperPost(BaseModel):
    media_format:Literal["album", "video", "image"]

    
    # album
    # carousel_media: List[MediaData] = []
    # carousel_media_count: int = 0
    caption: str
    media: list[MediaVersion]

    @root_validator(pre=True)
    def standardize_fields(cls, values):
        # caption
        if "caption" in values:
            values['caption'] = values['caption']['text']


        # album
        if values['media_format'] == "album":
            mediadata_list =  TypeAdapter(List[MediaData]).validate_python(values['carousel_media'])
            media_list = convert_list_of_media_data_to_media_version(mediadata_list)
            values['media'] = media_list
        
        # image / video
        if values['media_format'] != "album":
            values['media'] = get_media_list_for_post_reel(MediaData(**values))

        return values


def convert_list_of_media_data_to_media_version(the_list:List[MediaData]):

    new_list = []
    for x in the_list:
        new_list += get_media_list_for_post_reel(x)
    return new_list

    # else
