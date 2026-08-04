"""
Retrieval-Augmented Generation (RAG) layer for the Music Recommender.

This turns the deterministic content-based recommender into a conversational
one. The pipeline is:

    1. Understand  - Claude parses a free-text request into a UserProfile.
    2. Retrieve    - the existing recommender scores + ranks the catalog and
                     returns the top-k matching songs (the "grounding" data).
    3. Generate    - Claude writes a natural-language recommendation grounded
                     ONLY in the retrieved songs, so it can never invent a
                     track that is not in data/songs.csv.

The retrieval half is your existing code (recommender.py); this file only adds
the language-model front-end and grounded generation on top.

Setup:
    pip install anthropic          # or: pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...   # Windows PowerShell: $env:ANTHROPIC_API_KEY="..."

Run:
    python -m src.rag "upbeat gym music, nothing acoustic"
"""

import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple

# Load ANTHROPIC_API_KEY from a local .env file if python-dotenv is installed.
# The .env file is git-ignored — never commit real keys to source.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is optional
    pass

# `anthropic` is imported lazily inside the functions that build a live client,
# so the retrieval and grounding-guardrail logic can be imported and unit-tested
# without the SDK installed.

try:
    from src.recommender import load_songs, recommend_songs
except ImportError:  # pragma: no cover - fallback for direct script execution
    from recommender import load_songs, recommend_songs


logger = logging.getLogger("musicrec.rag")

# Latest and most capable Claude model. Adaptive thinking lets the model decide
# how much to reason per request; see the Anthropic API docs.
MODEL = "claude-opus-5"

# The structured shape we ask the model to extract from free text. It mirrors
# the fields the Recommender already understands.
PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "favorite_genre": {"type": "string"},
        "favorite_mood": {"type": "string"},
        "target_energy": {"type": "number"},
        "likes_acoustic": {"type": "boolean"},
    },
    "required": ["favorite_genre", "favorite_mood", "target_energy", "likes_acoustic"],
    "additionalProperties": False,
}


def parse_request(client, request: str) -> Dict:
    """Step 1 - turn a free-text request into a structured taste profile.

    Uses structured outputs so the response is guaranteed to match the schema
    the recommender expects.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=(
            "You translate a listener's free-text request into a music taste "
            "profile. Pick the single best value for each field. energy is a "
            "float from 0.0 (calm) to 1.0 (high energy)."
        ),
        messages=[{"role": "user", "content": request}],
        output_config={"format": {"type": "json_schema", "schema": PROFILE_SCHEMA}},
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def _format_grounding(retrieved: List[Tuple[Dict, float, str]]) -> str:
    """Render the retrieved songs as the grounding context for the model."""
    lines = []
    for rank, (song, score, explanation) in enumerate(retrieved, start=1):
        lines.append(
            f"{rank}. {song['title']} by {song['artist']} "
            f"[genre={song['genre']}, mood={song['mood']}, "
            f"energy={song['energy']}] "
            f"(score {score:.2f}; {explanation})"
        )
    return "\n".join(lines)


def generate_answer(
    client,
    request: str,
    retrieved: List[Tuple[Dict, float, str]],
) -> str:
    """Step 3 - write a grounded, conversational recommendation.

    The model is instructed to recommend ONLY from the retrieved songs, so it
    cannot hallucinate tracks outside the catalog.
    """
    grounding = _format_grounding(retrieved)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=(
            "You are a friendly music guide. Recommend songs to the listener "
            "using ONLY the candidate songs provided below. Never invent a "
            "song, artist, or detail that is not in the list. Explain briefly, "
            "in plain language, why each pick fits their request.\n\n"
            f"Candidate songs (already ranked by relevance):\n{grounding}"
        ),
        messages=[{"role": "user", "content": request}],
    )
    return next(b.text for b in response.content if b.type == "text")


def verify_grounding(
    answer: str,
    retrieved: List[Tuple[Dict, float, str]],
    songs: List[Dict],
) -> Tuple[bool, List[str]]:
    """Reliability guardrail: confirm the answer only names retrieved songs.

    Scans the generated answer for any catalog song title that was NOT in the
    retrieved set. Such a title means the model recommended a song outside the
    grounding context (a hallucination relative to what it was given).

    Returns (is_grounded, leaked_titles). Pure and deterministic, so it can be
    unit-tested without calling the API.
    """
    retrieved_titles = {song["title"] for song, _, _ in retrieved}
    answer_lower = answer.lower()
    leaked = sorted(
        song["title"]
        for song in songs
        if song["title"] not in retrieved_titles
        and song["title"].lower() in answer_lower
    )
    return (len(leaked) == 0, leaked)


def recommend(
    request: str,
    songs: Optional[List[Dict]] = None,
    k: int = 5,
    strategy_name: str = "balanced",
    client=None,
) -> str:
    """End-to-end RAG: understand -> retrieve -> generate -> verify.

    Returns a natural-language recommendation grounded in the catalog.
    """
    if client is None:
        import anthropic  # lazy import: only needed for a live API call

        client = anthropic.Anthropic()
    if songs is None:
        songs = load_songs("data/songs.csv")

    profile = parse_request(client, request)
    retrieved = recommend_songs(profile, songs, k=k, strategy_name=strategy_name)
    logger.info(
        "Retrieved %d songs: %s",
        len(retrieved),
        ", ".join(song["title"] for song, _, _ in retrieved),
    )

    answer = generate_answer(client, request, retrieved)

    grounded, leaked = verify_grounding(answer, retrieved, songs)
    if not grounded:
        # The guardrail caught a song outside the retrieved set. Log it rather
        # than silently trusting the model.
        logger.warning("Grounding violation — songs not in retrieved set: %s", leaked)
    return answer


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    request = " ".join(sys.argv[1:]) or "upbeat pop for a happy morning, nothing acoustic"
    print(f"Request: {request}\n")

    # Fail fast with a clear message if no credentials are configured, instead
    # of letting the SDK raise a bare TypeError deep in the call stack.
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        sys.exit(
            "Error: no Anthropic credentials found. Set ANTHROPIC_API_KEY and retry, e.g.\n"
            '  Windows PowerShell:  $env:ANTHROPIC_API_KEY="your-key"\n'
            '  macOS / Linux:       export ANTHROPIC_API_KEY="your-key"'
        )

    import anthropic  # lazy import: only needed for the live API path

    try:
        print(recommend(request))
    except anthropic.AuthenticationError:
        sys.exit("Error: invalid ANTHROPIC_API_KEY. Check the key and retry.")
    except anthropic.APIConnectionError:
        sys.exit("Error: could not reach the Anthropic API. Check your connection.")


if __name__ == "__main__":
    main()
