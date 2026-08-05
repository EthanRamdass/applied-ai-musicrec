# 🎵 Music Recommender — from Rule-Based Scoring to Retrieval-Augmented Generation

## Original Project (Modules 1–3): *Music Recommender Simulation*

My original project was the **Music Recommender Simulation**. Its goal was to build a small, fully transparent **content-based recommender**: represent songs and a user's "taste profile" as data, design a scoring rule that turns that data into ranked recommendations, and evaluate what the system gets right and wrong. It could load a song catalog from CSV, score each song against a user profile using weighted attributes (genre, mood, energy, acousticness, and more), rank the results, and explain *why* each song was recommended — mirroring how real platforms like Spotify surface tracks, but with logic simple enough to read end-to-end.

---

## Title and Summary

**What it does:** This project extends the original rule-based recommender with a **Retrieval-Augmented Generation (RAG)** layer. A user can now type a request in plain English ("upbeat gym music, nothing acoustic"), and the system parses it into a structured profile, retrieves the best-matching songs from its catalog using the original scoring engine, and has a large language model (Google's **Gemini**) write a friendly, grounded recommendation — using **only** the songs it actually retrieved.

**Why it matters:** It shows how a deterministic, explainable retrieval system and a generative model can be combined so you get the best of both: the recommender guarantees *which* songs are valid and *why* they match, while the LLM makes the result conversational and easy to read. Crucially, the LLM is constrained to the retrieved set, so it **cannot hallucinate songs that aren't in the catalog** — a concrete, testable answer to a common failure mode of generative AI.

---

## Architecture Overview

![System architecture](assets/mermaid%20diagram.png)

The system moves data left-to-right through three stages, with a dedicated zone for human and automated checks:

- **Input** — a natural-language request and the song catalog (`data/songs.csv`).
- **Process** —
  - **RAG layer** ([`src/rag.py`](src/rag.py)): Gemini parses the free-text request into a structured `UserProfile`.
  - **Retriever** ([`src/recommender.py`](src/recommender.py)): the original scoring engine (`ScoringStrategy.score_song`) rates every song, and `recommend_songs` ranks them and applies a diversity penalty to return the top-*k*.
  - Those top-*k* songs become the **grounding context**, and Gemini generates the final conversational answer from that set only.
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

5. **Run the RAG (conversational) layer** — requires a Google Gemini API key ([get one free at aistudio.google.com](https://aistudio.google.com/app/apikey)). The app auto-loads the key from a git-ignored `.env` file:
   ```bash
   # Option A: create a .env file in the project root (recommended)
   echo "GEMINI_API_KEY=your-key-here" > .env

   # Option B: set it in your shell
   export GEMINI_API_KEY="your-key-here"      # macOS / Linux
   $env:GEMINI_API_KEY="your-key-here"        # Windows PowerShell

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
python -m src.rag "upbeat gym music, nothing acoustic"
```

**Output** *(a real Gemini run — wording varies per run, but the songs are always drawn from the retrieved set):*
```text
Request: upbeat gym music, nothing acoustic

Hey there! I'd love to help you find the perfect high-energy soundtrack for your
workout. Here are some awesome, non-acoustic tracks from our list that will keep
your energy high at the gym:

1. "Circuit Bloom" by Nova Keys
   * Why it fits: An electronic track with a super uplifting mood and great
     energy (0.77) to keep you moving and motivated.
2. "Storm Runner" by Voltline
   * Why it fits: If you like rock, this intense track brings a ton of power
     with a very high energy level (0.91).
3. "Gym Hero" by Max Pulse
   * Why it fits: The name says it all! An intense pop song with an energy
     rating of 0.93 — perfect for a high-intensity session.
4. "Fire in the Skyline" by Iron Harbor
   * Why it fits: A metal track with a rebellious mood and a massive energy
     level (0.95) for maximum adrenaline.
5. "Neon Harbor" by Aura Lane
   * Why it fits: A confident hip hop track with high energy (0.81) to lock
     into your zone.

None of these are acoustic, so you can count on pure, high-octane energy!
```

> **Note:** Every song named above exists in `data/songs.csv` — the grounding guardrail (`verify_grounding`) enforces this, so Gemini cannot recommend a track outside the retrieved set. The exact wording varies per run; the song *selections* are deterministic from the scoring engine in Examples 1–2.

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
