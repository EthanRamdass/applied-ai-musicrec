# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

My design is a simple content-based recommender. It uses song attributes to estimate whether a track fits a user's taste profile. In real-world systems, platforms such as Spotify or TikTok combine many signals, including listening history, skips, likes, and playlist behavior, but this simulation keeps the logic simple and transparent.

In this version, each `Song` uses attributes like `genre`, `mood`, `energy`, `tempo_bpm`, `valence`, `danceability`, and `acousticness` to describe its style and feel. The `UserProfile` stores a small set of preferences, such as the user's favorite genre, favorite mood, target energy, and whether they prefer acoustic songs. The `Recommender` then compares every song to that profile and assigns it a score based on how well it matches.

My algorithm recipe is:

- `+2.0` points for a genre match
- `+1.0` point for a mood match
- `+1.0` point if the song's energy is close to the user's target energy
- `+0.5` points if the song matches the user's acoustic preference
- `+0.25` points for additional similarity in `valence` or `danceability` when relevant

The scoring rule evaluates one song at a time, while the ranking rule sorts the full list of songs from highest score to lowest score and returns the top $k$ recommendations. This separation matters because the scoring rule answers "How well does this one song match?" while the ranking rule answers "Which songs should appear first in the final list?"

A simple flow for the design is:

Input (User Prefs) → Process (Score each song in the CSV) → Output (Rank and return the top $k$ songs)

I expect this system to have some bias. Because it strongly favors genre and mood, it could over-recommend songs that are similar in style while missing enjoyable songs that fit the user's mood in a less obvious way. That is a common limitation of simple content-based recommender systems.


---

## Data Expansion and Example User Profile

I expanded the starter catalog in [data/songs.csv](data/songs.csv) with eight new songs that add genres and moods not already present in the original sample, such as hip hop, country, classical, metal, r&b, folk, soul, and electronic.

A useful prompt for generating more rows in the same CSV format is:

```text
Generate 8 additional songs for a music recommender dataset in valid CSV format.
Use the same headers as the existing file: id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness.
Create songs from genres and moods that are not already represented in the starter data, such as hip hop, country, classical, metal, r&b, folk, soul, or electronic.
Keep the values realistic and make sure the numerical columns stay within a sensible range.
```

A sample user profile for the recommender could look like this:

```python
user_profile = {
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.75,
    "likes_acoustic": False,
}
```

This profile is useful because it lets the recommender distinguish between energetic and upbeat songs versus more relaxed songs, while still leaving room for variety across the expanded catalog.
---

## Getting Started



### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

The CLI now prints a ranked list of recommendations for the default profile using the scoring logic implemented in [src/recommender.py](src/recommender.py):

```text
Loaded songs: 18

Top recommendations:

Sunrise City - Score: 4.48
Because: genre match (+2.0); mood match (+1.0); energy similarity (+0.98); non-acoustic preference (+0.5)

Gym Hero - Score: 3.37
Because: genre match (+2.0); energy similarity (+0.87); non-acoustic preference (+0.5)

Rooftop Lights - Score: 2.46
Because: mood match (+1.0); energy similarity (+0.96); non-acoustic preference (+0.5)

Neon Harbor - Score: 1.49
Because: energy similarity (+0.99); non-acoustic preference (+0.5)

Circuit Bloom - Score: 1.47
Because: energy similarity (+0.97); non-acoustic preference (+0.5)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



