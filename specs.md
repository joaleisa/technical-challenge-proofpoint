# Specs – Exercise B: The Streaming Service's Lost Episodes

## 1. Overview

A Python program (structured paradigm, no OOP, no database) split across two files:

- `main.py` — `main()` and the larger orchestrating functions.
- `utils.py` — small, atomic, pure helper functions.

The program reads a corrupted CSV catalog of streaming episodes, cleans and de-duplicates it,
and produces a clean CSV and a quality report in the `output/` folder.

---

## 2. File Structure

```
project/
├── main.py
├── utils.py
├── tests.py
├── input/          ← place the input .csv here
└── output/         ← episodes_clean.csv and report.md are written here
```

- `input/` and `output/` are created automatically by `main()` if they don't exist.
- The script scans `input/` for the first `.csv` file found.

---

## 3. Input

- **File discovery**: scan `input/` for the first `.csv` file (case-insensitive extension).
- **Encoding**: UTF-8.
- **Format**: comma-separated, **no header row** (data starts from row 1).
- **Expected columns (in order)**:
  `SeriesName, SeasonNumber, EpisodeNumber, EpisodeTitle, AirDate`

---

## 4. Processing Pipeline (per row)

Each row goes through the following sequential steps:

### Step 1 – Discard if no Series Name
If `SeriesName` stripped is empty → **discard** the row.

### Step 2 – Discard if no identifiable episode data
Check whether at least one of the following fields is valid (non-missing):
- `EpisodeNumber`: valid if it is a positive integer string (see §6).
- `EpisodeTitle`: valid if non-empty/non-whitespace.
- `AirDate`: valid if parseable as a date (see §7).

If **all three** are missing/invalid → **discard** the row.

> `0` and `"Unknown"` are treated as missing information for this check.

### Step 3 – Normalize and correct fields

Apply corrections in this order. Track how many fields were changed (for the report).

| Field | Rule |
|---|---|
| `SeriesName` | Trim + collapse internal spaces + lowercase |
| `SeasonNumber` | Parse as positive integer (see §6). If invalid → `0` |
| `EpisodeNumber` | Parse as positive integer (see §6). If invalid → `0` |
| `EpisodeTitle` | Trim + collapse spaces + lowercase. If empty after trim → `"untitledepisode"` |
| `AirDate` | Parse and validate (see §7). If invalid → `"Unknown"`. If valid → `YYYY-MM-DD` |

**Correction tracking**: a correction is counted **per field** — each field whose normalized
value differs from its original raw value counts as one correction.

> Example: a row with 3 fields corrected contributes 3 to the corrected counter.

> **TODO**: confirm with HR/team whether the corrected counter should be per-field or per-row.

**What counts as a correction**:
- String fields (`SeriesName`, `EpisodeTitle`): corrected if `normalize_string(raw) != raw`.
- Number fields (`SeasonNumber`, `EpisodeNumber`): corrected if `parse_number(raw)` differs
  from the integer value of `raw.strip()` when it can be parsed as an integer (e.g., `"-1"` → `0`,
  `"one"` → `0`), or if `raw.strip()` cannot be parsed as an integer at all (e.g., `""`, `"3.5"`).
  The value `"0"` already equals `parse_number("0") = 0`, so it is **not** counted as a correction.
- `AirDate`: corrected if `parse_date(raw) != raw.strip()`.

### Step 4 – Compute dedup key and compare against catalog
Determine the dedup key (see §8), then check if an entry with that key already exists.

- **New entry**: add to catalog.
- **Duplicate**: apply "best record" selection (see §9), increment duplicate counter.

---

## 5. Data Structure

A single flat dictionary is used as the catalog:

```python
catalog = {}  # dedup_key (tuple) → episode_record (dict)
```

### Episode record schema

```python
{
    "series_name":    str,  # normalized (lowercase, trimmed, collapsed spaces)
    "season_number":  int,
    "episode_number": int,
    "episode_title":  str,  # normalized, or "untitledepisode"
    "air_date":       str,  # "YYYY-MM-DD" or "Unknown"
}
```

---

## 6. Number Parsing (`parse_number`)

- Strip the value.
- Try `int(value_stripped)` — only accepts pure integer strings.
- Values like `"3.5"`, `"one"`, `"--2"`, `""`, `" "` raise `ValueError` → return `0`.
- If parsed result `<= 0` → return `0`.
- Otherwise return the integer.

> Handles: `""` → `0`, `"one"` → `0`, `"--2"` → `0`, `"3.5"` → `0`, `"-1"` → `0`,
> `"0"` → `0`, `"5"` → `5`.

---

## 7. Date Parsing and Validation (`parse_date`)

### Accepted separators
`-`, `/`, or one or more spaces.

