import unittest

from utils import (
    normalize_string,
    parse_number,
    parse_date,
    is_valid_episode_data,
    compute_dedup_key,
    is_better_record,
)
from main import process_row


class TestNormalizeString(unittest.TestCase):
    def test_strips_leading_trailing_spaces(self):
        self.assertEqual(normalize_string("  hello  "), "hello")

    def test_collapses_internal_spaces(self):
        self.assertEqual(normalize_string("game  of   thrones"), "game of thrones")

    def test_lowercases(self):
        self.assertEqual(normalize_string("Breaking Bad"), "breaking bad")

    def test_already_clean(self):
        self.assertEqual(normalize_string("daredevil"), "daredevil")

    def test_empty_string(self):
        self.assertEqual(normalize_string(""), "")

    def test_only_spaces(self):
        self.assertEqual(normalize_string("   "), "")


class TestParseNumber(unittest.TestCase):
    def test_valid_positive_integer(self):
        self.assertEqual(parse_number("5"), 5)

    def test_zero_returns_zero(self):
        self.assertEqual(parse_number("0"), 0)

    def test_negative_returns_zero(self):
        self.assertEqual(parse_number("-1"), 0)

    def test_float_string_returns_zero(self):
        self.assertEqual(parse_number("3.5"), 0)

    def test_word_returns_zero(self):
        self.assertEqual(parse_number("one"), 0)

    def test_empty_returns_zero(self):
        self.assertEqual(parse_number(""), 0)

    def test_whitespace_returns_zero(self):
        self.assertEqual(parse_number("   "), 0)

    def test_double_minus_returns_zero(self):
        self.assertEqual(parse_number("--2"), 0)

    def test_whitespace_around_valid_number(self):
        self.assertEqual(parse_number("  7  "), 7)


class TestParseDate(unittest.TestCase):
    def test_valid_yyyy_mm_dd(self):
        self.assertEqual(parse_date("2022-01-15"), "2022-01-15")

    def test_valid_dd_mm_yyyy(self):
        self.assertEqual(parse_date("15-01-2022"), "2022-01-15")

    def test_slash_separator(self):
        self.assertEqual(parse_date("2022/01/15"), "2022-01-15")

    def test_space_separator(self):
        self.assertEqual(parse_date("2022 01 15"), "2022-01-15")

    def test_invalid_month(self):
        self.assertEqual(parse_date("2022-13-01"), "Unknown")

    def test_invalid_day(self):
        self.assertEqual(parse_date("2022-01-99"), "Unknown")

    def test_all_zeros(self):
        self.assertEqual(parse_date("0000-00-00"), "Unknown")

    def test_empty_string(self):
        self.assertEqual(parse_date(""), "Unknown")

    def test_non_date_string(self):
        self.assertEqual(parse_date("not a date"), "Unknown")

    def test_feb_29_leap_year(self):
        self.assertEqual(parse_date("2024-02-29"), "2024-02-29")

    def test_feb_29_non_leap_year(self):
        self.assertEqual(parse_date("2023-02-29"), "Unknown")

    def test_zero_year(self):
        self.assertEqual(parse_date("0000-01-01"), "Unknown")

    def test_extra_separators(self):
        self.assertEqual(parse_date("2022- 40 - 99"), "Unknown")


class TestIsValidEpisodeData(unittest.TestCase):
    def test_all_missing(self):
        self.assertFalse(is_valid_episode_data("", "", ""))

    def test_only_episode_number_valid(self):
        self.assertTrue(is_valid_episode_data("3", "", ""))

    def test_only_title_valid(self):
        self.assertTrue(is_valid_episode_data("", "Pilot", ""))

    def test_only_date_valid(self):
        self.assertTrue(is_valid_episode_data("", "", "2022-01-15"))

    def test_all_valid(self):
        self.assertTrue(is_valid_episode_data("3", "Pilot", "2022-01-15"))

    def test_episode_zero_is_missing(self):
        self.assertFalse(is_valid_episode_data("0", "", ""))

    def test_episode_non_numeric_is_missing(self):
        self.assertFalse(is_valid_episode_data("one", "", ""))

    def test_whitespace_title_is_missing(self):
        self.assertFalse(is_valid_episode_data("", "   ", ""))


class TestComputeDedupKey(unittest.TestCase):
    def test_both_season_and_episode(self):
        key = compute_dedup_key("breakingbad", 2, 5, "sometitle", "2022-01-01")
        self.assertEqual(key, ("breakingbad", 2, 5))

    def test_no_season(self):
        key = compute_dedup_key("breakingbad", 0, 5, "sometitle", "2022-01-01")
        self.assertEqual(key, ("breakingbad", 0, 5, "sometitle"))

    def test_no_episode(self):
        key = compute_dedup_key("breakingbad", 2, 0, "sometitle", "2022-01-01")
        self.assertEqual(key, ("breakingbad", 2, 0, "sometitle"))

    def test_neither_with_real_title(self):
        key = compute_dedup_key("breakingbad", 0, 0, "sometitle", "2022-01-01")
        self.assertEqual(key, ("breakingbad", 0, 0, "sometitle"))

    def test_neither_with_untitled_uses_air_date(self):
        key = compute_dedup_key("breakingbad", 0, 0, "untitledepisode", "2022-01-01")
        self.assertEqual(key, ("breakingbad", 0, 0, "air:2022-01-01"))


