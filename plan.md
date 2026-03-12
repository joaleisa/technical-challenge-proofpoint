# Implementation Plan – Exercise B: The Streaming Service's Lost Episodes

## File Structure

```
project/
├── main.py       ← main() and orchestrating functions
├── utils.py      ← atomic, pure helper functions
├── tests.py      ← unit tests for individual functions
├── input/        ← place the input .csv here (created automatically)
└── output/       ← episodes_clean.csv and report.md (created automatically)
```

---

## Function Breakdown

### `utils.py`

```
utils.py
├── normalize_string(s)                                                  → str
├── parse_number(value)                                                  → int
├── parse_date(value)                                                    → str
├── is_valid_episode_data(raw_ep_num, raw_title, raw_air_date)           → bool
├── compute_dedup_key(series_norm, season, episode_num, title_norm, air_date) → tuple
└── is_better_record(new_rec, existing_rec)                              → bool
```

### `main.py`

```
main.py
├── find_csv_file(input_dir)             → str | None
├── process_row(raw_fields)              → (dict, int) | None
├── build_catalog(csv_path)              → (dict, dict)
├── write_clean_csv(catalog, output_dir)
├── write_report(metrics, output_dir)
└── main()
```

---

## Function Details

### `utils.py`

---

#### `normalize_string(s)`
- Strip leading/trailing whitespace.
- Collapse internal whitespace sequences to a single space.
- Lowercase.
- Return result.

---

#### `parse_number(value)`
- Strip the value.
- Try `int(value_stripped)` — pure integer conversion only (no float intermediary).
- If `ValueError` → return `0`. Catches: `""`, `" "`, `"one"`, `"3.5"`, `"--2"`.
- If parsed result `<= 0` → return `0`. Catches: `"-1"`, `"0"`.
- Otherwise return the integer.

> `"0"` → `int("0")` = `0` → returns `0` (not a correction, value unchanged).
> `"3.5"` → `ValueError` → returns `0` (correction counted).

---

#### `parse_date(value)`
- Strip value. If empty → return `"Unknown"`.
- Split into tokens using regex `r'[\s/\-]+'`.
- If not exactly 3 tokens → return `"Unknown"`.
- Determine format:
  - `len(tokens[0]) == 4` → year-first (`YYYY-MM-DD`)
  - Otherwise → day-first (`DD-MM-YYYY`)
- Parse `year`, `month`, `day` accordingly.
- Validate using `datetime.datetime(year, month, day)` inside `try/except ValueError`.
  - Catches: month 13, day 99, year 0, Feb 30, etc.
- If valid → return `f"{year:04d}-{month:02d}-{day:02d}"`.
- If invalid → return `"Unknown"`.

---

#### `is_valid_episode_data(raw_ep_num, raw_title, raw_air_date)`
- Returns `True` if **at least one** of the following holds:
  - `raw_ep_num.strip()` can be parsed as a positive integer (`parse_number` > 0).
  - `raw_title.strip()` is non-empty.
  - `parse_date(raw_air_date) != "Unknown"`.
- Returns `False` if all three fail (row will be discarded in Step 2).

---

#### `compute_dedup_key(series_norm, season, episode_num, title_norm, air_date)`

| Condition | Dedup Key |
|---|---|
| `season != 0 and episode_num != 0` | `(series_norm, season, episode_num)` |
| `season == 0 and episode_num != 0` | `(series_norm, 0, episode_num, title_norm)` |
| `season != 0 and episode_num == 0` | `(series_norm, season, 0, title_norm)` |
| `season == 0 and episode_num == 0 and title_norm != "untitledepisode"` | `(series_norm, 0, 0, title_norm)` |
| `season == 0 and episode_num == 0 and title_norm == "untitledepisode"` | `(series_norm, 0, 0, "air:" + air_date)` |

---

#### `is_better_record(new_rec, existing_rec)`
- Returns `True` if `new_rec` should replace `existing_rec`. Compare in order:
  1. `air_date != "Unknown"` beats `"Unknown"`.
  2. `episode_title != "untitledepisode"` beats `"untitledepisode"`.
  3. `season_number != 0 and episode_number != 0` beats any record where at least one is `0`.
     (Having only one non-zero does **not** win — both must be non-zero.)
  4. Tied → return `False` (keep existing = first encountered).

---

### `main.py`

---

#### `find_csv_file(input_dir)`
- Use `os.listdir(input_dir)`.
- Return the full path of the first file whose name ends in `.csv` (case-insensitive).
- Return `None` if none found.

---

