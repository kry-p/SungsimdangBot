# Strings and shared resources for this bot
# Modify at your OWN RISK!

import telebot

# Main strings

# Message for checking bot status
workingMsg = "성심당봇이 정상 작동 중입니다."
notWorkingMsg = "성심당봇에 이상이 있습니다. 문제를 확인해 주세요."

# Guideline message
startMsg = "성심당봇이에요! 무엇을 도와드릴까요?\n\n" \
           "1. 🌡 가까운 강 수온 알림 \n" \
           "2. ✅ 선택봇  \n" \
           "3. 🔫 러시안 룰렛 게임 \n" \
           "4. 🪙 동전뒤집기  \n" \
           "5. 🤬 나쁜말 감지기  \n" \
           "6. 📍 현재 위치 정보  \n" \
           "7. 📅 D-day \n" \
           "8. 🧮 계산기 \n\n" \
           "이외에도 많은 기능이 업데이트로 추가 제공될 예정입니다."

# Function strings

# nearby river temperature message
temperatureHelpMsg = "🌡 가까운 강 수온 알림 도움말 \n\n" \
                     "명령어 형식\n없음\n\n" \
                     "설명\n가까운 강 온도 정보를 제공합니다. '수온'이나 '자살'이 포함된 키워드를 " \
                     "입력할 경우 해당 사용자와 가까운 강의 온도 정보가 제공됩니다. \n" \
                     "사용자 정보 등록이 필요하며, 관련 사항은 봇 운영자에게 문의해 주세요."

# picker message
pickerHelpMsg = "✅ 선택봇 도움말 \n\n" \
                "명령어 형식\n/pick [단어1] [단어2] [단어3] ... [단어n]\n\n" \
                "설명\n1개 이상의 단어 중 하나를 무작위로 선택합니다. 선택장애를 위한 필수 아이템!\n"
pickerErrorMsg = "올바르게 입력되지 않았어요. 다시 확인해 주세요.\n\n" \
                 "예) /pick 튀김소보로 부추빵 모카번"

# russian roulette message
rouletteHelpMsg = "🔫 러시안 룰렛 도움말 \n\n" \
                  "명령어 형식\n/roulette [총 회전 수] [실탄 수]\n\n" \
                  "설명\n러시안 룰렛 게임입니다. 총 회전 수에는 내기에 참여할 사람 수를 입력하고, " \
                  "실탄 수는 당첨될 사람 수를 입력합니다. \n" \
                  "장전 후 격발은 /shoot 명령어를, \n" \
                  "룰렛 초기화는 /flush_bullet 명령어나 /roulette 0 0를 입력해 주세요."
rouletteErrorMsg = '명령어를 형식에 맞게 입력해 주세요.\n\n예) /roulette 7 3'

shotErrorMsg = '/roulette 명령어를 사용해 먼저 장전해 주세요.'
shotRealMsg = '이번 격발 결과는 실탄입니다.'
shotBlindMsg = '이번 격발 결과는 공포탄입니다.'

# coin toss message
coinTossHelpMsg = "🪙 동전 던지기 도움말 \n\n" \
                  "명령어 형식\n/coin_toss\n\n" \
                  "설명\n동전을 던진 결과를 제공합니다. 따로 입력할 사항은 없으며, " \
                  "가끔 특이한 결과가 나올 수도 있습니다."

# bad word detector message
badWordDetectorHelpMsg = "🤬 나쁜말 감지기 도움말 \n\n" \
                         "명령어 형식\n/없음\n\n" \
                         "설명\n설정된 시간 제한 이내에 다수의 나쁜말이 감지된 경우 자제할 것을 촉구하는 메시지를 보냅니다.\n" \
                         "차후 감지기를 고도화할 예정에 있습니다."