class TestIsBetterRecord(unittest.TestCase):
    def _rec(self, air_date="Unknown", title="untitledepisode", season=0, episode=0):
        return {
            "air_date": air_date,
            "episode_title": title,
            "season_number": season,
            "episode_number": episode,
        }

    def test_new_wins_on_air_date(self):
        new = self._rec(air_date="2022-01-01")
        old = self._rec(air_date="Unknown")
        self.assertTrue(is_better_record(new, old))

    def test_old_wins_on_air_date(self):
        new = self._rec(air_date="Unknown")
        old = self._rec(air_date="2022-01-01")
        self.assertFalse(is_better_record(new, old))

    def test_new_wins_on_title(self):
        new = self._rec(title="pilot")
        old = self._rec(title="untitledepisode")
        self.assertTrue(is_better_record(new, old))

    def test_old_wins_on_title(self):
        new = self._rec(title="untitledepisode")
        old = self._rec(title="pilot")
        self.assertFalse(is_better_record(new, old))

    def test_new_wins_on_both_numbers(self):
        new = self._rec(season=1, episode=2)
        old = self._rec(season=1, episode=0)
        self.assertTrue(is_better_record(new, old))

    def test_old_wins_on_both_numbers(self):
        new = self._rec(season=0, episode=2)
        old = self._rec(season=1, episode=2)
        self.assertFalse(is_better_record(new, old))

    def test_only_season_vs_only_episode_is_tie(self):
        new = self._rec(season=1, episode=0)
        old = self._rec(season=0, episode=2)
        self.assertFalse(is_better_record(new, old))

    def test_full_tie_keeps_existing(self):
        new = self._rec(air_date="2022-01-01", title="pilot", season=1, episode=2)
        old = self._rec(air_date="2022-01-01", title="pilot", season=1, episode=2)
        self.assertFalse(is_better_record(new, old))


class TestProcessRow(unittest.TestCase):
    def test_discard_empty_series(self):
        self.assertIsNone(process_row(["", "1", "2", "Pilot", "2022-01-01"]))

    def test_discard_whitespace_series(self):
        self.assertIsNone(process_row(["   ", "1", "2", "Pilot", "2022-01-01"]))

    def test_discard_all_episode_data_missing(self):
        self.assertIsNone(process_row(["breakingbad", "1", "", "", ""]))

    def test_valid_row_no_corrections(self):
        result = process_row(["breakingbad", "2", "5", "pilot", "2022-01-15"])
        self.assertIsNotNone(result)
        record, corrections = result
        self.assertEqual(record["series_name"], "breakingbad")
        self.assertEqual(record["season_number"], 2)
        self.assertEqual(record["episode_number"], 5)
        self.assertEqual(record["episode_title"], "pilot")
        self.assertEqual(record["air_date"], "2022-01-15")
        self.assertEqual(corrections, 0)

    def test_valid_row_with_corrections(self):
        # series has extra spaces, season is negative, title is uppercase, date is invalid
        result = process_row(["Breaking Bad", "-1", "3", "PILOT", "not-a-date"])
        self.assertIsNotNone(result)
        record, corrections = result
        self.assertEqual(record["series_name"], "breaking bad")
        self.assertEqual(record["season_number"], 0)
        self.assertEqual(record["episode_title"], "pilot")
        self.assertEqual(record["air_date"], "Unknown")
        self.assertEqual(corrections, 4)  # series, season, title, air_date

    def test_missing_title_becomes_untitledepisode(self):
        result = process_row(["breakingbad", "1", "2", "", "2022-01-15"])
        self.assertIsNotNone(result)
        record, corrections = result
        self.assertEqual(record["episode_title"], "untitledepisode")
        self.assertEqual(corrections, 1)  # title corrected

    def test_fewer_than_5_fields_padded(self):
        result = process_row(["breakingbad", "1", "2"])
        self.assertIsNotNone(result)
        record, _ = result
        self.assertEqual(record["episode_title"], "untitledepisode")
        self.assertEqual(record["air_date"], "Unknown")

    def test_zero_season_not_counted_as_correction(self):
        result = process_row(["breakingbad", "0", "3", "pilot", "2022-01-15"])
        self.assertIsNotNone(result)
        _, corrections = result
        self.assertEqual(corrections, 0)


if __name__ == "__main__":
    unittest.main()
