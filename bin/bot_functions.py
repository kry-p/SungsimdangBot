import random
import sqlite3

from selenium import webdriver
from bs4 import BeautifulSoup

TEMPERATURE_URL = 'http://www.koreawqi.go.kr/index_web.jsp'
USER_INFO = './user.db'

userDB = sqlite3.connect(USER_INFO)
cursor = userDB.cursor()


class UserManager:
    # init
    def __init__(self):
        pass



class BotFunctions:
    # init
    def __init__(self):

        BotFunctions.driver = webdriver.PhantomJS()

    # Get current river temperature (in progress)
    def get_temp(self):
        BotFunctions.driver.get(TEMPERATURE_URL)
        BotFunctions.driver.switch_to.frame('MainFrame')

        html = BotFunctions.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        try:
            hangang_temp = soup.select('tr > td.avg1')[18].text.strip()
            return '현재 한강 수온은 ' + hangang_temp + '도입니다.'
        except AttributeError:
            return '현재 수온 정보를 가져올 수 없습니다..'

    def picker(self, msg):
        random.seed()
        split = msg.split()
        split = [item for item in split if '/pick' not in item]

        try:
            choice = random.choice(split)
        except IndexError:
            return "올바르게 입력되지 않았어요. 다시 확인해 주세요.\n\n" \
               "예) /pick 튀김소보로 부추빵 모카번"

        return choice
