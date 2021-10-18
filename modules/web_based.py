import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import datetime
import requests
import cloudscraper
import json
import urllib.parse
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from config import config

# TEMPERATURE_BASE_URL = 'http://www.koreawqi.go.kr/index_web.jsp'
TEMPERATURE_BASE_URL = 'http://water.nier.go.kr/'
NAMUWIKI_BASE_URL = 'https://namu.wiki/w/'
SEARCH_BASE_URL = 'https://dapi.kakao.com/v2/search/web?'


# 강물 온도 조회
class WebManager:
    # init
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('headless')
        chrome_options.add_argument("--disable-gpu")

        self.session = requests.session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/92.0.4515.131 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        self.cloudscraper = cloudscraper.create_scraper()
        self.driver = webdriver.Chrome(config.CHROME_DRIVER_PATH, chrome_options=chrome_options)
        self.suon = list()
        self.site = list()
        self.suon_temp = None
        self.site_temp = None
        self.html = None
        self.soup = None
        # Records current time and latest update 현재 시간과 마지막 업데이트 시점을 기록
        self.currentTime = datetime.datetime.now()
        self.lastUpdateTime = datetime.datetime(self.currentTime.year,
                                                self.currentTime.month,
                                                self.currentTime.day,
                                                self.currentTime.hour,
                                                1)
        if self.currentTime.minute == 0:
            self.lastUpdateTime -= datetime.timedelta(hours=1)

        # Initialize current temperature information 현재 온도 정보를 최초 설정
        self.update_suon()

    # Update current temperature data 현재 온도 정보를 업데이트
    def update_suon(self):
        # check recently update temperature info 최근에 업데이트하였는지 확인
        self.currentTime = datetime.datetime.now()
        interval = (self.currentTime - self.lastUpdateTime).seconds

        if self.suon and interval < 600:  # refresh rate: 10 min.
            return
        else:
            self.suon = list()
            self.site = list()

            self.driver.get(TEMPERATURE_BASE_URL)
            self.html = self.driver.page_source
            self.soup = BeautifulSoup(self.html, 'html.parser')

            spot_list = self.soup.select("#tabb1 > div.auto_station_info > ul > li > div > div")
            suon_list = self.soup.select(
                "#tabb1 > div.auto_station_info > ul > li > div > table > tbody > tr:nth-child("
                "1) > td")[0::2]

            for i in spot_list:
                self.site.append(i.text.strip().replace("\t", "").split("\n")[0])
            for i in suon_list:
                self.suon.append(i.text.strip())

    # Search from Daum and returns result by JSON
    def daum_search(self, message, site):
        command = message.text.split()
        keyword = ''
        for i in range(1, len(command)):
            if i < len(command) - 1:
                keyword += command[i] + ' '
            else:
                keyword += command[i]

        # Sends request
        search_args = {'query': keyword if site is None else keyword + ' site:' + site}
        search_url = SEARCH_BASE_URL + urllib.parse.urlencode(search_args)
        search_headers = {"Authorization": 'KakaoAK ' + config.KAKAO_TOKEN}
        search_request = requests.get(search_url, headers=search_headers)

        result = json.loads(search_request.text)

        for i in result['documents']:
            urlinfo = urllib.parse.urlsplit(i['url'])
            i['url'] = f'{urlinfo.scheme}://{urlinfo.netloc}{urllib.parse.quote(urlinfo.path)}'

        return result

    # Search from Namu.wiki
    def namuwiki_search(self, message):
        command = message.text.split()
        keyword = ''
        for i in range(1, len(command)):
            if i < len(command) - 1:
                keyword += command[i] + ' '
            else:
                keyword += command[i]

        url = NAMUWIKI_BASE_URL + urllib.parse.quote(keyword)

        result = self.daum_search(message, "namu.wiki")['documents'][0]
        result_contents = result['contents']
        result_url = result['url']

        if result_url != url:
            return "[" + keyword + " - 나무위키](" + url + ")"
        else:
            text = re.sub('<.+?>', '', result_contents, 0, re.I | re.S)
            return "[" + keyword + " - 나무위키](" + url + ")\n\n" + text

    # Provide temperature data to other methods 다른 메소드로 온도 정보 전달
    def provide_suon(self, site):
        try:
            position = self.site.index(site)
            return self.suon[position]
        except ValueError:
            return 'error'
