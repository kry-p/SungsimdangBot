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
        assert result.startswith(strings.coin_toss_prefix_msg)
        value = result.replace(strings.coin_toss_prefix_msg, "")
        assert value in strings.coin_toss_result


class TestMagicConch:
    def test_returns_known_sentence(self):
        all_sentences = [s for group in strings.magic_conch_sentence for s in group]
        result = RandomBasedFeatures.magic_conch()
        assert result in all_sentences


class TestRussianRoulette:
    CHAT_ID = 1

    def test_load_bullets(self):
        feat = RandomBasedFeatures()
        result = feat.russian_roulette(self.CHAT_ID, "/roulette 6 1")
        assert result == strings.roulette_loaded_msg.format(6)
        assert len(feat.bullet[self.CHAT_ID]) == 6
        assert feat.bullet[self.CHAT_ID].count(True) == 1

    def test_shoot_without_loading(self):
        feat = RandomBasedFeatures()
        assert feat.trig_bullet(self.CHAT_ID) == strings.shot_error_msg

    def test_shoot_returns_real_or_blind(self):
        feat = RandomBasedFeatures()
        feat.russian_roulette(self.CHAT_ID, "/roulette 1 1")
        result = feat.trig_bullet(self.CHAT_ID)
        assert result in [strings.shot_real_msg, strings.shot_blind_msg]

    def test_invalid_input(self):
        feat = RandomBasedFeatures()
        assert feat.russian_roulette(self.CHAT_ID, "/roulette") == strings.roulette_error_msg

    def test_all_bullets_exhausted(self):
        feat = RandomBasedFeatures()
        feat.russian_roulette(self.CHAT_ID, "/roulette 3 1")
        results = [feat.trig_bullet(self.CHAT_ID) for _ in range(3)]
        assert results.count(strings.shot_real_msg) == 1
        assert results.count(strings.shot_blind_msg) == 2
        # after all exhausted, should return error
        assert feat.trig_bullet(self.CHAT_ID) == strings.shot_error_msg

    def test_flush_bullet(self):
        feat = RandomBasedFeatures()
        feat.russian_roulette(self.CHAT_ID, "/roulette 3 1")
        result = feat.russian_roulette(self.CHAT_ID, "/roulette 0 0")
        assert result == strings.roulette_flush_msg

    def test_bullet_overflow(self):
        feat = RandomBasedFeatures()
        result = feat.russian_roulette(self.CHAT_ID, "/roulette 3 5")
        assert result == strings.roulette_bullet_overflow_msg

    def test_per_chat_isolation(self):
        feat = RandomBasedFeatures()
        feat.russian_roulette(1, "/roulette 6 1")
        feat.russian_roulette(2, "/roulette 3 2")
        assert len(feat.bullet[1]) == 6
        assert feat.bullet[1].count(True) == 1
        assert len(feat.bullet[2]) == 3
        assert feat.bullet[2].count(True) == 2

    def test_shoot_unknown_chat(self):
        feat = RandomBasedFeatures()
        assert feat.trig_bullet(999) == strings.shot_error_msg


class TestPickerEdgeCases:
    def test_whitespace_only_input(self):
        assert RandomBasedFeatures.picker("/pick   ") == strings.picker_error_msg

    def test_special_characters(self):
        result = RandomBasedFeatures.picker("/pick @#$ %^&")
        assert result in ["@#$", "%^&"]
