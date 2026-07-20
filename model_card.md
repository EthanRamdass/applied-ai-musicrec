# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

---

## 2. Goal / Task  

This recommender tries to suggest songs that match a user's taste. It uses a short user profile with a favorite genre, a preferred mood, a target energy level, and an acoustic preference. The goal is to show how a simple content-based recommender turns user preferences into song rankings.

---

## 3. Algorithm Summary  

The model looks at a song's style and mood and compares it to the user's stated tastes. A song gets points for matching genre and mood, and it also gets points when its energy level is close to the user's target. It uses a simple acoustic check as well. These signals are combined into one score, and the songs with the highest scores are shown first.

---

## 4. Data Used  

The model uses a small catalog of 18 songs stored in the CSV file. I expanded the starter set with more songs to include genres and moods such as hip hop, country, classical, metal, r&b, folk, soul, and electronic. The dataset includes features like genre, mood, energy, tempo, valence, danceability, and acousticness. It is still small, so it does not capture the full range of real-world music tastes.

---

## 5. Observed Behavior / Biases  

The system works reasonably well for straightforward profiles. A user who wants pop and happy songs gets songs like Sunrise City and Gym Hero near the top, which makes sense. It also does a decent job for chill profiles, since lofi and acoustic-oriented songs rise to the top when the user prefers lower energy and more relaxed moods. One weakness is that it can over-prioritize a few songs and create a filter-bubble effect, where the same songs keep appearing even when the user profile is more unusual or conflicting.

---

## 6. Evaluation Process  

I tested the system with four user profiles in the CLI: High-Energy Pop, Chill Lofi, Deep Intense Rock, and a Conflicting Edge Case profile that mixed pop genre with a sad mood and high energy. I compared the top results from each profile and looked for whether the recommendations matched the mood and energy I expected. I also ran a small experiment to see how the ranking changed when I changed the weight of the energy signal. The biggest surprise was that some energetic songs still stayed near the top even for conflicting profiles, which showed that the current logic can be too simple for complex tastes.

---

## 7. Intended Use and Non-Intended Use  

This system is designed for small classroom demos and simple experiments with recommendation logic. It is good for showing how user preferences can be turned into ranked song suggestions. It should not be used as a real music recommendation product, because it does not learn from actual user behavior, it does not understand lyrics or context, and it cannot make deep judgments about taste.

---

## 8. Ideas for Improvement  

I would add more user signals, such as listening history, skip data, or playlist behavior. I would also improve diversity by making the system avoid showing too many similar songs at the top. Another improvement would be to make the scoring more balanced so conflicting preferences do not get overwhelmed by one feature like energy.

---

## 9. Personal Reflection  

My biggest learning moment was realizing that a recommender does not need a complicated model to feel convincing. A few simple rules can already produce recommendations that seem helpful, but they can also be surprisingly narrow or biased. Using AI tools helped me move faster by suggesting structure and code ideas, but I still had to double-check the output because the model sometimes made assumptions that did not match my project goals. I was surprised by how much a single feature like energy could change the ranking, and that made me think about how real recommendation systems balance many signals at once. If I extended this project, I would try adding more diverse songs and a more realistic scoring system based on actual listening behavior.
