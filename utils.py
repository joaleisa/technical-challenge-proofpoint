import re
import datetime


def normalize_string(s):
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    return s.lower()


def parse_number(value):
    stripped = value.strip()
    try:
        result = int(stripped)
    except ValueError:
        return 0
    if result <= 0:
        return 0
    return result


def parse_date(value):
    stripped = value.strip()
    if not stripped:
        return "Unknown"
    tokens = re.split(r'[\s/\-]+', stripped)
    if len(tokens) != 3:
        return "Unknown"
    try:
        if len(tokens[0]) == 4:
            year, month, day = int(tokens[0]), int(tokens[1]), int(tokens[2])
        else:
            day, month, year = int(tokens[0]), int(tokens[1]), int(tokens[2])
    except ValueError:
        return "Unknown"
    try:
        datetime.datetime(year, month, day)
    except ValueError:
        return "Unknown"
    if year <= 0:
        return "Unknown"
    return f"{year:04d}-{month:02d}-{day:02d}"


def is_valid_episode_data(raw_ep_num, raw_title, raw_air_date):
    if parse_number(raw_ep_num) > 0:
        return True
    if raw_title.strip():
        return True
    if parse_date(raw_air_date) != "Unknown":
        return True
    return False


def compute_dedup_key(series_norm, season, episode_num, title_norm, air_date):
    if season != 0 and episode_num != 0:
        return (series_norm, season, episode_num)
    if season == 0 and episode_num != 0:
        return (series_norm, 0, episode_num, title_norm)
    if season != 0 and episode_num == 0:
        return (series_norm, season, 0, title_norm)
    if title_norm != "untitledepisode":
        return (series_norm, 0, 0, title_norm)
    return (series_norm, 0, 0, "air:" + air_date)


def is_better_record(new_rec, existing_rec):
    new_has_date = new_rec["air_date"] != "Unknown"
    old_has_date = existing_rec["air_date"] != "Unknown"
    if new_has_date and not old_has_date:
        return True
    if not new_has_date and old_has_date:
        return False

    new_has_title = new_rec["episode_title"] != "untitledepisode"
    old_has_title = existing_rec["episode_title"] != "untitledepisode"
    if new_has_title and not old_has_title:
        return True
    if not new_has_title and old_has_title:
        return False

    new_has_both = new_rec["season_number"] != 0 and new_rec["episode_number"] != 0
    old_has_both = existing_rec["season_number"] != 0 and existing_rec["episode_number"] != 0
    if new_has_both and not old_has_both:
        return True
    if not new_has_both and old_has_both:
        return False

    return False