# geolocation message
geolocationHelpMsg = "📍 현재 위치 정보 도움말 \n\n" \
                     "명령어 형식\n/없음\n\n" \
                     "설명\n텔레그램의 위치 기능을 사용하여 현재 위치를 메시지로 보낸 경우 그 상세 정보를 메시지로 보냅니다.\n" \
                     "제공하는 정보는 주소, 경위도, 날씨입니다."

# D-day message
dayHelpMsg = "📅 D-Day 도움말 \n\n" \
             "명령어 형식\n/dday [연] [월] [일]\n\n" \
             "설명\n입력한 날짜의 오늘 기준 D-day를 계산합니다."
dayOutOfRangeMsg = "날짜를 잘못 입력했습니다. 확인 후 다시 입력해 주세요.\n\n" \
                   "예) /dday 2020 1 23"
dayLeftMsg = "일 남았습니다."
dayPassedMsg = "일 지났습니다."
dayDestMsg = "그 날이 바로 오늘입니다."

# Simplified calculator message
calcHelpMsg = "🧮 계산기 도움말 \n\n" \
              "명령어 형식\n(수식)\n\n" \
              "설명\n수식을 입력하면 자동으로 인식하여 결과를 반환합니다."
calcSyntaxErrorMsg = "구문 오류입니다. 수식을 정확하게 입력했는지 다시 확인해 주세요."
calcDivisionByZeroErrorMsg = "0으로 나눌 수 없습니다."

# # recommend info message
# gaechuInfoHelpMsg = "* 추천 및 비추천 글 정보 도움말 \n\n" \
#                     "명령어 형식\n준비 중\n\n" \
#                     "설명\n준비 중입니다."

# Resources

# Customized keyboards (inline)

mainKeyboard = telebot.types.InlineKeyboardMarkup()

mainKeyboard.row(
    telebot.types.InlineKeyboardButton('가까운 강 수온 알림', callback_data='get_nearby_temp'),
    telebot.types.InlineKeyboardButton('선택봇', callback_data='random_picker')
)
mainKeyboard.row(
    telebot.types.InlineKeyboardButton('러시안 룰렛 게임', callback_data='russian_roulette'),
    telebot.types.InlineKeyboardButton('동전 뒤집기', callback_data='coin_toss')
)
mainKeyboard.row(
    telebot.types.InlineKeyboardButton('나쁜말 감지기', callback_data='bad_word_detector'),
    telebot.types.InlineKeyboardButton('현재 위치 정보', callback_data='geolocation')
)
mainKeyboard.row(
    telebot.types.InlineKeyboardButton('D-day', callback_data='dday'),
    telebot.types.InlineKeyboardButton('계산기', callback_data='calc')
)
# mainKeyboard.row(
#     telebot.types.InlineKeyboardButton('추천 및 비추천 글 정보', callback_data='gaechu_info'),
# )


# Magic conch reaction
magicConchSentence = [['응', '그래', '언젠가는', '그럼'],
                      ['잘 모르겠다', '하고싶은대로', '다시 한번 물어봐'],
                      ['안 돼', '안.돼.', '아니', '가만히 있어']]

# Coin toss reaction
coinTossResult = ['앞면', '뒷면', '앞면', '뒷면', '앞면', '뒷면', '앞면', '뒷면',
                  '앞면', '뒷면', '앞면', '뒷면', '앞면', '뒷면', '앞면', '뒷면',
                  '앞면', '뒷면', '앞면', '뒷면', '앞면', '뒷면', '앞면', '뒷면', '수직으로 섰음']

# Meme reaction list
memeReaction = []

# K-Fword list
koreanFWord = ['시발', '씨발', '병신',
               '지랄', '개새끼', '색갸',
               '새꺄', '시바', '새끼',
               'tq', 'tlqkf', 'ㅅㅂ',
               '좆', '좃', '등신',
               '씹', '염병', '호로',
               '간나새끼']
anitiationWord = ['아니', '않이']
stopFWord = ['좀 진정해', '왜 욕해', '나쁜말 그만해']
stopAnitiation = ['제발 진정해', '왜 화났어', '너도 한국인이구나']
