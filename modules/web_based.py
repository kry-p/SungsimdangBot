import datetime
import html
import urllib.parse

import requests

from config import config
from modules import log
from modules.api_models import (
    HangangWaterResponse,
    KakaoAddressResponse,
    KakaoSearchResponse,
    RssfResponse,
    WeatherResponse,
)
from modules.utils import extract_command_args, strip_html_tags
from resources import strings

# Initialize logger module
logger = log.Logger()

NAMUWIKI_BASE_URL = config.NAMUWIKI_BASE_URL
SEARCH_BASE_URL = config.SEARCH_BASE_URL
MAP_BASE_URL = "https://dapi.kakao.com/v2/local/geo/coord2address.json?"
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
SUON_REFRESH_INTERVAL = 600  # seconds


# 강물 온도 조회
class WebManager:
    # init
    def __init__(self):
        self.suon_v2 = None
        # Records current time and latest update 현재 시간과 마지막 업데이트 시점을 기록
        self.current_time = datetime.datetime.now()
        self.last_update_time = datetime.datetime(
            self.current_time.year, self.current_time.month, self.current_time.day, self.current_time.hour, 1
        )
        if self.current_time.minute == 0:
            self.last_update_time -= datetime.timedelta(hours=1)

        # Initialize current temperature information 현재 온도 정보를 최초 설정
        self.update_suon()

    # Update current temperature data 현재 온도 정보를 업데이트
    def update_suon(self):
        # check recently update temperature info 최근에 업데이트하였는지 확인
        self.current_time = datetime.datetime.now()
        interval = (self.current_time - self.last_update_time).total_seconds()

        if self.suon_v2 and interval < SUON_REFRESH_INTERVAL:
            return
        else:
            try:
                search_request = requests.get(config.SEOUL_HANGANG_WATER_URL, timeout=10)
                parsed = HangangWaterResponse.model_validate_json(search_request.text)
                self.suon_v2 = parsed.WPOSInformationTime.row[0].WATT
            except Exception:
                logger.log_error("Retreiving water information of Hangang failed. Please check API Status.")
                self.suon_v2 = None

    # Search from Daum and returns result by JSON
    def daum_search(self, message, site):
        keyword = extract_command_args(message.text)

        # Sends request
        search_args = {"query": keyword if site is None else keyword + " site:" + site}
        search_url = SEARCH_BASE_URL + urllib.parse.urlencode(search_args)
        search_headers = {"Authorization": "KakaoAK " + config.KAKAO_TOKEN}

        try:
            search_request = requests.get(search_url, headers=search_headers, timeout=10)
            parsed = KakaoSearchResponse.model_validate_json(search_request.text)
        except Exception:
            return KakaoSearchResponse()

        for doc in parsed.documents:
            urlinfo = urllib.parse.urlsplit(doc.url)
            doc.url = f"{urlinfo.scheme}://{urlinfo.netloc}{urllib.parse.quote(urlinfo.path, safe='/:@!$&*+,;=%')}"

        return parsed

    # Search from Namu.wiki
    def namuwiki_search(self, message):
        keyword = extract_command_args(message.text)
        url = NAMUWIKI_BASE_URL + urllib.parse.quote(keyword)

        documents = self.daum_search(message, "namu.wiki").documents
        if not documents:
            return strings.search_no_result_msg

        result = documents[0]
        result_contents = result.contents
        result_url = result.url

        text = strip_html_tags(result_contents)

        if result_url != url:
            result_title = strip_html_tags(result.title)
            return (
                strings.search_mismatch_msg.format(keyword=keyword)
                + "["
                + result_title
                + "]("
                + result_url
                + ")\n\n"
                + text
            )
        else:
            return strings.namu_result_msg.format(keyword=keyword, url=url, text=text)

    # Geolocation information
    def geolocation_info(self, latitude, longitude):
        map_args = {"x": longitude, "y": latitude}
        map_url = MAP_BASE_URL + urllib.parse.urlencode(map_args)
        map_headers = {"Authorization": "KakaoAK " + config.KAKAO_TOKEN}
        map_request = requests.get(map_url, headers=map_headers, timeout=10)

        weather_args = {"lang": "kr", "appid": config.WEATHER_TOKEN, "lat": latitude, "lon": longitude}
        weather_url = WEATHER_BASE_URL + urllib.parse.urlencode(weather_args)
        weather_request = requests.get(weather_url, timeout=10)
        weather_data = WeatherResponse.model_validate_json(weather_request.text)

        weather = weather_data.weather[0].description
        temp = str(round(weather_data.main.temp - 273.15)) + "°C"
        feels_temp = str(round(weather_data.main.feels_like - 273.15)) + "°C"
        humidity = str(round(weather_data.main.humidity)) + "%"

        weather_result = strings.geolocation_weather_msg.format(
            weather=weather, temp=temp, feels_temp=feels_temp, humidity=humidity
        )

        map_parsed = KakaoAddressResponse.model_validate_json(map_request.text)
        map_location = map_parsed.documents[0].address.address_name
        geo_location = strings.geolocation_coords_msg.format(latitude=latitude, longitude=longitude)

        return geo_location + "\n" + map_location + "\n\n" + weather_result

    # Provide temperature data to other methods (V2, 한강으로 고정)
    def provide_suon_v2(self):
        if self.suon_v2 is None:
            return strings.suon_maintenance_status
        return self.suon_v2

    def rss_handler(self, message):
        try:
            res = requests.get(config.RSSF_URL, params={"token": config.RSSF_TOKEN}, timeout=10)
            data = RssfResponse.model_validate_json(res.text)
            time_of_day = strings.bfrss_am if data.hour < 12 else strings.bfrss_pm
            text = strings.bfrss_header_msg.format(month=data.date[4:6], day=data.date[6:], time_of_day=time_of_day)
            text += "\n".join(
                f'• <a href="{html.escape(e.link, quote=True)}">{html.escape(e.title)}</a>' for e in data.entries
            )
            return text, "HTML"
        except Exception as e:
            logger.log_error(f"rss_handler failed: {e}")
            return strings.bfrss_error_msg, None