#### `process_row(raw_fields)`
- Expects a list of raw string values. Pad with `""` if fewer than 5 fields.
- **Step 1**: if `raw_fields[0].strip()` is empty → return `None`.
- **Step 2**: call `is_valid_episode_data(raw_fields[2], raw_fields[3], raw_fields[4])`.
  If `False` → return `None`.
- **Step 3**: normalize each field, build the record dict, count corrections per field.

  | Field | Normalization | Correction check |
  |---|---|---|
  | `series_name` | `normalize_string(raw)` | changed if result `!= raw` |
  | `season_number` | `parse_number(raw)` | changed if `int(raw.strip()) != result` or raw not parseable as int |
  | `episode_number` | `parse_number(raw)` | same as season |
  | `episode_title` | `normalize_string(raw)` or `"untitledepisode"` | changed if result `!= raw` |
  | `air_date` | `parse_date(raw)` | changed if result `!= raw.strip()` |

- Return `(record_dict, corrections_count)` where `corrections_count` is the number of fields changed.

---

#### `build_catalog(csv_path)`
- Open and read CSV with `csv.reader`.
- Initialize `catalog = {}` and `metrics = {total_input, discarded, corrected_fields, duplicates_detected}`.
- For each row:
  - Increment `total_input`.
  - Call `process_row(row)`:
    - If `None` → increment `discarded`, continue.
    - Unpack `(record, corrections_count)`.
    - Add `corrections_count` to `corrected_fields`.
  - Call `compute_dedup_key(...)` with the record's fields.
  - If key **not** in catalog → `catalog[key] = record`.
  - If key **in** catalog → increment `duplicates_detected`; call `is_better_record(record, catalog[key])`:
    - If `True` → `catalog[key] = record`.
- Return `(catalog, metrics)`.

---

#### `write_clean_csv(catalog, output_dir)`
- Sort `catalog.values()` by `(series_name, season_number, episode_number)` ascending.
- Write to `output/episodes_clean.csv` using `csv.writer`.
- Header: `SeriesName,SeasonNumber,EpisodeNumber,EpisodeTitle,AirDate`.
- One row per record.
- Generated even if catalog is empty (header only).

---

#### `write_report(metrics, output_dir)`
- Write `output/report.md` with the following sections in order:
  1. Total input records
  2. Total output records
  3. Discarded entries
  4. Corrected fields
  5. Duplicates detected
  6. Deduplication strategy (static text from specs §10.2)
- Generated even if all counters are 0.

---

#### `main()`
- Resolve script directory: `os.path.dirname(os.path.abspath(__file__))`.
- Derive `input_dir = script_dir/input`, `output_dir = script_dir/output`.
- Create both dirs with `os.makedirs(..., exist_ok=True)`.
- Call `find_csv_file(input_dir)` → if `None`, print error and `sys.exit(1)`.
- Call `build_catalog(csv_path)` → `(catalog, metrics)`.
- Set `metrics["total_output"] = len(catalog)`.
- Call `write_clean_csv(catalog, output_dir)`.
- Call `write_report(metrics, output_dir)`.
- Print summary to stdout.

---

## Tests (`tests.py`)

One file with unit tests for the following functions from `utils.py` and `main.py`:

| Function | Cases to cover |
|---|---|
| `normalize_string` | extra spaces, uppercase, mixed, already clean |
| `parse_number` | valid int, `"0"`, negative, float string `"3.5"`, `"one"`, empty, whitespace |
| `parse_date` | valid YYYY-MM-DD, valid DD-MM-YYYY, invalid month, invalid day, `"0000-00-00"`, empty, non-date string |
| `is_valid_episode_data` | all missing, only episode valid, only title valid, only date valid, all valid |
| `compute_dedup_key` | each of the 5 key patterns |
| `is_better_record` | new wins on rule 1, rule 2, rule 3, tie (keep existing) |
| `process_row` | discard Step 1, discard Step 2, valid row no corrections, valid row with corrections, fewer than 5 fields |

---

## Dependencies

- Standard library only: `os`, `sys`, `csv`, `re`, `datetime`
- No external packages required.

---

## Implementation Order

1. `utils.py` — `normalize_string`, `parse_number`, `parse_date`
2. `utils.py` — `is_valid_episode_data`, `compute_dedup_key`, `is_better_record`
3. `main.py` — `find_csv_file`, skeleton of `main()` (directory creation, CSV discovery, error handling)
4. `main.py` — `process_row` (Steps 1–3, correction counting)
5. `main.py` — `build_catalog` (Step 4, dedup logic)
6. `main.py` — `write_clean_csv`, `write_report`
7. `tests.py` — unit tests for all functions above
8. End-to-end test with a hand-crafted CSV covering all edge cases from the specs
