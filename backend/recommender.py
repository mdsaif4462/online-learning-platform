"""Content-based course recommender (TF-IDF + cosine similarity)."""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class CourseRecommender:
    def __init__(self, courses: pd.DataFrame):
        self.df = courses.reset_index(drop=True)
        self.ready = len(self.df) > 1
        if not self.ready:
            return

        # Title, category and tags carry more signal than the long description,
        # so they are repeated to give them extra weight in the TF-IDF space.
        text = (
            (self.df["title"] + " ") * 2
            + (self.df["category"] + " ") * 2
            + (self.df["tags"] + " ") * 2
            + self.df["description"]
        )
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(text)
        self.similarity = cosine_similarity(self.matrix)
        self.position = {cid: i for i, cid in enumerate(self.df["id"])}

    def similar_to(self, course_id, n=4):
        """Course ids most similar to a single course."""
        if not self.ready or course_id not in self.position:
            return []
        scores = self.similarity[self.position[course_id]].copy()
        scores[self.position[course_id]] = -1
        return self._top(scores, n)

    def for_user(self, enrolled_ids, n=6):
        """Course ids that best match everything the user is enrolled in."""
        rows = [self.position[c] for c in enrolled_ids if c in self.position]
        if not self.ready or not rows:
            return []
        scores = np.asarray(self.similarity[rows].mean(axis=0)).ravel()
        scores[rows] = -1  # never recommend what they already have
        return self._top(scores, n)

    def _top(self, scores, n):
        order = np.argsort(scores)[::-1]
        return [int(self.df["id"].iloc[i]) for i in order[:n] if scores[i] > 0]
