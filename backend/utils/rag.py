"""
RAG (Retrieval-Augmented Generation) pipeline for DRINKOO chatbot.
Combines vector similarity search with SQLite-backed company data.
"""

from __future__ import annotations

from typing import Optional

from .embeddings import KnowledgeBase
from ..database.db import get_db


class DrinkooRAG:
    """
    RAG pipeline that grounds chatbot responses in DRINKOO data.
    Uses semantic search + database queries for accurate answers.
    """

    def __init__(self):
        """Initialize RAG pipeline."""
        self.kb = KnowledgeBase()
        self._build_knowledge_base()

    def _build_knowledge_base(self) -> None:
        """Build knowledge base with DRINKOO-specific QA pairs."""
        # Questions about customers
        self.kb.add_qa(
            "How many customers does DRINKOO have in this state?",
            "DRINKOO customer base is growing! Use the state selector to see customer counts.",
            tags=["customers", "state", "data"]
        )
        
        # Questions about SKUs
        self.kb.add_qa(
            "What are the available drink SKUs?",
            "DRINKOO offers 50 unique SKUs including sodas, juices, energy drinks, and more.",
            tags=["sku", "products"]
        )
        
        self.kb.add_qa(
            "Which SKU is performing best in sales?",
            "The top-performing SKU varies by state. Check the sales analytics to see regional trends.",
            tags=["sku", "sales", "analytics"]
        )
        
        # Questions about shipments
        self.kb.add_qa(
            "How can I track a shipment?",
            "Enter your tracking code (format: DRINKOO-YYYYMMDDHHMMSS-XXXXXX) in the shipments view to track delivery status.",
            tags=["shipment", "tracking"]
        )
        
        self.kb.add_qa(
            "What shipment statuses exist?",
            "Shipments have 4 statuses: pending (awaiting pickup), in_transit (on the way), delivered (completed), and failed.",
            tags=["shipment", "status"]
        )
        
        # Questions about company info
        self.kb.add_qa(
            "What is DRINKOO?",
            "DRINKOO is a beverage distribution company serving across all 36 Indian states and UTs with quality drinks and efficient logistics.",
            tags=["company", "info"]
        )
        
        self.kb.add_qa(
            "Which states does DRINKOO serve?",
            "DRINKOO operates across all 36 Indian states and union territories with a distributed customer base.",
            tags=["states", "coverage"]
        )
        
        # Questions about system
        self.kb.add_qa(
            "How do I create a new SKU?",
            "Use the SKUs view to create new products. SKUs must be 1000ml or 1500ml in size per DRINKOO standards.",
            tags=["sku", "create", "system"]
        )
        
        self.kb.add_qa(
            "How do I create a shipment?",
            "Go to the Shipments view, select a state, choose a SKU, enter quantity and cost, then click Create Shipment.",
            tags=["shipment", "create", "system"]
        )
        
        # Fit embeddings after adding all QAs
        self.kb.fit()

    def query(self, question: str) -> dict:
        """
        Process a user question and return grounded answer with sources.
        
        Args:
            question: User question
            
        Returns:
            Dictionary with answer, confidence, and sources
        """
        # Get semantically similar QAs from knowledge base
        kb_results = self.kb.query(question, top_k=3)
        
        # Query company data based on question intent
        db_answer = self._query_database(question)
        
        # Combine results
        if db_answer:
            return {
                "answer": db_answer["answer"],
                "source": "DRINKOO database",
                "confidence": "high",
                "kb_context": kb_results[0] if kb_results else None
            }
        elif kb_results and kb_results[0]["similarity"] > 0.3:
            # Use knowledge base if similarity is decent
            return {
                "answer": kb_results[0]["answer"],
                "source": "Knowledge base",
                "confidence": "medium",
                "similar_questions": kb_results
            }
        else:
            # Fallback response
            return {
                "answer": (
                    "I'm not sure about that. I can help with questions about "
                    "customer counts by state, SKU performance, shipment tracking, and DRINKOO operations."
                ),
                "source": "Default response",
                "confidence": "low",
                "suggestions": ["How many customers in Maharashtra?", "Which SKU is top seller?", "Track shipment"]
            }

    def _query_database(self, question: str) -> Optional[dict]:
        """
        Query DRINKOO database based on question intent.
        
        Args:
            question: User question
            
        Returns:
            Answer dict if database query successful, None otherwise
        """
        db = get_db()
        lower_q = question.lower()
        
        # Extract state if mentioned
        state_code = self._extract_state(question, db)
        
        # Question: How many customers...
        if "customer" in lower_q and "how many" in lower_q:
            if state_code:
                count = db.fetch_scalar(
                    "SELECT COUNT(*) FROM customers WHERE state_code = ?",
                    (state_code,)
                )
                state_name = db.fetch_scalar(
                    "SELECT state_name FROM states WHERE state_code = ?",
                    (state_code,)
                )
                return {
                    "answer": f"{state_name} has {count} DRINKOO customers in the current dataset.",
                    "state": state_code
                }
            else:
                count = db.fetch_scalar("SELECT COUNT(*) FROM customers")
                return {
                    "answer": f"DRINKOO has {count} customers across all states."
                }
        
        # Question: Top SKU / Best seller
        if ("top" in lower_q or "best" in lower_q or "popular" in lower_q) and "sku" in lower_q:
            state_clause = "WHERE sales.state_code = ?" if state_code else ""
            params = (state_code,) if state_code else ()
            
            top_sku = db.fetch_one(
                f"""
                SELECT
                    skus.sku_name,
                    skus.flavor_profile,
                    COUNT(DISTINCT sales.sale_id) as sale_count,
                    COALESCE(SUM(sales.quantity_sold), 0) as total_qty,
                    COALESCE(SUM(sales.revenue), 0) as total_revenue
                FROM sales
                JOIN skus ON skus.sku_id = sales.sku_id
                {state_clause}
                GROUP BY skus.sku_id
                ORDER BY total_qty DESC, total_revenue DESC
                LIMIT 1
                """,
                params
            )
            
            if top_sku:
                scope = f"in {state_code}" if state_code else "across all states"
                return {
                    "answer": (
                        f"The top DRINKOO SKU {scope} is {top_sku['sku_name']} "
                        f"({top_sku['flavor_profile']}) with {top_sku['total_qty']} units sold "
                        f"generating ₹{int(top_sku['total_revenue'])} revenue across {top_sku['sale_count']} sales."
                    )
                }
        
        # Question: Pending shipments
        if "pending" in lower_q and ("shipment" in lower_q or "delivery" in lower_q):
            if state_code:
                count = db.fetch_scalar(
                    "SELECT COUNT(*) FROM shipments WHERE state_code = ? AND status = 'pending'",
                    (state_code,)
                )
                return {
                    "answer": f"{state_code} has {count} pending DRINKOO shipments awaiting delivery."
                }
            else:
                count = db.fetch_scalar("SELECT COUNT(*) FROM shipments WHERE status = 'pending'")
                return {
                    "answer": f"DRINKOO has {count} pending shipments across all states."
                }
        
        # Question: Shipment statuses / status distribution
        if "shipment" in lower_q and ("status" in lower_q or "distribution" in lower_q):
            status_dist = db.fetch_all(
                """
                SELECT status, COUNT(*) as count
                FROM shipments
                GROUP BY status
                ORDER BY count DESC
                """
            )
            
            if status_dist:
                status_text = ", ".join(f"{s['status']}: {s['count']}" for s in status_dist)
                return {
                    "answer": f"Current DRINKOO shipment distribution: {status_text}"
                }
        
        # Question: SKU sizes / offerings
        if "sku" in lower_q and ("size" in lower_q or "ml" in lower_q):
            return {
                "answer": "DRINKOO SKUs come in 1000ml and 1500ml sizes only, ensuring consistency and quality standards."
            }
        
        # Question: Total statistics
        if "total" in lower_q or "summary" in lower_q or "statistics" in lower_q:
            customers = db.fetch_scalar("SELECT COUNT(*) FROM customers")
            skus = db.fetch_scalar("SELECT COUNT(*) FROM skus WHERE status = 'active'")
            shipments = db.fetch_scalar("SELECT COUNT(*) FROM shipments")
            revenue = db.fetch_scalar("SELECT COALESCE(SUM(revenue), 0) FROM sales")
            
            return {
                "answer": (
                    f"DRINKOO Summary: {customers} customers, {skus} active SKUs, "
                    f"{shipments} total shipments, ₹{int(revenue)} total revenue."
                )
            }
        
        return None

    def _extract_state(self, question: str, db) -> Optional[str]:
        """Extract state code from question if mentioned."""
        import re
        lower_q = question.lower()
        states = db.fetch_all("SELECT state_code, state_name FROM states")

        for state in states:
            if state["state_name"].lower() in lower_q:
                return state["state_code"]

        for state in states:
            pattern = r"\b" + re.escape(state["state_code"].lower()) + r"\b"
            if re.search(pattern, lower_q):
                return state["state_code"]

        return None

    def get_kb_info(self) -> dict:
        """Get knowledge base information."""
        return self.kb.get_kb_summary()


# Global RAG instance
_rag_instance: Optional[DrinkooRAG] = None


def get_rag_pipeline() -> DrinkooRAG:
    """Get or create RAG pipeline instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = DrinkooRAG()
    return _rag_instance
