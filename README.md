# The Streaming Service's Lost Episodes

A Python program that reads a corrupted CSV catalog of streaming episodes, cleans and
de-duplicates it, and produces a clean output CSV and a quality report.

## How to Run

Place the input `.csv` file in the `input/` folder, then run the program:

Both `input/` and `output/` are created automatically if they don't exist.
Output files are written to `output/`:

- `episodes_clean.csv` — cleaned and de-duplicated catalog
- `report.md` — data quality report

## What "Normalized" Means

All string fields (series name, episode title) are normalized before comparison and storage:

- Leading and trailing whitespace is removed
- Internal whitespace sequences are collapsed to a single space
- All characters are lowercased

**Example:** `"    Game  OF Thrones       "` → `"game of thrones"`

Missing episode titles are replaced with `"untitled episode"` (already in normalized form).

## Deduplication Strategy

### Primary key

Two episodes are considered duplicates when they share the same normalized series name
combined with the best available identifying fields, in priority order:

| Available data | Key used |
|---|---|
| Season + Episode both known | `(series, season, episode)` |
| Season unknown, Episode known | `(series, 0, episode, title)` |
| Season known, Episode unknown | `(series, season, 0, title)` |
| Both unknown, title known | `(series, 0, 0, title)` |
| Both unknown, no title | `(series, 0, 0, "air:" + date)` |

Air date is intentionally excluded from identity keys in all cases where better identifying
information is available — multiple episodes within a season can share an air date, making it
an unreliable episode identifier on its own. The one exception is the last row in the table
above: when a row has no season, no episode number, and no title, the air date is used as a
last resort so that at least same-day rows of the same series are grouped together. The
trade-offs of that decision are covered in the Limitations section below.

### Secondary title index

When a season is known and the episode title is real (not `"untitled episode"`), a secondary
index maps `(series, season, title)` to the existing catalog entry. This catches duplicates
that the primary key alone would miss — specifically when one row has the episode number and
another does not, but both share the same series, season, and title.

**Example (Game of Thrones, Season 6, Episode 9):**

```
Row 1: game of thrones, 6, 9, untitled episode, Unknown
  → primary key: ("game of thrones", 6, 9)
  → added to catalog
  → title index: not indexed (title is "untitled episode")

Row 2: game of thrones, 6, 9, battle of the bastards, 2016-06-19
  → primary key: ("game of thrones", 6, 9)  ← same key → duplicate detected
  → Row 2 wins: has a real title and a valid air date
  → catalog updated; title index: ("game of thrones", 6, "battle of the bastards") added

Row 3: game of thrones, 6, 0, battle of the bastards, Unknown
  → primary key: ("game of thrones", 6, 0, "battle of the bastards")  ← not in catalog
  → title index lookup: ("game of thrones", 6, "battle of the bastards")  ← FOUND
  → duplicate detected via secondary index
  → Row 2's record wins: has a known episode number (9 vs 0)
  → Row 3 is discarded
```

Without the secondary index, Row 3 would produce a separate output entry — visually a
duplicate to a human, but undetectable by primary key lookup alone.

### Best record selection

When duplicates are found, the record with the most complete information is kept:

1. Valid air date over `"Unknown"`
2. Known episode title over `"untitled episode"`
3. Both season and episode number non-zero over any record missing either
4. If still tied → keep the first record encountered in the file

## Assumptions and Limitations

### Assumptions

- **Episode titles are unique within a season, but not necessarily across seasons of the same show.**
  The secondary title index key includes the season number for this reason. Two rows with the
  same series and title but different seasons are never merged. If two genuinely different
  episodes within the same season share a title they would be incorrectly merged — accepted
  trade-off, as most series use unique titles per season and multi-part episodes use
  distinguishing suffixes ("Part 1", "Part 2").

- **Season and episode numbers must be positive integers.**
  Any value that is not a pure integer string is treated as missing and set to `0`. This
  includes floats (`"3.5"`), words (`"one"`), double negatives (`"--2"`), negatives (`"-1"`),
  and blank values. There is no concept of episode `0` or season `0` — `0` is used internally
  as a sentinel meaning "unknown". This follows the spec definition of a valid number.

- **Dates are either year-first (`YYYY-MM-DD`) or day-first (`DD-MM-YYYY`).**
  Disambiguation is based solely on whether the first token has 4 digits. Two-digit years are
  not supported — a value like `"23-01-15"` would be parsed as day=23, month=1, year=15 (year
  15 AD), which fails validation and becomes `"Unknown"`. Accepted separators are `-`, `/`, or
  one or more spaces.

- **The input file is UTF-8 encoded with no header row.**
  Data is expected to start from row 1. If a header row is present it will be treated as a
  data row and most likely discarded (series name would be `"SeriesName"`, which is valid, but
  episode and date fields would fail parsing).

### Limitation: cross-tier matching requires the season to be known

If a row is missing the season number, the secondary title index is not consulted — a missing
season makes it impossible to confirm the episode belongs to the same season as an existing
entry. This is a direct consequence of the assumption that titles are unique within a season
but not across seasons: matching by title alone, without a season, could incorrectly merge
two episodes from different seasons that happen to share the same title.

Example of an unresolvable case:

```
game of thrones, 6, 10, winds of winter, 2016-06-26  → key: ("game of thrones", 6, 10)
game of thrones, 0,  0, winds of winter, Unknown      → key: ("game of thrones", 0, 0, "winds of winter")
```

These two rows likely refer to the same episode, but there is no safe way to confirm it —
the second row could belong to any season. Both entries are kept in the output.

### Limitation: air date as last-resort key

When a row has no season, no episode number, and no title, the air date is used as the
dedup key of last resort. Since multiple episodes can air on the same day, this may
incorrectly merge distinct episodes.

Consider a streaming platform that releases a full season at once with no metadata:

```
netflix show, 0, 0, untitled episode, 2026-01-01
netflix show, 0, 0, untitled episode, 2026-01-01
netflix show, 0, 0, untitled episode, 2026-01-01
... (8 rows)
```

All 8 rows share the same key `("netflix show", 0, 0, "air:2026-01-01")` and collapse into
one output entry. They could be 8 different episodes, 8 duplicates of the same one, or
anything in between — the program cannot know.

Discarding these rows entirely was considered but rejected: keeping at least one entry
preserves the signal that data exists for that series, allowing a human or downstream system
to identify that a season may be missing or corrupt. Silently discarding would lose that
information entirely.
