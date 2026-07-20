import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """

    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """

    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs for a user, ranking them by a simple similarity score."""
        scored_songs = []
        for song in self.songs:
            score, _ = score_song(_profile_to_dict(user), _song_to_dict(song))
            scored_songs.append((score, song))

        scored_songs.sort(key=lambda item: item[0], reverse=True)
        return [song for _, song in scored_songs[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Explain why a single song matches the user's profile."""
        score, reasons = score_song(_profile_to_dict(user), _song_to_dict(song))
        return "; ".join(reasons) if reasons else f"Score: {score:.2f}"


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file and convert numeric fields to floats or ints."""
    path = Path(csv_path)
    if not path.is_absolute():
        candidate = Path(__file__).resolve().parent.parent / csv_path
        if candidate.exists():
            path = candidate

    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    songs = []
    for row in rows:
        songs.append(
            {
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            }
        )
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song against a user profile and return the score plus reasons."""
    if isinstance(user_prefs, UserProfile):
        user_prefs = _profile_to_dict(user_prefs)
    if isinstance(song, Song):
        song = _song_to_dict(song)

    favorite_genre = (user_prefs.get("favorite_genre") or user_prefs.get("genre") or "").strip().lower()
    favorite_mood = (user_prefs.get("favorite_mood") or user_prefs.get("mood") or "").strip().lower()
    target_energy = user_prefs.get("target_energy") if "target_energy" in user_prefs else user_prefs.get("energy")
    likes_acoustic = user_prefs.get("likes_acoustic", False)

    score = 0.0
    reasons: List[str] = []

    song_genre = str(song.get("genre", "")).strip().lower()
    song_mood = str(song.get("mood", "")).strip().lower()
    song_energy = float(song.get("energy", 0.0))
    song_acousticness = float(song.get("acousticness", 0.0))

    if favorite_genre and song_genre == favorite_genre:
        score += 2.0
        reasons.append("genre match (+2.0)")

    if favorite_mood and song_mood == favorite_mood:
        score += 1.0
        reasons.append("mood match (+1.0)")

    if target_energy is not None:
        energy_distance = abs(song_energy - float(target_energy))
        energy_score = max(0.0, 1.0 - energy_distance)
        score += energy_score
        reasons.append(f"energy similarity (+{energy_score:.2f})")

    if likes_acoustic is True and song_acousticness >= 0.6:
        score += 0.5
        reasons.append("acoustic preference (+0.5)")
    elif likes_acoustic is False and song_acousticness < 0.4:
        score += 0.5
        reasons.append("non-acoustic preference (+0.5)")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score each song, rank them, and return the top-k results with explanations."""
    ranked = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons) if reasons else "No specific match"
        ranked.append((song, score, explanation))

    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:k]


def _profile_to_dict(profile: UserProfile) -> Dict:
    return {
        "favorite_genre": profile.favorite_genre,
        "favorite_mood": profile.favorite_mood,
        "target_energy": profile.target_energy,
        "likes_acoustic": profile.likes_acoustic,
    }


def _song_to_dict(song: Song) -> Dict:
    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "genre": song.genre,
        "mood": song.mood,
        "energy": song.energy,
        "tempo_bpm": song.tempo_bpm,
        "valence": song.valence,
        "danceability": song.danceability,
        "acousticness": song.acousticness,
    }