### Accepted formats
1. `YYYY[sep]MM[sep]DD` → validate and keep as `YYYY-MM-DD`
2. `DD[sep]MM[sep]YYYY` → validate and convert to `YYYY-MM-DD`

> Disambiguation: if the first numeric token has 4 digits → year-first; otherwise → day-first.

### Validation rules
After parsing, the date must satisfy:
- `year > 0`
- `month` between 1 and 12
- `day` between 1 and the actual number of days in that month/year (leap years included)

Use `datetime.datetime(year, month, day)` inside `try/except` to validate.
If any rule fails → return `"Unknown"`.

---

## 8. Dedup Key Computation (`compute_dedup_key`)

The key is a tuple determined by which fields are valid after correction:

| Condition | Dedup Key |
|---|---|
| `season ≠ 0` and `episode ≠ 0` | `(series_norm, season, episode_num)` |
| `season == 0` and `episode ≠ 0` | `(series_norm, 0, episode_num, title_norm)` |
| `season ≠ 0` and `episode == 0` | `(series_norm, season, 0, title_norm)` |
| `season == 0` and `episode == 0`, real title | `(series_norm, 0, 0, title_norm)` |
| `season == 0` and `episode == 0`, no real title | `(series_norm, 0, 0, "air:" + air_date)` |

> "Real title" = title is not `"untitledepisode"`.
> The last case is always reachable: if title is `"untitledepisode"` AND air date is `"Unknown"`,
> the row would have been discarded in Step 2.

---

## 9. Best Record Selection (`is_better_record`)

When a duplicate is found, keep the record with the highest priority (compare in order):

1. Valid `AirDate` (not `"Unknown"`) over `"Unknown"`
2. Known `EpisodeTitle` (not `"untitledepisode"`) over `"untitledepisode"`
3. Both `SeasonNumber != 0` **and** `EpisodeNumber != 0` over any record where at least one is `0`
4. If still tied → keep the **first** entry encountered (return `False`, do not replace)

> Rule 3 is a single combined condition: a record only wins on this criterion if it has
> **both** season and episode non-zero. Having only one of them non-zero does not win.

> The winning record replaces the existing catalog entry entirely.

---

## 10. Output

### 10.1 `output/episodes_clean.csv`

- Header: `SeriesName,SeasonNumber,EpisodeNumber,EpisodeTitle,AirDate`
- One row per catalog entry (no duplicates)
- All string fields normalized (lowercase, trimmed, collapsed spaces)
- Sorted by `(series_name, season_number, episode_number)` ascending
- Generated even if empty (header only)

### 10.2 `output/report.md`

Sections and order:

1. **Total input records** – rows read from the CSV
2. **Total output records** – entries in the final catalog
3. **Discarded entries** – rows removed in Step 1 or Step 2
4. **Corrected fields** – total field-level corrections applied in Step 3
5. **Duplicates detected** – key collisions found in Step 4
6. **Deduplication strategy** – written explanation (see draft below)

Generated even if all counters are 0.

#### Deduplication strategy text

> Episodes are considered duplicates when they share the same normalized series name and
> a combination of season number, episode number, and/or episode title, depending on which
> fields are available. When both season and episode numbers are known (non-zero), identity
> is determined solely by those two numbers together with the series name. When one of the
> two numbers is zero (unknown), the episode title is added to the key to improve precision.
> When both numbers are zero, the episode title is used if it is known; otherwise the air date
> is used as a last resort. Among duplicate records, the one with the most complete information
> is kept: a known air date is preferred over "Unknown", a real title over "untitledepisode",
> and a record with both a valid season and episode number over one missing either. When all
> else is equal, the first record encountered in the file is kept.

---

## 11. Edge Cases

| Scenario | Behavior |
|---|---|
| No `.csv` file found in `input/` | Print error message and `sys.exit(1)` |
| Multiple `.csv` files in `input/` | Use the first one found (filesystem order) |
| CSV has no valid rows | Output `episodes_clean.csv` with header only; report with all counters at 0 |
| `SeasonNumber` like `"one"`, `"3.5"`, `"--2"` | Invalid → corrected to `0` |
| `AirDate` like `"0000-00-00"`, `"2022-40-99"` | Fails validation → `"Unknown"` |
| Two `"untitledepisode"` episodes, same series, different season → not duplicates | Different tuple keys |
| Same episode with different capitalizations | Normalized before comparison → treated as duplicate |
| Row with fewer than 5 columns | Pad with empty strings |

---

## 12. Metrics Tracked

| Counter | When incremented |
|---|---|
| `total_input` | Each row read from the CSV |
| `total_output` | Final count of catalog entries (computed at end) |
| `discarded` | Row removed in Step 1 or Step 2 |
| `corrected_fields` | Each individual field changed in Step 3 (per-field, not per-row) |
| `duplicates_detected` | Each key collision found in Step 4 (3 identical rows → 2 collisions) |
