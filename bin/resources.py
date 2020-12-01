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
           "2. 가까운 강 온도 \n" \
           "3. 러시안 룰렛 \n" \
           "4. 동전 뒤집기 \n" \
           "5. 추천 및 비추천 글 정보"

# Function list message
functionListMsg = "성심당봇은 아래와 같은 기능을 제공해요.\n\n" \
                  "- 랜덤픽 \n" \
                  "- 추천 및 비추천 글 정보 (미구현) \n" \
                  "- 밈 리액션 (미구현) \n" \
                  "- 가까운 강 온도 (구현 중) \n\n" \
                  "이외에도 숨겨진 기능이 있으니 잘 찾아 보세요!"


# Function strings

# picker message 
pickerErrorMsg = "올바르게 입력되지 않았어요. 다시 확인해 주세요.\n\n" \
           "예) /pick 튀김소보로 부추빵 모카번"

# river temperature message
tempErrorMsg = '현재 수온 정보를 가져올 수 없습니다.'

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
                  '앞면', '뒷면', '앞면', '뒷면', '앞면', '뒷면', '앞면', '뒷면', '중첩된 상태']

# Meme reaction list
memeReaction = []

# K-Fword list
koreanFWord = ['시발', '씨발', '병신', 
               '지랄', '개새끼','색갸', 
               '새꺄', '시바', '새끼', 
               'tq', 'tlqkf', 'ㅅㅂ']
anitiationWord = ['아니', '않이']