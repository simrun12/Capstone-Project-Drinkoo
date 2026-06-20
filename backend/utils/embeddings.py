"""
Vector embeddings and semantic search utilities for DRINKOO RAG chatbot.
Uses TF-IDF for lightweight semantic similarity without external ML dependencies.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import List, Tuple


class SimpleEmbedding:
    """
    Lightweight TF-IDF based embedding system for semantic search.
    No external ML library required - pure Python implementation.
    """

    def __init__(self):
        """Initialize the embedding system."""
        self.vocabulary: dict[str, int] = {}
        self.idf_scores: dict[str, float] = {}
        self.documents: list[str] = []
        self.vocab_id = 0

    def _tokenize(self, text: str) -> list[str]:
        """Convert text to lowercase tokens."""
        text = text.lower()
        # Remove punctuation, split by whitespace
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def fit(self, documents: list[str]) -> None:
        """
        Build vocabulary and compute IDF scores from documents.
        
        Args:
            documents: List of text documents to learn from
        """
        self.documents = documents
        doc_count = len(documents)
        doc_word_counts: dict[str, int] = Counter()

        # Build vocabulary and count document frequency
        for doc in documents:
            tokens = set(self._tokenize(doc))  # Use set to count doc frequency, not term frequency
            for token in tokens:
                if token not in self.vocabulary:
                    self.vocabulary[token] = self.vocab_id
                    self.vocab_id += 1
                doc_word_counts[token] += 1

        # Compute IDF scores (log of inverse document frequency)
        for word, doc_freq in doc_word_counts.items():
            # IDF = log(total_docs / docs_containing_term)
            self.idf_scores[word] = math.log(doc_count / doc_freq) if doc_freq > 0 else 0.0

    def encode(self, text: str) -> list[float]:
        """
        Convert text to TF-IDF vector.
        
        Args:
            text: Text to encode
            
        Returns:
            Vector of TF-IDF scores for vocabulary
        """
        tokens = self._tokenize(text)
        term_freq = Counter(tokens)
        
        vector = [0.0] * len(self.vocabulary)
        
        # Create TF-IDF vector
        for token, freq in term_freq.items():
            if token in self.vocabulary:
                vocab_idx = self.vocabulary[token]
                tf = freq / len(tokens) if tokens else 0
                idf = self.idf_scores.get(token, 0.0)
                vector[vocab_idx] = tf * idf
        
        # Normalize vector
        magnitude = math.sqrt(sum(x**2 for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        
        return vector

    def similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score between 0 and 1
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, dot_product))

    def find_similar(self, query: str, top_k: int = 5) -> list[Tuple[str, float]]:
        """
        Find most similar documents to query.
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of (document, similarity) tuples sorted by similarity
        """
        query_vec = self.encode(query)
        
        similarities: list[Tuple[str, float]] = []
        for doc in self.documents:
            doc_vec = self.encode(doc)
            sim = self.similarity(query_vec, doc_vec)
            similarities.append((doc, sim))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class KnowledgeBase:
    """
    Knowledge base for DRINKOO chatbot with semantic search capability.
    """

    def __init__(self):
        """Initialize knowledge base."""
        self.embedding = SimpleEmbedding()
        self.qa_pairs: list[dict] = []
        self.is_fitted = False

    def add_qa(self, question: str, answer: str, tags: list[str] | None = None) -> None:
        """
        Add a question-answer pair to the knowledge base.
        
        Args:
            question: Sample question
            answer: Answer to the question
            tags: Optional tags for categorization
        """
        self.qa_pairs.append({
            "question": question,
            "answer": answer,
            "tags": tags or []
        })

    def fit(self) -> None:
        """Build embeddings from QA pairs."""
        if not self.qa_pairs:
            return
        
        # Fit embeddings on all questions
        questions = [qa["question"] for qa in self.qa_pairs]
        self.embedding.fit(questions)
        self.is_fitted = True

    def query(self, question: str, top_k: int = 3) -> list[dict]:
        """
        Find most relevant answers to a question.
        
        Args:
            question: User question
            top_k: Number of results to return
            
        Returns:
            List of relevant QA pairs with similarity scores
        """
        if not self.is_fitted:
            return []
        
        similarities = self.embedding.find_similar(question, top_k=top_k)
        results = []
        
        for question_text, similarity in similarities:
            # Find the corresponding QA pair
            for qa in self.qa_pairs:
                if qa["question"] == question_text:
                    results.append({
                        "question": qa["question"],
                        "answer": qa["answer"],
                        "tags": qa["tags"],
                        "similarity": round(similarity, 3)
                    })
                    break
        
        return results

    def get_kb_summary(self) -> dict:
        """Get summary of knowledge base."""
        tags_count: dict[str, int] = Counter()
        for qa in self.qa_pairs:
            for tag in qa["tags"]:
                tags_count[tag] += 1
        
        return {
            "total_qa_pairs": len(self.qa_pairs),
            "categories": dict(tags_count),
            "is_fitted": self.is_fitted
        }
