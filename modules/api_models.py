from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# --- 서울 한강 수온 ---


class HangangWaterRow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    WATT: str


class HangangWaterData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    row: list[HangangWaterRow]


class HangangWaterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    WPOSInformationTime: HangangWaterData


# --- 카카오 웹 검색 ---


class KakaoSearchDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = ""
    contents: str = ""
    url: str = ""


class KakaoSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    documents: list[KakaoSearchDocument] = Field(default_factory=list)


# --- 카카오 좌표→주소 ---


class KakaoAddress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    address_name: str = ""


class KakaoAddressDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    address: KakaoAddress


class KakaoAddressResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    documents: list[KakaoAddressDocument]


# --- OpenWeatherMap ---


class WeatherDescription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    description: str = ""


class WeatherMain(BaseModel):
    model_config = ConfigDict(extra="ignore")
    temp: float
    feels_like: float
    humidity: float


class WeatherResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    weather: list[WeatherDescription]
    main: WeatherMain


# --- Laftel ---


class LaftelAnime(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int = 0
    name: str | None = ""
    genres: list[str] | None = Field(default_factory=list)
    content_rating: str | None = ""
    distributed_air_time: str | None = ""
    is_ending: bool | None = False
    is_laftel_only: bool | None = False
    is_exclusive: bool | None = False
    is_dubbed: bool | None = False


class LaftelSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    count: int = 0
    results: list[LaftelAnime] = Field(default_factory=list)


# --- Spotify Web API ---


class SpotifyTokenResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str = ""
    token_type: str = "Bearer"
    expires_in: int = 0


class SpotifyExternalUrls(BaseModel):
    model_config = ConfigDict(extra="ignore")

    spotify: str = ""


class SpotifyArtist(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = ""


class SpotifyAlbumImage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: str = ""
    width: int | None = None
    height: int | None = None


class SpotifyAlbum(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = ""
    release_date: str = ""
    images: list[SpotifyAlbumImage] = Field(default_factory=list)


class SpotifyTrack(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    artists: list[SpotifyArtist] = Field(default_factory=list)
    album: SpotifyAlbum = Field(default_factory=SpotifyAlbum)
    duration_ms: int = 0
    explicit: bool = False
    external_urls: SpotifyExternalUrls = Field(default_factory=SpotifyExternalUrls)


class SpotifySearchTracks(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[SpotifyTrack] = Field(default_factory=list)


class SpotifySearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tracks: SpotifySearchTracks = Field(default_factory=SpotifySearchTracks)


# --- RSS Feed (FastAPI) ---


class RssfEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = ""
    link: str = ""


class RssfResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date: str = ""
    hour: int | None = None
    entries: list[RssfEntry] = Field(default_factory=list)


# --- Codex Reset ---


class CodexResetProbabilityWindow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    display: int


class CodexResetProbabilities(BaseModel):
    model_config = ConfigDict(extra="ignore")

    h24: CodexResetProbabilityWindow


class CodexResetLatestReset(BaseModel):
    model_config = ConfigDict(extra="ignore")

    occurred_at: datetime = Field(alias="occurredAt")


class CodexResetForecastResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    calculated_at: datetime | None = Field(alias="calculatedAt")
    valid_until: datetime | None = Field(alias="validUntil")
    publication_state: str = Field(alias="publicationState")
    display_mode: str = Field(alias="displayMode")
    probabilities: CodexResetProbabilities | None = None
    latest_reset: CodexResetLatestReset | None = Field(default=None, alias="latestReset")


# --- Codex Reset History ---


class CodexResetHistoryEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    announced_at: datetime = Field(alias="announcedAt")
    kind: str
    event_kind: str = Field(default="", alias="eventKind")
    status: str = ""
    scope: str = "unknown"
    evidence_url: str | None = Field(default=None, alias="evidenceUrl")


class CodexResetHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[CodexResetHistoryEvent]
