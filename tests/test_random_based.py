import pytest

from modules.random_based import RandomBasedFeatures
from resources import strings


class TestPicker:
    def test_picks_from_options(self):
        result = RandomBasedFeatures.picker("/pick 튀김소보로 부추빵 모카번")
        assert result in ["튀김소보로", "부추빵", "모카번"]

    def test_single_option(self):
        assert RandomBasedFeatures.picker("/pick 튀김소보로") == "튀김소보로"

    def test_no_option_returns_error(self):
        assert RandomBasedFeatures.picker("/pick") == strings.picker_error_msg


class TestCoinToss:
    def test_returns_valid_result(self):
        result = RandomBasedFeatures.coin_toss()
        assert result.startswith("동전뒤집기 결과 : ")
        value = result.replace("동전뒤집기 결과 : ", "")
        assert value in strings.coin_toss_result


class TestMagicConch:
    def test_returns_known_sentence(self):
        all_sentences = [s for group in strings.magic_conch_sentence for s in group]
        result = RandomBasedFeatures.magic_conch()
        assert result in all_sentences


class TestRussianRoulette:
    def test_load_bullets(self):
        feat = RandomBasedFeatures()
        result = feat.russian_roulette("/roulette 6 1")
        assert result == "6발이 장전되었습니다."
        assert len(feat.Bullet) == 6
        assert feat.Bullet.count(True) == 1

    def test_shoot_without_loading(self):
        feat = RandomBasedFeatures()
        assert feat.trig_bullet() == strings.shot_error_msg

    def test_shoot_returns_real_or_blind(self):
        feat = RandomBasedFeatures()
        feat.russian_roulette("/roulette 1 1")
        result = feat.trig_bullet()
        assert result in [strings.shot_real_msg, strings.shot_blind_msg]

    def test_invalid_input(self):
        feat = RandomBasedFeatures()
        assert feat.russian_roulette("/roulette") == strings.roulette_error_msg

    def test_all_bullets_exhausted(self):
        feat = RandomBasedFeatures()
        feat.russian_roulette("/roulette 3 1")
        results = [feat.trig_bullet() for _ in range(3)]
        assert results.count(strings.shot_real_msg) == 1
        assert results.count(strings.shot_blind_msg) == 2
        # after all exhausted, should return error
        assert feat.trig_bullet() == strings.shot_error_msg

    @pytest.mark.xfail(
        reason="flush_bullet compares str with int: message.split()[1] == 0",
        strict=True,
    )
    def test_flush_bullet(self):
        feat = RandomBasedFeatures()
        feat.russian_roulette("/roulette 3 1")
        result = feat.russian_roulette("/roulette 0 0")
        assert result == "약실을 비웠습니다. 사용하려면 다시 장전해주세요."


class TestPickerEdgeCases:
    def test_whitespace_only_input(self):
        assert RandomBasedFeatures.picker("/pick   ") == strings.picker_error_msg

    def test_special_characters(self):
        result = RandomBasedFeatures.picker("/pick @#$ %^&")
        assert result in ["@#$", "%^&"]
