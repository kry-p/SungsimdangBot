# Strings and shared resources for this bot
# Modify at your OWN RISK!

import telebot

# Main strings

# Message for checking bot status
working_msg = "성심당봇이 정상 작동 중입니다."

# Generic error message
generic_error_msg = "요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

# Guideline message
start_msg = (
    "성심당봇이에요! 무엇을 도와드릴까요?\n\n"
    "1. 🌡 가까운 강 수온 알림 \n"
    "2. ✅ 선택봇  \n"
    "3. 🔫 러시안 룰렛 게임 \n"
    "4. 🪙 동전뒤집기  \n"
    "5. 📍 현재 위치 정보  \n"
    "6. 📅 D-day \n"
    "7. 🧮 계산기 \n"
    "8. 🤖 AI 질문 \n"
    "9. 🔎 검색 \n"
    "10. 📚 나무위키 검색 \n\n"
    "이외에도 많은 기능이 업데이트로 추가 제공될 예정입니다."
)

# Function strings

# nearby river temperature message
temperature_help_msg = (
    "🌡 가까운 강 수온 알림 도움말 \n\n"
    "명령어 형식\n없음\n\n"
    "설명\n가까운 강 온도 정보를 제공합니다. '수온'이나 '자살'이 포함된 키워드를 "
    "입력할 경우 해당 사용자와 가까운 강의 온도 정보가 제공됩니다. \n"
    "사용자 정보 등록이 필요하며, 관련 사항은 봇 운영자에게 문의해 주세요."
)

# picker message
picker_help_msg = (
    "✅ 선택봇 도움말 \n\n"
    "명령어 형식\n/pick [단어1] [단어2] [단어3] ... [단어n]\n\n"
    "설명\n1개 이상의 단어 중 하나를 무작위로 선택합니다. 선택장애를 위한 필수 아이템!\n"
)
picker_error_msg = "올바르게 입력되지 않았어요. 다시 확인해 주세요.\n\n예) /pick 튀김소보로 부추빵 모카번"

# russian roulette message
roulette_help_msg = (
    "🔫 러시안 룰렛 도움말 \n\n"
    "명령어 형식\n/roulette [총 회전 수] [실탄 수]\n\n"
    "설명\n러시안 룰렛 게임입니다. 총 회전 수에는 내기에 참여할 사람 수를 입력하고, "
    "실탄 수는 당첨될 사람 수를 입력합니다. \n"
    "장전 후 격발은 /shoot 명령어를, \n"
    "룰렛 초기화는 /flush_bullet 명령어나 /roulette 0 0를 입력해 주세요."
)
roulette_error_msg = "명령어를 형식에 맞게 입력해 주세요.\n\n예) /roulette 7 3"
roulette_bullet_overflow_msg = "실탄 수가 총 회전 수보다 많습니다. 확인 후 다시 입력해 주세요."

roulette_flush_msg = "약실을 비웠습니다. 사용하려면 다시 장전해주세요."
roulette_loaded_msg = "{}발이 장전되었습니다."

shot_error_msg = "/roulette 명령어를 사용해 먼저 장전해 주세요."
shot_real_msg = "이번 격발 결과는 실탄입니다."
shot_blind_msg = "이번 격발 결과는 공포탄입니다."

# coin toss message
coin_toss_prefix_msg = "동전뒤집기 결과 : "

# keyword triggers
temp_keywords = ("수온", "자살")
magic_conch_keywords = ("마법의 소라고둥", "마법의 소라고동")

# suon (river temperature) message
suon_maintenance_status = "점검중"
suon_unavailable_msg = "현재 한강 수온 정보를 가져올 수 없습니다. (사유: 정보 미제공)"
suon_result_msg = "현재 한강 수온은 {} 도입니다."

# search result header
coin_toss_help_msg = (
    "🪙 동전 던지기 도움말 \n\n"
    "명령어 형식\n/coin_toss\n\n"
    "설명\n동전을 던진 결과를 제공합니다. 따로 입력할 사항은 없으며, "
    "가끔 특이한 결과가 나올 수도 있습니다."
)

# geolocation message
geolocation_help_msg = (
    "📍 현재 위치 정보 도움말 \n\n"
    "명령어 형식\n/없음\n\n"
    "설명\n텔레그램의 위치 기능을 사용하여 현재 위치를 메시지로 보낸 경우 그 상세 정보를 메시지로 보냅니다.\n"
    "제공하는 정보는 주소, 경위도, 날씨입니다."
)

# D-day message
day_help_msg = (
    "📅 D-Day 도움말 \n\n명령어 형식\n/dday [연] [월] [일]\n\n설명\n입력한 날짜의 오늘 기준 D-day를 계산합니다."
)
day_out_of_range_msg = "날짜를 잘못 입력했습니다. 확인 후 다시 입력해 주세요.\n\n예) /dday 2020 1 23"
day_left_msg = "일 남았습니다."
day_passed_msg = "일 지났습니다."
day_dest_msg = "그 날이 바로 오늘입니다."

