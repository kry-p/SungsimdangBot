# module for random based features
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import random
from resources import strings


class RandomBasedFeatures:
    def __init__(self):
        self.Bullet = list()

    # Random picker 랜덤픽
    @staticmethod
    def picker(msg):
        random.seed()
        split = msg.split()
        split = [item for item in split if '/pick' not in item]

        try:
            choice = random.choice(split)
        except IndexError:
            return strings.pickerErrorMsg

        return choice

    # Coin toss-up 동전뒤집기
    @staticmethod
    def coin_toss():
        random.seed()
        return '동전뒤집기 결과 : ' + random.choice(strings.coinTossResult)

    # Spongebob SquarePants magic conch 마법의 소라고동
    @staticmethod
    def magic_conch():
        random.seed()
        init_rand = random.randrange(0, 3)
        return strings.magicConchSentence[init_rand][
            random.randrange(0, len(strings.magicConchSentence[init_rand]))]

    # Russian roulette 러시안 룰렛
    def russian_roulette(self, message):
        try:
            if message.split()[1].isdigit() and message.split()[2].isdigit():
                if message.split()[1] == 0 and message.split()[2] == 0:
                    self.Bullet = ()
                    return "약실을 비웠습니다. 사용하려면 다시 장전해주세요."
                self.Bullet = list()
                for n in range(int(message.split()[1])):
                    self.Bullet.append(False)
                for n in range(int(message.split()[2])):
                    self.Bullet[n] = True
                random.shuffle(self.Bullet)
                return '{}발이 장전되었습니다.'.format(len(self.Bullet))
        except IndexError:
            return strings.rouletteErrorMsg

    # Launch roulette 러시안 룰렛 격발
    def trig_bullet(self):
        if len(self.Bullet) == 0:
            return strings.shotErrorMsg
        check = self.Bullet.pop()
        if check:
            return strings.shotRealMsg
        else:
            return strings.shotBlindMsg
