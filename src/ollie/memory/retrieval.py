import chromadb
from typing import List, Dict, Any
from pathlib import Path
from .embeddings import EmbeddingService

class MemorySystem:
    def __init__(self, persist_path: str = "/data/chroma", embedding_service: EmbeddingService = None):
        """
        Initialize the RAG memory system.
        
        Args:
            persist_path: Path to store ChromaDB data
            embedding_service: Service to generate embeddings
        """
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(name="conversations")
        
        if embedding_service is None:
            self.embedding_service = EmbeddingService()
        else:
            self.embedding_service = embedding_service

    def add_memory(self, text: str, metadata: Dict[str, Any], memory_id: str):
        """
        Add a memory to the system.
        
        Args:
            text: The text content (transcript)
            metadata: Associated metadata (timestamp, speaker, session_id)
            memory_id: Unique ID for the memory
        """
        embeddings = self.embedding_service.generate_embeddings([text])
        
        self.collection.add(
            documents=[text],
            embeddings=embeddings,
            metadatas=[metadata],
            ids=[memory_id]
        )

    def search_memory(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant memories.
        
        Args:
            query: The search query
            n_results: Number of results to return
            
        Returns:
            List of results with content and metadata
        """
        query_embedding = self.embedding_service.generate_embeddings([query])
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        formatted_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
                
        return formatted_results

