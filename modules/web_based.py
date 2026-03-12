import datetime
import json
import re
import urllib.parse

import requests

from config import config
from modules import log
from resources import strings

# Initialize logger module
logger = log.Logger()

NAMUWIKI_BASE_URL = config.NAMUWIKI_BASE_URL
SEARCH_BASE_URL = config.SEARCH_BASE_URL


# 강물 온도 조회
class WebManager:
    # init
    def __init__(self):
        self.suonV2 = None
        # Records current time and latest update 현재 시간과 마지막 업데이트 시점을 기록
        self.currentTime = datetime.datetime.now()
        self.lastUpdateTime = datetime.datetime(
            self.currentTime.year, self.currentTime.month, self.currentTime.day, self.currentTime.hour, 1
        )
        if self.currentTime.minute == 0:
            self.lastUpdateTime -= datetime.timedelta(hours=1)

        # Initialize current temperature information 현재 온도 정보를 최초 설정
        self.update_suon()

    # Update current temperature data 현재 온도 정보를 업데이트
    def update_suon(self):
        # check recently update temperature info 최근에 업데이트하였는지 확인
        self.currentTime = datetime.datetime.now()
        interval = (self.currentTime - self.lastUpdateTime).seconds

        if self.suonV2 and interval < 600:  # refresh rate: 10 min.
            return
        else:
            try:
                search_request = requests.get(config.SEOUL_HANGANG_WATER_URL, timeout=10)
                result = json.loads(search_request.text)
                self.suonV2 = result["WPOSInformationTime"]["row"][0]["WATT"]
            except Exception:
                logger.log_error("Retreiving water information of Hangang failed. Please check API Status.")
                self.suonV2 = None

    # Search from Daum and returns result by JSON
    def daum_search(self, message, site):
        command = message.text.split()
        keyword = ""
        for i in range(1, len(command)):
            if i < len(command) - 1:
                keyword += command[i] + " "
            else:
                keyword += command[i]

        # Sends request
        search_args = {"query": keyword if site is None else keyword + " site:" + site}
        search_url = SEARCH_BASE_URL + urllib.parse.urlencode(search_args)
        search_headers = {"Authorization": "KakaoAK " + config.KAKAO_TOKEN}

        try:
            search_request = requests.get(search_url, headers=search_headers, timeout=10)
            result = json.loads(search_request.text)
        except Exception:
            return {"documents": []}

        for i in result["documents"]:
            urlinfo = urllib.parse.urlsplit(i["url"])
            i["url"] = f"{urlinfo.scheme}://{urlinfo.netloc}{urllib.parse.quote(urlinfo.path)}"

        return result

    # Search from Namu.wiki
    def namuwiki_search(self, message):
        command = message.text.split()
        keyword = ""
        for i in range(1, len(command)):
            if i < len(command) - 1:
                keyword += command[i] + " "
            else:
                keyword += command[i]

        url = NAMUWIKI_BASE_URL + urllib.parse.quote(keyword)

        documents = self.daum_search(message, "namu.wiki")["documents"]
        if not documents:
            return strings.search_no_result_msg

        result = documents[0]
        result_contents = result["contents"]
        result_url = result["url"]

        if result_url != url:
            return "[" + keyword + " - 나무위키](" + url + ")"
        else:
            text = re.sub("<.+?>", "", result_contents, count=0, flags=re.IGNORECASE | re.DOTALL)
            return "[" + keyword + " - 나무위키](" + url + ")\n\n" + text

    # Provide temperature data to other methods (V2, 한강으로 고정)
    def provide_suon_v2(self):
        if self.suonV2 is None:
            return "점검중"
        return self.suonV2
