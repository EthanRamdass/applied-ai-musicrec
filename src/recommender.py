import csv
from dataclasses import dataclass, field
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
    popularity: int = 50
    release_decade: int = 2000
    mood_tags: str = ""
    subgenre: str = ""
    instrumentalness: float = 0.0
    lyric_density: float = 0.0


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
    target_popularity: Optional[int] = None
    preferred_release_decade: Optional[int] = None
    preferred_mood_tags: Optional[List[str]] = None
    preferred_subgenres: Optional[List[str]] = None
    likes_instrumental: bool = False


class ScoringStrategy:
    """Simple strategy object that controls how a song is scored."""

    def __init__(self, name: str, description: str, weights: Dict[str, float]):
        self.name = name
        self.description = description
        self.weights = weights

    def score_song(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        """Score a single song against a user profile using the strategy weights."""
        if isinstance(user_prefs, UserProfile):
            user_prefs = _profile_to_dict(user_prefs)
        if isinstance(song, Song):
            song = _song_to_dict(song)

        favorite_genre = (user_prefs.get("favorite_genre") or user_prefs.get("genre") or "").strip().lower()
        favorite_mood = (user_prefs.get("favorite_mood") or user_prefs.get("mood") or "").strip().lower()
        target_energy = user_prefs.get("target_energy") if "target_energy" in user_prefs else user_prefs.get("energy")
        likes_acoustic = user_prefs.get("likes_acoustic", False)
        target_popularity = user_prefs.get("target_popularity")
        preferred_release_decade = user_prefs.get("preferred_release_decade")
        preferred_mood_tags = _normalize_tags(user_prefs.get("preferred_mood_tags"))
        preferred_subgenres = _normalize_tags(user_prefs.get("preferred_subgenres"))
        target_instrumentalness = user_prefs.get("target_instrumentalness")

        score = 0.0
        reasons: List[str] = []

        song_genre = str(song.get("genre", "")).strip().lower()
        song_mood = str(song.get("mood", "")).strip().lower()
        song_energy = float(song.get("energy", 0.0))
        song_acousticness = float(song.get("acousticness", 0.0))
        song_popularity = float(song.get("popularity", 50))
        song_release_decade = int(song.get("release_decade", 2000))
        song_instrumentalness = float(song.get("instrumentalness", 0.0))
        song_subgenre = str(song.get("subgenre", "")).strip().lower()
        song_mood_tags = _normalize_tags(song.get("mood_tags", ""))

        if favorite_genre and song_genre == favorite_genre:
            score += self.weights.get("genre", 2.0)
            reasons.append(f"genre match (+{self.weights.get('genre', 2.0):.2f})")

        if favorite_mood and song_mood == favorite_mood:
            score += self.weights.get("mood", 1.0)
            reasons.append(f"mood match (+{self.weights.get('mood', 1.0):.2f})")

        if target_energy is not None:
            energy_distance = abs(song_energy - float(target_energy))
            energy_score = max(0.0, 1.0 - energy_distance)
            score += self.weights.get("energy", 1.0) * energy_score
            reasons.append(f"energy similarity (+{(self.weights.get('energy', 1.0) * energy_score):.2f})")

        if likes_acoustic is True and song_acousticness >= 0.6:
            score += self.weights.get("acoustic", 0.5)
            reasons.append(f"acoustic preference (+{self.weights.get('acoustic', 0.5):.2f})")
        elif likes_acoustic is False and song_acousticness < 0.4:
            score += self.weights.get("acoustic", 0.5)
            reasons.append(f"non-acoustic preference (+{self.weights.get('acoustic', 0.5):.2f})")

        if target_popularity is not None:
            popularity_distance = abs(song_popularity / 100.0 - float(target_popularity) / 100.0)
            popularity_score = max(0.0, 1.0 - popularity_distance)
            score += self.weights.get("popularity", 0.3) * popularity_score
            reasons.append(f"popularity fit (+{(self.weights.get('popularity', 0.3) * popularity_score):.2f})")

        if preferred_release_decade is not None:
            decade_distance = abs(song_release_decade - int(preferred_release_decade))
            decade_score = max(0.0, 1.0 - (decade_distance / 20.0))
            score += self.weights.get("release_decade", 0.2) * decade_score
            reasons.append(f"decade fit (+{(self.weights.get('release_decade', 0.2) * decade_score):.2f})")

        if preferred_mood_tags:
            overlap_count = len(set(song_mood_tags) & set(preferred_mood_tags))
            if overlap_count:
                tag_score = (overlap_count / max(1, len(preferred_mood_tags))) * self.weights.get("mood_tags", 0.4)
                score += tag_score
                reasons.append(f"mood tag overlap (+{tag_score:.2f})")

        if preferred_subgenres and song_subgenre:
            if song_subgenre in preferred_subgenres:
                score += self.weights.get("subgenre", 0.3)
                reasons.append(f"subgenre match (+{self.weights.get('subgenre', 0.3):.2f})")

        if target_instrumentalness is not None:
            instrumentalness_distance = abs(song_instrumentalness - float(target_instrumentalness))
            instrumentalness_score = max(0.0, 1.0 - instrumentalness_distance)
            score += self.weights.get("instrumentalness", 0.2) * instrumentalness_score
            reasons.append(f"instrumentalness fit (+{(self.weights.get('instrumentalness', 0.2) * instrumentalness_score):.2f})")

        return score, reasons


def _normalize_tags(value: Optional[object]) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip().lower() for item in value.replace(";", ",").split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    return []


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5, strategy_name: str = "balanced") -> List[Song]:
        """Return the top-k songs for a user, ranking them by a simple similarity score."""
        strategy = get_strategy(strategy_name)
        scored_songs = []
        for song in self.songs:
            score, reasons = strategy.score_song(_profile_to_dict(user), _song_to_dict(song))
            explanation = "; ".join(reasons) if reasons else "No specific match"
            scored_songs.append((song, score, explanation))

        scored_songs.sort(key=lambda item: item[1], reverse=True)
        adjusted = _apply_diversity_penalty(scored_songs)
        return [song for song, _, _ in adjusted[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song, strategy_name: str = "balanced") -> str:
        """Explain why a single song matches the user's profile."""
        strategy = get_strategy(strategy_name)
        score, reasons = strategy.score_song(_profile_to_dict(user), _song_to_dict(song))
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
                "popularity": int(row.get("popularity", 50)),
                "release_decade": int(row.get("release_decade", 2000)),
                "mood_tags": row.get("mood_tags", ""),
                "subgenre": row.get("subgenre", ""),
                "instrumentalness": float(row.get("instrumentalness", 0.0)),
                "lyric_density": float(row.get("lyric_density", 0.0)),
            }
        )
    return songs


