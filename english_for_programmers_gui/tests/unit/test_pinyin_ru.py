# Русское чтение пиньиня: пиньинь превращается в примерное русское звучание.
# Один тест - одно правило. Проверяем, что русскому человеку понятно, как
# прочитать китайское слово "на глаз".

import unittest

from core.pinyin_ru import russian_reading


class RussianReadingTests(unittest.TestCase):
    def test_simple_syllable(self):
        self.assertEqual(russian_reading("nǐ"), "ни")
        self.assertEqual(russian_reading("hǎo"), "хао")

    def test_two_syllables_with_space(self):
        self.assertEqual(russian_reading("nǐ hǎo"), "ни хао")

    def test_written_together_is_split(self):
        """Слитный пиньинь разбивается на слоги: diànnǎo - это diàn + nǎo."""
        self.assertEqual(russian_reading("diànnǎo"), "дянь нао")
        self.assertEqual(russian_reading("xièxie"), "се се")

    def test_u_with_two_dots_stays_u_umlaut(self):
        """ü читается "юй", а не "у": nǚ - это "нюй", не "ну"."""
        self.assertEqual(russian_reading("nǚ"), "нюй")
        self.assertEqual(russian_reading("lǜ"), "люй")

    def test_reduced_vowel_after_retroflex(self):
        """zhi, chi, shi, ri читаются с почти неслышной гласной."""
        self.assertEqual(russian_reading("shì"), "шы")
        self.assertEqual(russian_reading("sì"), "сы")

    def test_j_q_x_with_u_means_u_umlaut(self):
        """После j, q, x буква u на самом деле ü: ju - это "цзю"."""
        self.assertEqual(russian_reading("qù"), "цю")
        self.assertEqual(russian_reading("xué"), "сюэ")

    def test_y_and_w_at_start(self):
        """y и w - это гласные i и u в начале слога."""
        self.assertEqual(russian_reading("yī"), "и")
        self.assertEqual(russian_reading("wǔ"), "у")
        self.assertEqual(russian_reading("yuè"), "юэ")

    def test_erhua_r_at_end(self):
        """Буква r на конце - эризация: nǎr читается "нар"."""
        self.assertEqual(russian_reading("nǎr"), "нар")
        self.assertEqual(russian_reading("diǎnr"), "дяньр")

    def test_compound_word(self):
        """péngyou (друг) - слоги peng + you."""
        self.assertEqual(russian_reading("péngyou"), "пэн ю")

    def test_zh_and_initials(self):
        """zh читается "чж", ong - "ун"."""
        self.assertEqual(russian_reading("zhōngwén"), "чжун уэнь")


if __name__ == "__main__":
    unittest.main()
