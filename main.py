import os
import sys
import csv

from utils import (
    normalize_string,
    parse_number,
    parse_date,
    is_valid_episode_data,
    compute_dedup_key,
    is_better_record,
)


def find_csv_file(input_dir):
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".csv"):
            return os.path.join(input_dir, filename)
    return None


def _is_number_corrected(raw, result):
    stripped = raw.strip()
    try:
        original = int(stripped)
    except ValueError:
        return stripped != "" or result != 0
    return original != result


def process_row(raw_fields):
    while len(raw_fields) < 5:
        raw_fields.append("")

    raw_series, raw_season, raw_episode, raw_title, raw_air_date = raw_fields[:5]

    # Step 1: discard if no series name
    if not raw_series.strip():
        return None

    # Step 2: discard if no identifiable episode data
    if not is_valid_episode_data(raw_episode, raw_title, raw_air_date):
        return None

    # Step 3: normalize and correct, track corrections per field
    corrections = 0

    series_name = normalize_string(raw_series)
    if series_name != raw_series:
        corrections += 1

    season_number = parse_number(raw_season)
    if _is_number_corrected(raw_season, season_number):
        corrections += 1

    episode_number = parse_number(raw_episode)
    if _is_number_corrected(raw_episode, episode_number):
        corrections += 1

    title_norm = normalize_string(raw_title)
    if not title_norm:
        episode_title = "untitled episode"
    else:
        episode_title = title_norm
    if episode_title != raw_title:
        corrections += 1

    air_date = parse_date(raw_air_date)
    if air_date != raw_air_date.strip():
        corrections += 1

    record = {
        "series_name": series_name,
        "season_number": season_number,
        "episode_number": episode_number,
        "episode_title": episode_title,
        "air_date": air_date,
    }

    return (record, corrections)


def build_catalog(csv_path):
    catalog = {}
    metrics = {
        "total_input": 0,
        "discarded": 0,
        "corrected_fields": 0,
        "duplicates_detected": 0,
    }

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for raw_fields in reader:
            metrics["total_input"] += 1

            result = process_row(raw_fields)
            if result is None:
                metrics["discarded"] += 1
                continue

            record, corrections = result
            metrics["corrected_fields"] += corrections

            key = compute_dedup_key(
                record["series_name"],
                record["season_number"],
                record["episode_number"],
                record["episode_title"],
                record["air_date"],
            )

            if key not in catalog:
                catalog[key] = record
            else:
                metrics["duplicates_detected"] += 1
                if is_better_record(record, catalog[key]):
                    catalog[key] = record

    return catalog, metrics


def write_clean_csv(catalog, output_dir):
    rows = sorted(
        catalog.values(),
        key=lambda r: (r["series_name"], r["season_number"], r["episode_number"]),
    )
    output_path = os.path.join(output_dir, "episodes_clean.csv")
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["SeriesName", "SeasonNumber", "EpisodeNumber", "EpisodeTitle", "AirDate"])
        for r in rows:
            writer.writerow([
                r["series_name"],
                r["season_number"],
                r["episode_number"],
                r["episode_title"],
                r["air_date"],
            ])


def write_report(metrics, output_dir):
    dedup_strategy = (
        "Episodes are considered duplicates when they share the same normalized series name and\n"
        "a combination of season number, episode number, and/or episode title, depending on which\n"
        "fields are available. When both season and episode numbers are known (non-zero), identity\n"
        "is determined solely by those two numbers together with the series name. When one of the\n"
        "two numbers is zero (unknown), the episode title is added to the key to improve precision.\n"
        "When both numbers are zero, the episode title is used if it is known; otherwise the air date\n"
        "is used as a last resort. Among duplicate records, the one with the most complete information\n"
        "is kept: a known air date is preferred over \"Unknown\", a real title over \"untitled episode\",\n"
        "and a record with both a valid season and episode number over one missing either. When all\n"
        "else is equal, the first record encountered in the file is kept."
    )

    output_path = os.path.join(output_dir, "report.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Data Quality Report\n\n")
        f.write(f"- **Total input records**: {metrics['total_input']}\n")
        f.write(f"- **Total output records**: {metrics['total_output']}\n")
        f.write(f"- **Discarded entries**: {metrics['discarded']}\n")
        f.write(f"- **Corrected fields**: {metrics['corrected_fields']}\n")
        f.write(f"- **Duplicates detected**: {metrics['duplicates_detected']}\n")
        f.write("\n## Deduplication Strategy\n\n")
        f.write(dedup_strategy + "\n")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input")
    output_dir = os.path.join(script_dir, "output")

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    csv_path = find_csv_file(input_dir)
    if csv_path is None:
        print("Error: no .csv file found in the input/ folder.")
        sys.exit(1)

    print(f"Processing: {os.path.basename(csv_path)}")

    catalog, metrics = build_catalog(csv_path)  # most important logic
    metrics["total_output"] = len(catalog)  # it adds the final metric to metrics

    write_clean_csv(catalog, output_dir)
    write_report(metrics, output_dir)

    print(f"  Input records   : {metrics['total_input']}")
    print(f"  Output records  : {metrics['total_output']}")
    print(f"  Discarded       : {metrics['discarded']}")
    print(f"  Corrected fields: {metrics['corrected_fields']}")
    print(f"  Duplicates      : {metrics['duplicates_detected']}")
    print("Done. Output written to output/")


if __name__ == "__main__":
    main()
