# module for random based features
import random

from resources import strings


class RandomBasedFeatures:
    def __init__(self):
        self.bullet = []

    # Random picker 랜덤픽
    @staticmethod
    def picker(msg):
        random.seed()
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
        random.seed()
        return strings.coin_toss_prefix_msg + random.choice(strings.coin_toss_result)

    # Spongebob SquarePants magic conch 마법의 소라고동
    @staticmethod
    def magic_conch():
        random.seed()
        init_rand = random.randrange(0, 3)
        return strings.magic_conch_sentence[init_rand][
            random.randrange(0, len(strings.magic_conch_sentence[init_rand]))
        ]

    # Russian roulette 러시안 룰렛
    def russian_roulette(self, message):
        try:
            if message.split()[1].isdigit() and message.split()[2].isdigit():
                if message.split()[1] == "0" and message.split()[2] == "0":
                    self.bullet = ()
                    return strings.roulette_flush_msg
                total = int(message.split()[1])
                bullets = int(message.split()[2])
                if bullets > total:
                    return strings.roulette_bullet_overflow_msg
                self.bullet = []
                for _n in range(total):
                    self.bullet.append(False)
                for n in range(bullets):
                    self.bullet[n] = True
                random.shuffle(self.bullet)
                return strings.roulette_loaded_msg.format(len(self.bullet))
        except IndexError:
            return strings.roulette_error_msg

    # Launch roulette 러시안 룰렛 격발
    def trig_bullet(self):
        if len(self.bullet) == 0:
            return strings.shot_error_msg
        check = self.bullet.pop()
        if check:
            return strings.shot_real_msg
        else:
            return strings.shot_blind_msg
