from typing import Optional
from unidecode import unidecode
from typing_extensions import TypedDict

class BaseModel(TypedDict):
    # Define common attributes that both AlbumInfo and TrackInfo share
    title: Optional[str]
    artist: Optional[str]
    artist_id: Optional[str]
    media: Optional[str]
    artist_sort: Optional[str]
    data_source: Optional[str]
    data_url: Optional[str]
    genre: Optional[str]
