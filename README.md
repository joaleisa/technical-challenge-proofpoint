# The Streaming Service's Lost Episodes

A Python program that reads a corrupted CSV catalog of streaming episodes, cleans and
de-duplicates it, and produces a clean output CSV and a quality report.

## How to Run

Place the input `.csv` file in the `input/` folder, then run:

```bash
python main.py
```

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

Air date is intentionally excluded from identity keys — multiple episodes within a season
can share an air date and it is not a reliable dedup identifier.

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

### Assumption: episode titles are unique within a series and season

The secondary title index relies on this assumption. If two genuinely different episodes
within the same season share the same title (e.g. an anthology series with repeated titles),
they would be incorrectly merged into one output entry.

This is a known and accepted trade-off. The vast majority of series use unique titles per
season, and multi-part episodes typically use distinguishing suffixes ("Part 1", "Part 2").

### Limitation: cross-tier matching requires the season to be known

If a row is missing the season number, the secondary title index is not consulted — a missing
season makes it impossible to confirm the episode belongs to the same season as an existing
entry.

Example of an unresolvable case:

```
game of thrones, 6, 10, winds of winter, 2016-06-26  → key: ("game of thrones", 6, 10)
game of thrones,  ,  0, winds of winter, Unknown      → key: ("game of thrones", 0, 0, "winds of winter")
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
