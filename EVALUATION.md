# Reliability & Evaluation

This project is tested three ways: **automated tests**, a **deterministic grounding guardrail**, and **human/manual review**. Results are recorded below in parseable form so they can be read without running a demo.

## Summary

> **5 out of 5 automated tests passed.** The deterministic recommender is fully reproducible. The RAG grounding guardrail correctly flags any song that appears in a generated answer but was not in the retrieved set — verified with both a passing and a failing case. The generative layer cannot be asserted by exact string match (wording varies per run), so it is validated by the guardrail and human review instead. Biggest reliability gap: with a small 18-song catalog, the retriever can over-favor genre/mood and surface stylistically similar songs.

## 1. Automated Tests (`pytest`)

Run with `pytest`. Latest result: **5 passed in 0.07s**.

| Test | What it checks | Result |
|------|----------------|--------|
| `test_recommend_returns_songs_sorted_by_score` | Ranking returns k songs, best match first | Pass |
| `test_explain_recommendation_returns_non_empty_string` | Every recommendation has a human-readable reason | Pass |
| `test_verify_grounding_passes_when_only_retrieved_songs_named` | Guardrail accepts a grounded answer | Pass |
| `test_verify_grounding_flags_song_outside_retrieved_set` | Guardrail rejects a hallucinated song | Pass |
| `test_recommend_runs_end_to_end_and_stays_grounded` | Full pipeline (stubbed model) stays grounded | Pass |

The RAG tests use a **stub model client**, so they run in CI with no API key and no network — only the retrieval and guardrail logic is under test.

## 2. Grounding Guardrail + Logging

`verify_grounding()` in [`src/rag.py`](src/rag.py) is a pure, deterministic check: it scans the generated answer for any catalog title that was **not** in the retrieved set and returns `(is_grounded, leaked_titles)`. The pipeline logs the retrieved songs at `INFO` and logs a `WARNING` if the guardrail detects a leak, so failures are recorded with a reason rather than passing silently. The CLI also handles a missing/invalid `GEMINI_API_KEY` and transient API errors (e.g. `503`/rate limits) with clear messages instead of a stack trace.

## 3. Human / Manual Evaluation

| Test Input | Evaluation Criteria | Result |
|------------|--------------------|--------|
| `{genre: pop, mood: happy, energy: 0.8, acoustic: false}` | Top pick is an upbeat pop song matching the profile | Pass — *Sunrise City* (4.48), then *Gym Hero* |
| `{genre: lofi, mood: chill, energy: 0.4, acoustic: true}` | Top picks are low-energy, acoustic-leaning lofi | Pass — *Midnight Coding* (4.31), *Library Rain* |
| `{genre: pop, mood: sad, energy: 0.9, acoustic: false}` (conflicting) | Handles contradictory preferences without crashing | Partial — runs, but energy dominates and surfaces upbeat songs for a "sad" request |
| Empty / unmatched profile | Does not crash; returns something or a clear "no strong match" | Pass — returns ranked list; low scores signal weak match |
| Generated answer names a non-retrieved song | Guardrail flags it | Pass — `verify_grounding` returns `(False, [...])` and logs a warning |
| Live RAG answer for `"upbeat gym music, nothing acoustic"` | Conversational, only names retrieved songs | Pass — real Gemini run named Circuit Bloom, Storm Runner, Gym Hero, Fire in the Skyline, Neon Harbor (all in `data/songs.csv`); guardrail reported no leak |
| Live RAG under transient API error (`503` / rate limit) | Fails with a clear message, no stack trace | Pass — CLI prints `Error: Gemini API request failed (503 ...)` and exits 1 |

**What worked:** deterministic ranking is reproducible and explainable; the guardrail reliably catches out-of-catalog songs.
**What didn't:** conflicting profiles let one feature (energy) dominate; the generative layer resists exact-match testing.
**What I learned:** a hybrid system needs two testing styles — exact assertions for the deterministic half, and invariant/guardrail checks for the generative half.
