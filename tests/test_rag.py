"""Offline reliability tests for the RAG layer.

These do NOT call the Anthropic API — they use a stub client so the retrieval
and grounding-guardrail logic can be verified deterministically in CI.
"""

from src.rag import recommend, verify_grounding


# --- Test fixtures -----------------------------------------------------------

SONGS = [
    {"id": 1, "title": "Sunrise City", "artist": "Neon Echo", "genre": "pop",
     "mood": "happy", "energy": 0.82, "acousticness": 0.18},
    {"id": 2, "title": "Gym Hero", "artist": "Max Pulse", "genre": "pop",
     "mood": "intense", "energy": 0.93, "acousticness": 0.05},
    {"id": 3, "title": "Moonlit Strings", "artist": "Elliot Vale", "genre": "classical",
     "mood": "serene", "energy": 0.20, "acousticness": 0.95},
]


class _StubBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _StubResponse:
    def __init__(self, text):
        self.content = [_StubBlock(text)]


class _StubMessages:
    """Returns a canned profile when parsing, a canned answer when generating."""

    def create(self, **kwargs):
        if "output_config" in kwargs:  # parse_request step
            return _StubResponse(
                '{"favorite_genre": "pop", "favorite_mood": "happy", '
                '"target_energy": 0.8, "likes_acoustic": false}'
            )
        return _StubResponse("Try 'Sunrise City' by Neon Echo — an upbeat pop pick.")


class _StubClient:
    def __init__(self):
        self.messages = _StubMessages()


# --- Grounding guardrail (pure, deterministic) -------------------------------

def test_verify_grounding_passes_when_only_retrieved_songs_named():
    retrieved = [(SONGS[0], 4.48, "genre match")]
    answer = "I recommend Sunrise City for an upbeat vibe."
    grounded, leaked = verify_grounding(answer, retrieved, SONGS)
    assert grounded is True
    assert leaked == []


def test_verify_grounding_flags_song_outside_retrieved_set():
    retrieved = [(SONGS[0], 4.48, "genre match")]  # only Sunrise City retrieved
    answer = "You should also listen to Moonlit Strings."  # not retrieved
    grounded, leaked = verify_grounding(answer, retrieved, SONGS)
    assert grounded is False
    assert "Moonlit Strings" in leaked


# --- End-to-end pipeline with a stubbed model --------------------------------

def test_recommend_runs_end_to_end_and_stays_grounded():
    answer = recommend("upbeat pop", songs=SONGS, client=_StubClient())
    assert "Sunrise City" in answer
    # The stub answer only names a retrieved song, so grounding must hold.
    retrieved = [(SONGS[0], 0.0, ""), (SONGS[1], 0.0, "")]
    grounded, _ = verify_grounding(answer, retrieved, SONGS)
    assert grounded is True
