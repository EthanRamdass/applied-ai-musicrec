"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import textwrap

try:
    from src.recommender import load_songs, recommend_songs, get_strategy
except ImportError:  # pragma: no cover - fallback for direct script execution
    from recommender import load_songs, recommend_songs, get_strategy


def _print_recommendations(label: str, user_prefs: dict, songs: list, k: int = 5, strategy_name: str = "balanced") -> None:
    print(f"\n=== {label} [{strategy_name}] ===")
    recommendations = recommend_songs(user_prefs, songs, k=k, strategy_name=strategy_name)

    headers = ["Rank", "Title", "Score", "Reason"]
    rows = []
    for index, rec in enumerate(recommendations, start=1):
        song, score, explanation = rec
        reason_text = textwrap.shorten(explanation, width=90, placeholder="...")
        rows.append((str(index), song["title"], f"{score:.2f}", reason_text))

    widths = [max(len(header), *(len(row[i]) for row in rows)) for i, header in enumerate(headers)]
    header_line = " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
    divider = "-+-".join("-" * width for width in widths)
    print(header_line)
    print(divider)
    for row in rows:
        print(" | ".join(value.ljust(widths[i]) for i, value in enumerate(row)))
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    profiles = [
        ("High-Energy Pop", {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}),
        ("Chill Lofi", {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True}),
        ("Deep Intense Rock", {"genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False}),
        ("Conflicting Edge Case", {"genre": "pop", "mood": "sad", "energy": 0.9, "likes_acoustic": False}),
    ]

    strategies = ["balanced", "genre-first", "mood-first", "energy-focused"]

    for label, user_prefs in profiles:
        for strategy_name in strategies:
            _print_recommendations(label, user_prefs, songs, k=5, strategy_name=strategy_name)


if __name__ == "__main__":
    main()
