# 🎵 Music Recommender — from Rule-Based Scoring to Retrieval-Augmented Generation

## Original Project (Modules 1–3): *Music Recommender Simulation*

My original project was the **Music Recommender Simulation**. Its goal was to build a small, fully transparent **content-based recommender**: represent songs and a user's "taste profile" as data, design a scoring rule that turns that data into ranked recommendations, and evaluate what the system gets right and wrong. It could load a song catalog from CSV, score each song against a user profile using weighted attributes (genre, mood, energy, acousticness, and more), rank the results, and explain *why* each song was recommended — mirroring how real platforms like Spotify surface tracks, but with logic simple enough to read end-to-end.

---

## Title and Summary

**What it does:** This project extends the original rule-based recommender with a **Retrieval-Augmented Generation (RAG)** layer. A user can now type a request in plain English ("upbeat gym music, nothing acoustic"), and the system parses it into a structured profile, retrieves the best-matching songs from its catalog using the original scoring engine, and has a large language model (Claude) write a friendly, grounded recommendation — using **only** the songs it actually retrieved.

**Why it matters:** It shows how a deterministic, explainable retrieval system and a generative model can be combined so you get the best of both: the recommender guarantees *which* songs are valid and *why* they match, while the LLM makes the result conversational and easy to read. Crucially, the LLM is constrained to the retrieved set, so it **cannot hallucinate songs that aren't in the catalog** — a concrete, testable answer to a common failure mode of generative AI.

---

## Architecture Overview

![System architecture](assets/mermaid%20diagram.png)

The system moves data left-to-right through three stages, with a dedicated zone for human and automated checks:

- **Input** — a natural-language request and the song catalog (`data/songs.csv`).
- **Process** —
  - **RAG layer** ([`src/rag.py`](src/rag.py)): Claude parses the free-text request into a structured `UserProfile`.
  - **Retriever** ([`src/recommender.py`](src/recommender.py)): the original scoring engine (`ScoringStrategy.score_song`) rates every song, and `recommend_songs` ranks them and applies a diversity penalty to return the top-*k*.
  - Those top-*k* songs become the **grounding context**, and Claude generates the final conversational answer from that set only.
  - A **CLI runner** ([`src/main.py`](src/main.py)) exercises the deterministic pipeline directly, without the LLM.
- **Output** — a ranked recommendation table and/or a grounded conversational answer.
- **Human & Testing** — `pytest` verifies scoring and ranking correctness, a **grounding guardrail** rejects any song not in the retrieved set, and **human review** (experiments and bias analysis) is documented in `model_card.md`.

A focused view of just the RAG data flow lives in [`assets/rag_architecture.md`](assets/rag_architecture.md) (rendered as `assets/rag_architecture.png`).

---

## Setup Instructions

**Prerequisites:** Python 3.10+ (developed on 3.12).

1. **Clone and enter the project**
   ```bash
   git clone https://github.com/EthanRamdass/applied-ai-musicrec.git
   cd applied-ai-musicrec
   ```

2. **(Optional) Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # macOS / Linux
   .venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the deterministic recommender** (no API key needed)
   ```bash
   python -m src.main
   ```

5. **Run the RAG (conversational) layer** — requires an Anthropic API key
   ```bash
   # macOS / Linux
   export ANTHROPIC_API_KEY="your-key-here"
   # Windows PowerShell
   $env:ANTHROPIC_API_KEY="your-key-here"

   python -m src.rag "upbeat gym music, nothing acoustic"
   ```

6. **Run the tests**
   ```bash
   pytest
   ```

---

## Sample Interactions

### Example 1 — Deterministic recommender (High-Energy Pop)

**Input** (user profile): `{ genre: "pop", mood: "happy", energy: 0.8, likes_acoustic: false }`

**Output:**
```text
=== High-Energy Pop [balanced] ===
Rank | Title         | Score | Reason
-----+---------------+-------+-------------------------------------------------------------
1    | Sunrise City  | 4.48  | genre match (+2.0); mood match (+1.0); energy similarity (+0.98); non-acoustic preference (+0.5)
2    | Gym Hero      | 3.37  | genre match (+2.0); energy similarity (+0.87); non-acoustic preference (+0.5)
3    | Rooftop Lights| 2.46  | mood match (+1.0); energy similarity (+0.96); non-acoustic preference (+0.5)
```