# Simplified calculator message
calc_help_msg = (
    "🧮 계산기 도움말 \n\n명령어 형식\n/calc (수식)\n\n설명\n수식을 입력하면 자동으로 인식하여 결과를 반환합니다."
)
calc_syntax_error_msg = (
    "구문 오류입니다. \n수식을 정확하게 입력했는지 확인해 주시고, "
    "상수의 상수배인 경우 곱셈 기호(*)가 있는지 확인해 주세요."
)
calc_division_by_zero_error_msg = "0으로 나눌 수 없습니다."

# geolocation error message
geolocation_error_msg = "위치 정보를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

# search error message
search_error_msg = "검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
search_mismatch_msg = "'{keyword}' 문서를 찾지 못했습니다. 이 문서를 찾으셨나요?\n\n"
search_no_result_msg = "검색 결과가 없습니다."
search_help_msg = (
    "🔎 검색 도움말 \n\n명령어 형식\n/search [검색어]\n\n설명\n검색어에 대한 결과를 링크와 함께 제공합니다."
)
namu_help_msg = (
    "📚 나무위키 검색 도움말 \n\n명령어 형식\n/namu [검색어]\n\n설명\n나무위키에서 검색한 결과를 제공합니다."
)
search_result_header_msg = "검색 결과입니다.\n\n"

# ask (Gemini Q&A) message
ask_help_msg = (
    "🤖 AI 질문 도움말 \n\n"
    "명령어 형식\n/ask [질문]\n\n"
    "설명\nAI에게 질문하면 답변을 제공합니다. "
    "대화 맥락이 유지되므로 이어서 질문할 수 있습니다.\n"
    "다른 메시지에 답장하면서 /ask를 사용하면 해당 메시지를 참조하여 답변합니다.\n"
    "사진에 캡션으로 /ask를 입력하거나, 사진 메시지에 답장하면 이미지를 분석합니다.\n"
    "대화 초기화는 /clear_chat 명령어를 사용해 주세요."
)
ask_context_format = "[참조된 메시지]\n{context}\n\n[질문]\n{question}"
ask_empty_msg = "질문을 입력해 주세요.\n\n예) /ask 오늘 날씨 어때?"
ask_photo_download_error_msg = "사진을 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
ask_error_msg = "AI 응답을 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
ask_timeout_msg = "AI 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
ask_client_error_msg = "AI 서비스 요청이 거부되었습니다. 잠시 후 다시 시도해 주세요."
ask_not_allowed_msg = "이 채팅에서는 AI 질문 기능을 사용할 수 없습니다."
ask_rate_limit_msg = "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요."
ask_clear_msg = "대화 기록이 초기화되었습니다."

# admin message
admin_only_msg = "관리자만 사용할 수 있는 명령어입니다."
admin_allow_chat_msg = "{name} ({chat_id}) 이(가) 허용 목록에 추가되었습니다."
admin_deny_chat_msg = "{name} ({chat_id}) 이(가) 허용 목록에서 제거되었습니다."
admin_deny_chat_not_found_msg = "채팅 {chat_id}이(가) 허용 목록에 없습니다."
admin_list_chats_msg = "허용된 채팅 목록:\n{}"
admin_list_chats_empty_msg = "허용된 채팅이 없습니다."
admin_allow_usage_msg = "사용법: /allow_chat [chat_id]"
admin_deny_usage_msg = "사용법: /deny_chat [chat_id]"
admin_allow_confirm_msg = "{name} ({chat_id})을(를) 허용 목록에 추가할까요?"
admin_deny_confirm_msg = "{name} ({chat_id})을(를) 허용 목록에서 제거할까요?"
admin_cancel_msg = "취소되었습니다."
admin_confirm_btn = "확인"
admin_cancel_btn = "취소"

# /ask_settings message
ask_settings_msg = "AI 질문 설정\n\n모델: {model}\n웹 검색: {search}\n추가 지시: {prompt}"
ask_settings_model_btn = "모델 변경"
ask_settings_search_btn = "웹 검색 설정"
ask_settings_allowlist_btn = "허용 목록 보기"

# model selection message
set_model_msg = "현재 모델: {model}\n사용할 모델을 선택해주세요."
set_model_done_msg = "모델이 {model}(으)로 변경되었습니다."
set_model_error_msg = "모델 목록을 가져올 수 없습니다."

# search grounding message
set_search_msg = "현재 웹 검색: {status}\n변경할 상태를 선택해주세요."
set_search_enabled_msg = "웹 검색이 활성화되었습니다. AI 응답에 검색 결과가 반영됩니다."
set_search_disabled_msg = "웹 검색이 비활성화되었습니다."
admin_enable_btn = "활성화"
admin_disable_btn = "비활성화"

