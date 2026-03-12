# Data Quality Report

- **Total input records**: 22
- **Total output records**: 14
- **Discarded entries**: 2
- **Corrected fields**: 51
- **Duplicates detected**: 6

## Deduplication Strategy

Episodes are considered duplicates when they share the same normalized series name and
a combination of season number, episode number, and/or episode title, depending on which
fields are available. When both season and episode numbers are known (non-zero), identity
is determined solely by those two numbers together with the series name. When one of the
two numbers is zero (unknown), the episode title is added to the key to improve precision.
When both numbers are zero, the episode title is used if it is known; otherwise the air date
is used as a last resort.
A secondary title index is also maintained: when the season is known and the episode title
is real, the combination (series, season, title) is indexed regardless of episode number.
This allows detecting duplicates across rows that differ only in episode number completeness
(e.g. one row has the number, another does not), under the assumption that episode titles
are unique within a season. Among duplicate records, the one with the most complete
information is kept: a known air date is preferred over "Unknown", a real title over
"untitled episode", and a record with both a valid season and episode number over one
missing either. When all else is equal, the first record encountered in the file is kept.
