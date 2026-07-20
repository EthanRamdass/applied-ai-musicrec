# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked the agent to extend the simple starter recommender with stretch features: multiple scoring strategies, diversity penalties, richer song attributes, and a more readable terminal table. The goal was to keep the logic content-based while making the CLI output easier to inspect.

**Prompts used:**

- “Implement the recommender logic in src/recommender.py.”
- “Add multiple scoring strategies so the recommender can switch between balanced, genre-first, mood-first, and energy-focused behavior.”
- “Expand the song dataset and make the output readable in a table.”
- “Help me verify the CLI output and fix any parser issues from the expanded CSV data.”

**What did the agent generate or change?**

- Added a scoring-strategy layer in [src/recommender.py](src/recommender.py) with a `ScoringStrategy` helper and `get_strategy()` selector.
- Expanded the catalog in [data/songs.csv](data/songs.csv) to include richer attributes such as popularity, mood tags, subgenre, instrumentalness, and lyric density.
- Updated [src/main.py](src/main.py) to print ranked recommendations in a compact ASCII table with score and explanation text.
- Ran the CLI with `python -m src.main` to verify the new output.

**What did you verify or fix manually?**

The agent initially introduced a parsing problem because the new CSV values used `2010s`/`2020s` strings for `release_decade`, while the loader expected numeric values. I fixed that manually by converting the values to integers like `2010` and `2020` in [data/songs.csv](data/songs.csv), and then re-ran the CLI to confirm the output printed correctly.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

Strategy pattern.

**How did AI help you brainstorm or implement it?**

The agent suggested separating “how scoring is weighted” from “how recommendations are ranked” so the same recommender could support different user-intent modes without duplicating logic. That led to a small strategy interface with a selector function that returns the appropriate scoring function depending on the requested mode.

**How does the pattern appear in your final code?**

The strategy logic is implemented in [src/recommender.py](src/recommender.py) through `ScoringStrategy` and `get_strategy()`. The recommender calls the selected strategy inside `score_song()` and `recommend_songs()` so the ranking behavior can be switched between balanced, genre-first, mood-first, and energy-focused modes without rewriting the rest of the pipeline.