def score_song(user_prefs: Dict, song: Dict, strategy_name: str = "balanced") -> Tuple[float, List[str]]:
    """Score a single song against a user profile and return the score plus reasons."""
    strategy = get_strategy(strategy_name)
    return strategy.score_song(user_prefs, song)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, strategy_name: str = "balanced") -> List[Tuple[Dict, float, str]]:
    """Score each song, rank them, and return the top-k results with explanations."""
    strategy = get_strategy(strategy_name)
    ranked = []
    for song in songs:
        score, reasons = strategy.score_song(user_prefs, song)
        explanation = "; ".join(reasons) if reasons else "No specific match"
        ranked.append((song, score, explanation))

    ranked.sort(key=lambda item: item[1], reverse=True)
    adjusted = _apply_diversity_penalty(ranked)
    return adjusted[:k]


def get_strategy(strategy_name: str = "balanced") -> ScoringStrategy:
    """Return a scoring strategy by name."""
    strategies = {
        "balanced": ScoringStrategy("balanced", "Balanced scoring across genre, mood, energy, and new features.", {"genre": 2.0, "mood": 1.0, "energy": 1.0, "acoustic": 0.5, "popularity": 0.3, "release_decade": 0.2, "mood_tags": 0.4, "subgenre": 0.3, "instrumentalness": 0.2}),
        "genre-first": ScoringStrategy("genre-first", "Prioritizes genre before mood or energy.", {"genre": 3.0, "mood": 0.8, "energy": 0.8, "acoustic": 0.3, "popularity": 0.2, "release_decade": 0.1, "mood_tags": 0.2, "subgenre": 0.3, "instrumentalness": 0.1}),
        "mood-first": ScoringStrategy("mood-first", "Prioritizes mood before genre or energy.", {"genre": 1.5, "mood": 2.0, "energy": 0.7, "acoustic": 0.4, "popularity": 0.2, "release_decade": 0.1, "mood_tags": 0.6, "subgenre": 0.2, "instrumentalness": 0.2}),
        "energy-focused": ScoringStrategy("energy-focused", "Prioritizes proximity to the target energy.", {"genre": 1.2, "mood": 0.7, "energy": 1.5, "acoustic": 0.3, "popularity": 0.25, "release_decade": 0.1, "mood_tags": 0.2, "subgenre": 0.2, "instrumentalness": 0.2}),
    }
    return strategies[strategy_name.lower()]


def _apply_diversity_penalty(ranked: List[Tuple[object, float, str]]) -> List[Tuple[object, float, str]]:
    """Reduce the score for songs whose artist or genre repeats too much in the top results."""
    adjusted = []
    seen_artists = set()
    seen_genres = set()
    for song, score, explanation in ranked:
        adjusted_score = score
        adjusted_reason = explanation

        if isinstance(song, dict):
            artist = str(song.get("artist", ""))
            genre = str(song.get("genre", ""))
        else:
            artist = str(getattr(song, "artist", ""))
            genre = str(getattr(song, "genre", ""))

        if artist in seen_artists:
            adjusted_score -= 0.8
            adjusted_reason += "; artist diversity penalty (-0.8)"
        if genre in seen_genres and artist not in seen_artists:
            adjusted_score -= 0.2
            adjusted_reason += "; genre diversity penalty (-0.2)"
        adjusted.append((song, adjusted_score, adjusted_reason))
        seen_artists.add(artist)
        seen_genres.add(genre)
    adjusted.sort(key=lambda item: item[1], reverse=True)
    return adjusted


def _profile_to_dict(profile: UserProfile) -> Dict:
    return {
        "favorite_genre": profile.favorite_genre,
        "favorite_mood": profile.favorite_mood,
        "target_energy": profile.target_energy,
        "likes_acoustic": profile.likes_acoustic,
        "target_popularity": profile.target_popularity,
        "preferred_release_decade": profile.preferred_release_decade,
        "preferred_mood_tags": profile.preferred_mood_tags,
        "preferred_subgenres": profile.preferred_subgenres,
        "likes_instrumental": profile.likes_instrumental,
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
        "popularity": song.popularity,
        "release_decade": song.release_decade,
        "mood_tags": song.mood_tags,
        "subgenre": song.subgenre,
        "instrumentalness": song.instrumentalness,
        "lyric_density": song.lyric_density,
    }
