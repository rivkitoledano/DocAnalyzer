
# ============================================================================
# rag_system.py - מערכת RAG (זהה)
# ============================================================================

import logging
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
class RAGSystem:
    """מערכת RAG עם FAISS"""
    
    def __init__(self, model_path: str):
        logging.info(f"טוען מודל embedding: {model_path}")
        self.model = SentenceTransformer(model_path)
        self.texts: List[str] = []
        self.metadata: List[dict] = []
        self.index = None
    
    def build_index(self, texts: List[str], metadata: List[dict] = None):
        self.texts = texts
        self.metadata = metadata or [{'index': i} for i in range(len(texts))]
        
        logging.info("יוצר embeddings...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(embeddings))
        
        logging.info(f"✓ אינדקס FAISS נבנה עם {self.index.ntotal} chunks\n")
    
    def query(self, question: str, k: int = 7) -> List[Tuple[str, dict, float]]:
        if self.index is None:
            raise ValueError("Index not built")
        
        q_emb = self.model.encode([question])
        distances, ids = self.index.search(np.array(q_emb), k)
        
        results = []
        for dist, idx in zip(distances[0], ids[0]):
            results.append((self.texts[idx], self.metadata[idx], float(dist)))
        
        return results
    
    def query_as_context(self, question: str, k: int = 3) -> str:
        results = self.query(question, k)
        
        context = "סעיפים רלוונטיים:\n\n"
        for i, (text, meta, dist) in enumerate(results, 1):
            context += f"--- סעיף {i} ---\n{text}\n\n"
        
        return context

