# Exercise B — Thinking Behind the Script
*The Streaming Service's Lost Episodes*

---

## My Approach

Before writing any code, I spent time fully understanding the domain problem. I treated the spec like a client brief, not a set of instructions to execute blindly, but a document to question, challenge, and internalize. I created a plan to map out the architecture in advance, identifying the key functions, their responsibilities, and the flow between them.

As I planned, questions surfaced that the spec didn't answer. I documented them rather than making silent assumptions. Some I resolved through reasoning; one of them, specifically whether episode titles are unique within a season, I didn't get to escalate due to the submission deadline, so I made a deliberate, documented decision and moved on.

## Technical Decisions

I chose a structured (functional) paradigm as required, with no OOP and no database. The data lives in a plain Python dictionary, which keeps the logic transparent and easy to follow.

The most interesting challenge was deduplication. My first instinct was to compare full normalized rows, but I quickly realized this would break the most common duplicate pattern: the same episode appearing twice, once with a title and once without. They would generate different complete rows and never be caught. The right approach was to build identity keys using only the fields that are meaningful for identification.

From there I identified a gap: the key logic worked when both rows had equal or better data, but missed cross-tier duplicates, meaning a full row and a partial row for the same episode. I designed a secondary title index mapping (series, season, title) to the catalog entry to catch this case. Season is required in the index key because I explicitly don't assume titles are unique across seasons, only within one. Each assumption is documented, with its trade-offs and the reasoning behind it.

The air date question also required deliberate reasoning: dates are unreliable dedup identifiers since multiple episodes can air the same day. But as a last resort for completely unidentifiable rows, they are better than nothing. Discarding those rows entirely would lose the signal that data exists for a series at all.

## What This Process Reflects

Every decision I made has a documented why, in the README, in the assumptions section, in the code. This isn't just for the reviewer; it is how I think software should be built. The next person should be able to understand not just what the code does, but why it does it that way and what trade-offs were accepted.

I iterated. When I found a normalization bug (the spec implied two words for the untitled placeholder, my implementation had none), I fixed it everywhere it appeared: logic, tests, output text, and documentation. When the key logic had a gap, I didn't patch it quietly; I documented the limitation and designed a proper solution.

That is how I think about systems: understand the problem deeply, iterate as new information comes in, adapt when things change, and keep the goal in mind. The code is not the product. The value it creates is.
