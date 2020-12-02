# Strings and shared resources for this bot
# Modify at your OWN RISK!

import telebot

# Main strings

# Message for checking bot status
workingMsg = "성심당봇이 정상 작동 중입니다."
notWorkingMsg = "성심당봇에 이상이 있습니다. 문제를 확인해 주세요."

# Guideline message
startMsg = "성심당봇이에요! 무엇을 도와드릴까요?\n\n" \
           "1. 랜덤픽 \n" \
           "2. 강 온도 \n" \
           "3. 러시안 룰렛 \n" \
           "4. 동전 뒤집기 \n" \
           "5. 추천 및 비추천 글 정보\n\n" \
           "이외에도 숨겨진 기능이 있으니 잘 찾아 보세요!"

# Function strings

# picker message
pickerHelpMsg = "* 랜덤픽 도움말 \n\n" \
                "명령어 형식\n/pick [단어1] [단어2] [단어3] ... [단어n]\n\n" \
                "설명\n1개 이상의 단어 중 하나를 무작위로 선택합니다. 선택장애를 위한 필수 아이템!\n"
pickerErrorMsg = "올바르게 입력되지 않았어요. 다시 확인해 주세요.\n\n" \
                 "예) /pick 튀김소보로 부추빵 모카번"

# russian roulette message
rouletteHelpMsg = "* 러시안 룰렛 도움말 \n\n" \
                "명령어 형식\n/roulette [총 회전 수] [실탄 수]\n\n" \
                "설명\n러시안 룰렛 게임입니다. 총 회전 수에는 내기에 참여할 사람 수를 입력하고, " \
                "실탄 수는 당첨될 사람 수를 입력합니다. \n" \
                "장전 후 격발은 /shoot 명령어를 사용해주시고, \n" \
                "룰렛 초기화는 /flush_bullet 명령어나 /roulette 0 0를 입력해주세요."
rouletteErrorMsg = '명령어를 형식에 맞게 입력해주세요.\n(ex. /roulette 7 3 장전탄수, 당첨탄수)'

shotErrorMsg = '/roulette 명령어를 사용해 먼저 장전해주세요.'
shotRealMsg = '이번 격발 결과는 실탄입니다.'
shotBlindMsg = '이번 격발 결과는 공포탄입니다.'

# nearby river temperature message
temperatureHelpMsg = "* 가까운 강 온도 도움말 \n\n" \
                     "명령어 형식\n없음\n\n" \
                     "설명\n가까운 강 온도 정보를 제공합니다. '수온'이나 '자살'이 포함된 키워드를 " \
                     "입력할 경우 해당 사용자와 가까운 강의 온도 정보가 제공됩니다. \n" \
                     "사용자 정보 등록이 필요하며, 관련 사항은 봇 운영자에게 문의해 주세요."

# coin toss message
coinTossHelpMsg = "* 동전 던지기 도움말 \n\n" \
                  "명령어 형식\n/coin_toss\n\n" \
                  "설명\n동전을 던진 결과를 제공합니다. 따로 입력할 사항은 없으며, " \
                  "가끔 특이한 결과가 나올 수도 있습니다."

# recommend info message/
gaechuInfoHelpMsg = "* 추천 및 비추천 글 정보 도움말 \n\n" \
                   "명령어 형식\n준비 중\n\n" \
                   "설명\n준비 중입니다."

# Resources

# Customized keyboards (inline)

mainKeyboard = telebot.types.InlineKeyboardMarkup()
 
mainKeyboard.row(
    telebot.types.InlineKeyboardButton('1. 랜덤픽', callback_data='random_picker'),
    telebot.types.InlineKeyboardButton('2. 가까운 강 온도', callback_data='get_nearby_temp')
    )
mainKeyboard.row(
    telebot.types.InlineKeyboardButton('3. 러시안 룰렛', callback_data='russian_roulette'),
    telebot.types.InlineKeyboardButton('4. 동전 뒤집기', callback_data='coin_toss')
    )
mainKeyboard.row(
    telebot.types.InlineKeyboardButton('5. 추천 및 비추천 글 정보', callback_data='gaechu_info')
    )

# User information
# ex) ['user_id', 'user_name', 'river_measure', 'river_alias', 'meme_list']
user = [['user_id', 'user_name', 'river_measure', 'river_alias', 'meme_list']]

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
               '지랄', '개새끼','색갸', 
               '새꺄', '시바', '새끼', 
               'tq', 'tlqkf', 'ㅅㅂ']
anitiationWord = ['아니', '않이']