# custom prompt message
ask_settings_prompt_btn = "추가 지시 수정"
ask_settings_prompt_edit_btn = "수정"
ask_settings_prompt_clear_btn = "초기화"
set_prompt_msg = "현재 추가 지시:\n{prompt}"
set_prompt_input_msg = "새로운 추가 지시를 입력해주세요."
set_prompt_done_msg = "추가 지시가 저장되었습니다. 새 대화부터 적용됩니다."
set_prompt_cleared_msg = "추가 지시가 초기화되었습니다."

# status labels
status_enabled = "활성화"
status_disabled = "비활성화"
status_empty = "(없음)"

# geolocation format
geolocation_weather_msg = "날씨 {weather}, 기온 {temp}, 체감온도 {feels_temp}, 습도 {humidity}"
geolocation_coords_msg = "위도 : {latitude}, 경도 : {longitude}"

# search result format
search_more_link_msg = "더 보기"
namu_result_msg = "[{keyword} - 나무위키]({url})\n\n{text}"

# grounding sources label
grounding_sources_label = "\n\n참고한 자료"

# user info message
myid_msg = "사용자 ID: {}"

# --- Laftel ---

laftel_portal_msg = "라프텔 기능을 선택해 주세요."
laftel_schedule_btn = "신작 편성표"
laftel_schedule_header_msg = "*{} 신작 편성표*\n\n"
laftel_schedule_entry_msg = "*{name}*  {rating}\n  {genres} {tags}\n  [보기](https://laftel.net/item/{item_id})\n\n"
laftel_schedule_empty_msg = "{}에 편성된 신작이 없습니다."
laftel_error_msg = "라프텔 정보를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
laftel_schedule_footer_msg = "_(총 {}개)_"
laftel_schedule_truncated_msg = "... 더 많은 작품은 laftel.net에서 확인해 주세요."
laftel_ranking_btn = "랭킹"
laftel_ranking_header_msg = "*{} 랭킹 Top 20*\n\n"
laftel_ranking_entry_msg = (
    "{rank}. *{name}*  {rating}\n   {genres} {tags}\n   [보기](https://laftel.net/item/{item_id})\n\n"
)
laftel_ranking_empty_msg = "랭킹 정보를 가져올 수 없습니다."
laftel_ranking_footer_msg = "_(총 {}개)_"
laftel_search_btn = "검색"
laftel_search_input_msg = "검색할 키워드를 입력해 주세요."
laftel_search_header_msg = '*"{}" 검색 결과*\n\n'
laftel_search_empty_msg = '"{}"에 대한 검색 결과가 없습니다.'
laftel_search_footer_msg = "_(총 {}개)_"
laftel_search_empty_input_msg = "검색할 키워드를 입력해 주세요."
laftel_search_again_btn = "다시 검색"
laftel_portal_btn = "포털로"
laftel_help_msg = "/laftel 명령어로 라프텔 편성표, 랭킹, 검색 기능을 이용할 수 있습니다."

# RSS feed translater message
bfrss_help_msg = "번역된 rss를 보여줍니다. 주기는 오전 9시(딜레이 약 2분)에 갱신됩니다."
bfrss_error_msg = "번역 서버에 연결할 수 없습니다."
bfrss_am = "오전"
bfrss_pm = "오후"
bfrss_header_msg = " HACKER NEWS ({month}월 {day}일 {time_of_day})\n\n"

# Resources

# Customized keyboards (inline)

main_keyboard = telebot.types.InlineKeyboardMarkup()

main_keyboard.row(
    telebot.types.InlineKeyboardButton("가까운 강 수온 알림", callback_data="get_nearby_temp"),
    telebot.types.InlineKeyboardButton("선택봇", callback_data="random_picker"),
)
main_keyboard.row(
    telebot.types.InlineKeyboardButton("러시안 룰렛 게임", callback_data="russian_roulette"),
    telebot.types.InlineKeyboardButton("동전 뒤집기", callback_data="coin_toss"),
)
main_keyboard.row(
    telebot.types.InlineKeyboardButton("현재 위치 정보", callback_data="geolocation"),
)
main_keyboard.row(
    telebot.types.InlineKeyboardButton("D-day", callback_data="dday"),
    telebot.types.InlineKeyboardButton("계산기", callback_data="calc"),
)
main_keyboard.row(
    telebot.types.InlineKeyboardButton("AI 질문", callback_data="ask"),
)
main_keyboard.row(
    telebot.types.InlineKeyboardButton("검색", callback_data="search"),
    telebot.types.InlineKeyboardButton("나무위키 검색", callback_data="namu"),
)
main_keyboard.row(
    telebot.types.InlineKeyboardButton("라프텔", callback_data="laftel_menu:portal"),
)


# Magic conch reaction
magic_conch_sentence = [
    ["응", "그래", "언젠가는", "그럼"],
    ["잘 모르겠다", "하고싶은대로", "다시 한번 물어봐"],
    ["안 돼", "안.돼.", "아니", "가만히 있어"],
]

# Coin toss reaction
coin_toss_result = [
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "앞면",
    "뒷면",
    "수직으로 섰음",
]