### Example 2 — Deterministic recommender (Chill Lofi)

**Input:** `{ genre: "lofi", mood: "chill", energy: 0.4, likes_acoustic: true }`

**Output:**
```text
=== Chill Lofi [balanced] ===
Rank | Title         | Score | Reason
-----+---------------+-------+-------------------------------------------------------------
1    | Midnight Coding| 4.31 | genre match (+2.0); mood match (+1.0); energy similarity (+0.58); acoustic preference (+0.5)
2    | Library Rain   | 3.81 | genre match (+2.0); mood match (+1.0); energy similarity (+0.65); acoustic preference (+0.5)
3    | Focus Flow     | 2.80 | mood match (+1.0); energy similarity (+0.60); acoustic preference (+0.5)
```

### Example 3 — RAG (conversational) layer

**Input:**
```bash
python -m src.rag "I want upbeat gym music, nothing acoustic"
```

**Output** *(representative — the exact wording varies per model run; the songs are always drawn from the retrieved top-k above):*
```text
Request: I want upbeat gym music, nothing acoustic

For a high-energy, non-acoustic gym session, start with "Sunrise City" by
Neon Echo — it's a bright, upbeat pop track that lands right in your energy
zone. "Gym Hero" by Max Pulse is an even harder-hitting pop workout song
(and basically built for this). If you want to keep momentum without maxing
out, "Rooftop Lights" by Indigo Parade keeps the happy, upbeat feel a notch
lower. All three are firmly on the non-acoustic side.
```

> ⚠️ **Honesty note:** Example 3's *wording* is illustrative because the generative output depends on a live API call and varies per run. The *song selections* are deterministic and come from the same scoring engine shown in Examples 1–2, and the grounding guardrail guarantees every named song exists in `data/songs.csv`.

---

## Design Decisions

- **RAG over fine-tuning or an agent.** With an 18-song catalog and an existing, well-tested scoring engine, RAG was the natural fit: the retriever already *is* the "retrieval" half, so I only needed to add a generation step. Fine-tuning would have required training data the project doesn't have, and a multi-step agent would have added planning machinery a single-pass recommendation doesn't need.
- **Reuse, don't rewrite.** The RAG layer calls the original `recommend_songs()` unchanged. The generative feature is additive — the deterministic pipeline still runs standalone via `src/main.py` with no API key.
- **Ground the model, then constrain it.** The LLM only ever sees the retrieved top-*k* songs and is instructed to recommend from that list only. This trades a little conversational freedom for a strong correctness guarantee.
- **Structured outputs for parsing.** The request-parsing step uses a strict JSON schema so the model's output always matches the `UserProfile` fields the recommender expects — avoiding brittle free-text parsing.

**Trade-offs:** The system depends on an external API (cost, latency, and network) for the conversational layer, so the deterministic CLI remains the offline fallback. The catalog is tiny and the scoring is intentionally simple, so recommendation *quality* is bounded by the data, not the model.

---

## Testing Summary

- **What worked:** The `pytest` suite in `tests/test_recommender.py` confirms the scoring rule and ranking behave correctly across profiles, and sensitivity experiments (e.g., increasing the energy weight) produced sensible, predictable shifts in ranking order. The deterministic pipeline is fully reproducible.
- **What didn't (or is a known limitation):** The generative layer can't be asserted with exact-match tests because output wording varies per run; it's validated by the grounding constraint and manual review rather than string equality. With a small catalog, the recommender can also over-favor genre/mood and surface stylistically similar songs.
- **What I learned:** Testing a hybrid system means testing the two halves differently — *exact assertions* for the deterministic retriever, and *invariant/guardrail checks* (every recommended song must exist in the catalog) for the generative half.

---

## Reflection

Extending a rule-based system with a generative layer taught me that the highest-leverage design choice was **what to make deterministic vs. generative** — keeping retrieval explainable and testable while letting the model handle only presentation. It reframed "using AI" as a system-design problem about grounding and guardrails, not just prompting.

> 📄 My full **responsible-AI reflection** — how I collaborated with AI, one helpful and one flawed AI suggestion, and the system's limitations — is in [`model_card.md`](model_card.md).
