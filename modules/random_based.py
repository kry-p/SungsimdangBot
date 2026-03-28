# module for random based features
import json
import random

from modules.database import RouletteGame, db
from resources import strings


class RandomBasedFeatures:
    # Random picker 랜덤픽
    @staticmethod
    def picker(msg):
        split = msg.split()
        split = [item for item in split if "/pick" not in item]

        try:
            choice = random.choice(split)
        except IndexError:
            return strings.picker_error_msg

        return choice

    # Coin toss-up 동전뒤집기
    @staticmethod
    def coin_toss():
        return strings.coin_toss_prefix_msg + random.choice(strings.coin_toss_result)

    # Spongebob SquarePants magic conch 마법의 소라고동
    @staticmethod
    def magic_conch():
        init_rand = random.randrange(0, 3)
        return strings.magic_conch_sentence[init_rand][
            random.randrange(0, len(strings.magic_conch_sentence[init_rand]))
        ]

    # Russian roulette 러시안 룰렛
    def russian_roulette(self, chat_id, message):
        try:
            parts = message.split()
            if parts[1].isdigit() and parts[2].isdigit():
                if parts[1] == "0" and parts[2] == "0":
                    # IMMEDIATE: /shoot 동시 호출과의 경합 방지
                    with db.atomic("IMMEDIATE"):
                        RouletteGame.delete().where(RouletteGame.chat_id == chat_id).execute()
                    return strings.roulette_flush_msg
                total = int(parts[1])
                bullets = int(parts[2])
                if bullets > total:
                    return strings.roulette_bullet_overflow_msg
                bullet_list = [True] * bullets + [False] * (total - bullets)
                random.shuffle(bullet_list)
                # IMMEDIATE: /shoot 동시 호출과의 경합 방지
                with db.atomic("IMMEDIATE"):
                    RouletteGame.replace(chat_id=chat_id, bullets=json.dumps(bullet_list)).execute()
                return strings.roulette_loaded_msg.format(total)
        except IndexError:
            return strings.roulette_error_msg

    # Launch roulette 러시안 룰렛 격발
    def trig_bullet(self, chat_id):
        # IMMEDIATE: 읽기-수정-쓰기 전체를 원자적으로 처리하여
        # 동시 /shoot 호출 시 상태 덮어쓰기 방지
        with db.atomic("IMMEDIATE"):
            game = RouletteGame.get_or_none(RouletteGame.chat_id == chat_id)
            if not game:
                return strings.shot_error_msg
            bullets = json.loads(game.bullets)
            if not bullets:
                game.delete_instance()
                return strings.shot_error_msg
            check = bullets.pop()
            if bullets:
                game.bullets = json.dumps(bullets)
                game.save()
            else:
                game.delete_instance()
        if check:
            return strings.shot_real_msg
        else:
            return strings.shot_blind_msg
