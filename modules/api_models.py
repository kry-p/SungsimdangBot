from pydantic import BaseModel, ConfigDict

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
    documents: list[KakaoSearchDocument] = []


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
    genres: list[str] | None = []
    content_rating: str | None = ""
    distributed_air_time: str | None = ""
    is_ending: bool | None = False
    is_laftel_only: bool | None = False
    is_exclusive: bool | None = False
    is_dubbed: bool | None = False


class LaftelSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    count: int = 0
    results: list[LaftelAnime] = []


# --- RSS Feed (FastAPI) ---


class RssfEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = ""
    link: str = ""


class RssfResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date: str = ""
    entries: list[RssfEntry] = []
