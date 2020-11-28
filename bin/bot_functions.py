from selenium import webdriver
from bs4 import BeautifulSoup

TEMPERATURE_URL = 'http://www.koreawqi.go.kr/index_web.jsp'


class BotFunctions:
    # init (not in use for now)
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
            return '현재 한강 수온 정보를 가져올 수 없습니다..'
