"""
Test RAG embedding and semantic search system.
Tests TF-IDF embeddings and knowledge base querying.
"""

import pytest
from backend.utils.embeddings import SimpleEmbedding, KnowledgeBase


class TestSimpleEmbedding:
    """Test TF-IDF embedding system."""
    
    @pytest.mark.rag
    def test_embedding_initialization(self):
        """Test embedding system initialization."""
        embedding = SimpleEmbedding()
        assert embedding.vocabulary == {}
        assert embedding.idf_scores == {}
        assert embedding.documents == []
    
    @pytest.mark.rag
    def test_tokenization(self):
        """Test text tokenization."""
        embedding = SimpleEmbedding()
        tokens = embedding._tokenize("Hello, World! This is DRINKOO.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "drinkoo" in tokens
        assert len(tokens) == 5
    
    @pytest.mark.rag
    def test_vocabulary_building(self):
        """Test vocabulary building from documents."""
        embedding = SimpleEmbedding()
        docs = [
            "DRINKOO is a beverage company",
            "We sell sodas and juices",
            "Maharashtra is a large state"
        ]
        embedding.fit(docs)
        
        assert len(embedding.vocabulary) > 0
        assert "drinkoo" in embedding.vocabulary
        assert "beverage" in embedding.vocabulary
        assert "state" in embedding.vocabulary
    
    @pytest.mark.rag
    def test_encoding_produces_vector(self):
        """Test that encoding produces a vector."""
        embedding = SimpleEmbedding()
        docs = ["hello world", "hello there"]
        embedding.fit(docs)
        
        vector = embedding.encode("hello world")
        assert len(vector) == len(embedding.vocabulary)
        assert isinstance(vector, list)
    
    @pytest.mark.rag
    def test_vector_normalization(self):
        """Test that vectors are normalized."""
        embedding = SimpleEmbedding()
        docs = ["test document", "another test"]
        embedding.fit(docs)
        
        vector = embedding.encode("test document")
        # Calculate magnitude
        magnitude = sum(x**2 for x in vector) ** 0.5
        # Should be close to 1 (normalized)
        assert 0.9 <= magnitude <= 1.1
    
    @pytest.mark.rag
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        embedding = SimpleEmbedding()
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        
        sim_same = embedding.similarity(v1, v2)
        sim_diff = embedding.similarity(v1, v3)
        
        assert sim_same > 0.9  # Same vectors should be very similar
        assert sim_diff == 0.0  # Orthogonal vectors should have 0 similarity
    
    @pytest.mark.rag
    def test_find_similar_documents(self):
        """Test finding similar documents."""
        embedding = SimpleEmbedding()
        docs = [
            "DRINKOO has customers in Maharashtra",
            "SKU sales are increasing",
            "Shipments are pending",
            "DRINKOO serves all states"
        ]
        embedding.fit(docs)
        
        results = embedding.find_similar("How many customers in Maharashtra?", top_k=2)
        assert len(results) == 2
        assert results[0][0] == docs[0]  # Should match first doc
        assert results[0][1] > results[1][1]  # First should be more similar


class TestKnowledgeBase:
    """Test RAG knowledge base."""
    
    @pytest.mark.rag
    def test_kb_initialization(self):
        """Test knowledge base initialization."""
        kb = KnowledgeBase()
        assert kb.qa_pairs == []
        assert not kb.is_fitted
    
    @pytest.mark.rag
    def test_add_qa_pair(self):
        """Test adding QA pairs."""
        kb = KnowledgeBase()
        kb.add_qa("What is DRINKOO?", "DRINKOO is a beverage company", tags=["company"])
        
        assert len(kb.qa_pairs) == 1
        assert kb.qa_pairs[0]["question"] == "What is DRINKOO?"
        assert kb.qa_pairs[0]["tags"] == ["company"]
    
    @pytest.mark.rag
    def test_kb_fitting(self):
        """Test knowledge base fitting."""
        kb = KnowledgeBase()
        kb.add_qa("How many customers?", "We have 1000 customers", tags=["customers"])
        kb.add_qa("What states?", "We serve all 36 states", tags=["states"])
        kb.fit()
        
        assert kb.is_fitted
        assert len(kb.embedding.vocabulary) > 0
    
    @pytest.mark.rag
    def test_kb_query(self):
        """Test querying knowledge base."""
        kb = KnowledgeBase()
        kb.add_qa("How many customers are in Maharashtra?", "Maharashtra has 100 customers", tags=["customers"])
        kb.add_qa("Which SKU is best?", "Cola is our top SKU", tags=["sku"])
        kb.fit()
        
        results = kb.query("customers in Maharashtra", top_k=2)
        assert len(results) > 0
        assert results[0]["similarity"] > 0.3
    
    @pytest.mark.rag
    def test_kb_summary(self):
        """Test knowledge base summary."""
        kb = KnowledgeBase()
        kb.add_qa("Q1", "A1", tags=["customers", "state"])
        kb.add_qa("Q2", "A2", tags=["customers"])
        kb.fit()
        
        summary = kb.get_kb_summary()
        assert summary["total_qa_pairs"] == 2
        assert summary["is_fitted"]
        assert "customers" in summary["categories"]


class TestDrinkooRAG:
    """Test DRINKOO-specific RAG pipeline."""
    
    @pytest.mark.rag
    def test_rag_initialization(self):
        """Test RAG pipeline initialization."""
        from backend.utils.rag import DrinkooRAG
        rag = DrinkooRAG()
        assert rag.kb.is_fitted
        assert rag.kb.get_kb_summary()["total_qa_pairs"] > 0
    
    @pytest.mark.rag
    def test_rag_instance_singleton(self):
        """Test that RAG instance is singleton."""
        from backend.utils.rag import get_rag_pipeline
        rag1 = get_rag_pipeline()
        rag2 = get_rag_pipeline()
        assert rag1 is rag2
    
    @pytest.mark.rag
    def test_state_extraction(self):
        """Test state code extraction from questions."""
        from backend.utils.rag import DrinkooRAG
        from backend.database.db import get_db
        
        db = get_db()
        rag = DrinkooRAG()
        
        state = rag._extract_state("How many customers in Maharashtra?", db)
        assert state == "MH"
        
        state = rag._extract_state("Random question", db)
        assert state is None
    
    @pytest.mark.rag
    def test_rag_query_response_structure(self):
        """Test that RAG query returns expected structure."""
        from backend.utils.rag import get_rag_pipeline
        rag = get_rag_pipeline()
        
        result = rag.query("What is DRINKOO?")
        assert "answer" in result
        assert "source" in result
        assert "confidence" in result
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0


class TestEmbeddingPerformance:
    """Test embedding system performance."""
    
    @pytest.mark.rag
    def test_large_vocabulary(self):
        """Test embedding with large vocabulary."""
        embedding = SimpleEmbedding()
        docs = [f"Document about topic {i}" for i in range(100)]
        embedding.fit(docs)
        
        assert len(embedding.vocabulary) > 100
        vector = embedding.encode("Document about topic 50")
        assert len(vector) == len(embedding.vocabulary)
    
    @pytest.mark.rag
    def test_similarity_range(self):
        """Test that similarity scores are in valid range."""
        embedding = SimpleEmbedding()
        docs = ["test"] * 10
        embedding.fit(docs)
        
        results = embedding.find_similar("test", top_k=5)
        for _, sim in results:
            assert 0.0 <= sim <= 1.0
