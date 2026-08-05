# RAG Architecture — Music Recommender

This document describes the Retrieval-Augmented Generation (RAG) layer that turns
the deterministic content-based recommender into a conversational one. The
implementation lives in [`src/rag.py`](../src/rag.py); the retrieval half reuses
the existing scorer/ranker in [`src/recommender.py`](../src/recommender.py).

## Pipeline

1. **Understand** — Gemini parses a free-text request into a structured `UserProfile`.
2. **Retrieve** — the existing recommender scores + ranks `data/songs.csv` and returns the top-k songs (the grounding data).
3. **Generate** — Gemini writes a conversational recommendation grounded **only** in the retrieved songs, so it can never invent a track outside the catalog.

## Diagram

```mermaid
flowchart TD
    User["👤 User<br/>natural-language request<br/>e.g. 'upbeat gym music, nothing acoustic'"]

    subgraph Parse["1 · Understand the request"]
        LLM_Parse["Gemini (gemini-3.5-flash)<br/>parse free text → structured UserProfile<br/>favorite_genre, favorite_mood,<br/>target_energy, likes_acoustic"]
    end

    subgraph Retrieve["2 · Retrieve (existing recommender)"]
        CSV[("data/songs.csv<br/>song catalog")]
        Scorer["ScoringStrategy.score_song<br/>weighted content-based match"]
        Ranker["recommend_songs<br/>rank + diversity penalty<br/>→ top-k songs"]
        CSV --> Scorer --> Ranker
    end

    subgraph Generate["3 · Generate (grounded)"]
        Context["Build grounding context<br/>ONLY the top-k retrieved songs<br/>+ their scores & reasons"]
        LLM_Gen["Gemini (gemini-3.5-flash)<br/>write conversational recommendation<br/>grounded in retrieved songs only"]
        Context --> LLM_Gen
    end

    Answer["💬 Grounded answer<br/>natural-language picks<br/>with human-readable 'why'"]

    User --> LLM_Parse
    LLM_Parse -->|UserProfile| Ranker
    Ranker -->|top-k songs| Context
    LLM_Gen --> Answer

    %% Guardrail note
    Guard{{"🛡 Guardrail:<br/>model may only recommend<br/>songs present in the retrieved set —<br/>no hallucinated tracks"}}
    Context -.-> Guard
    Guard -.-> LLM_Gen

    classDef llm fill:#2d6cdf,stroke:#1b3f85,color:#fff;
    classDef data fill:#e8a33d,stroke:#8a5a12,color:#111;
    classDef io fill:#3ba36b,stroke:#1c5a38,color:#fff;
    classDef guard fill:#c0392b,stroke:#7b241c,color:#fff;
    class LLM_Parse,LLM_Gen llm;
    class CSV,Scorer,Ranker data;
    class User,Answer io;
    class Guard guard;
```

> Rendered automatically on GitHub. To export locally: `mmdc -i ../diagrams/rag_architecture.mmd -o rag_architecture.svg`
