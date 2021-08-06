import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import datetime
import requests
import cloudscraper
from bs4 import BeautifulSoup
from selenium import webdriver
from config import config
from urllib import parse

TEMPERATURE_BASE_URL = 'http://www.koreawqi.go.kr/index_web.jsp'
NAMUWIKI_BASE_URL = 'https://namu.wiki/w/'


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
            self.driver.get(TEMPERATURE_BASE_URL)
            self.driver.switch_to.frame('MainFrame')
            self.html = self.driver.page_source
            self.soup = BeautifulSoup(self.html, 'html.parser')

            self.site_temp = self.soup.select("tr[class^='site'] > th")
            self.suon_temp = self.soup.select('tr > td.avg1')

            for i in self.site_temp:
                self.site.append(i.text.strip())
            for i in self.suon_temp:
                self.suon.append(i.text.strip())

    def get_from_namuwiki(self, message):
        command = message.text.split()
        keyword = ''
        for i in range(1, len(command)):
            if i < len(command) - 1:
                keyword += command[i] + ' '
            else:
                keyword += command[i]

        url = NAMUWIKI_BASE_URL + parse.quote(keyword)

        self.html = self.cloudscraper.get(url).text
        self.soup = BeautifulSoup(self.html, 'html.parser')

        print(self.soup.get_text())

    # Provide temperature data to other methods 다른 메소드로 온도 정보 전달
    def provide_suon(self, site):
        try:
            position = self.site.index(site)
            return self.suon[position]
        except ValueError:
            return 'error'
