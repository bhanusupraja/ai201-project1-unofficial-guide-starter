"""
Embedding Module: Convert chunks to embeddings and store in vector database.

Strategy from planning.md:
- Model: all-MiniLM-L6-v2 (sentence-transformers)
- Vector store: ChromaDB
- Metadata: source, chunk_id, sequence number
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages embedding model and vector store operations."""
    
    # From planning.md spec
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    def __init__(self, persist_dir: str = "chroma_db"):
        """
        Initialize the embedding manager.
        
        Args:
            persist_dir: Directory for ChromaDB persistence
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(exist_ok=True)
        
        # Load embedding model
        logger.info(f"Loading embedding model: {self.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(self.EMBEDDING_MODEL)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = None
        
        logger.info(f"Initialized ChromaDB at {self.persist_dir}")
    
    def create_collection(self, collection_name: str = "unofficial_guide") -> chromadb.Collection:
        """
        Create or get a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            ChromaDB collection
        """
        # Delete existing collection if it exists (for fresh start)
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted existing collection: {collection_name}")
        except:
            pass
        
        # Create new collection
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )
        logger.info(f"Created collection: {collection_name}")
        
        return self.collection
    
    def embed_chunks(self, chunks: List[Dict]) -> List[List[float]]:
        """
        Embed a list of chunks.
        
        Args:
            chunks: List of chunk dicts with 'text' field
        
        Returns:
            List of embeddings (vectors)
        """
        texts = [chunk["text"] for chunk in chunks]
        logger.info(f"Embedding {len(texts)} chunks...")
        
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def add_chunks_to_collection(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
        collection_name: str = "unofficial_guide"
    ):
        """
        Add chunks and embeddings to the collection.
        
        Args:
            chunks: List of chunk dicts
            embeddings: List of embedding vectors
            collection_name: Name of the collection
        """
        if not self.collection:
            self.create_collection(collection_name)
        
        # Prepare data for ChromaDB
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Add to collection
        logger.info(f"Adding {len(chunks)} chunks to collection...")
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        
        logger.info(f"Successfully added {len(chunks)} chunks to collection")
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        if not self.collection:
            return {"status": "No collection loaded"}
        
        count = self.collection.count()
        
        return {
            "collection_name": self.collection.name,
            "total_chunks": count,
            "embedding_model": self.EMBEDDING_MODEL,
            "vector_db": "ChromaDB",
            "similarity_metric": "cosine",
        }
    
    def get_collection(self, collection_name: str = "unofficial_guide"):
        """Get an existing collection."""
        self.collection = self.client.get_collection(name=collection_name)
        logger.info(f"Loaded collection: {collection_name}")
        return self.collection


class RetrieverQuery:
    """Wrapper for retrieval queries with metadata."""
    
    def __init__(
        self,
        query_text: str,
        query_embedding: List[float],
        distance: float,
        chunk_text: str,
        source: str,
        chunk_id: str,
        rank: int
    ):
        self.query_text = query_text
        self.query_embedding = query_embedding
        self.distance = distance
        self.chunk_text = chunk_text
        self.source = source
        self.chunk_id = chunk_id
        self.rank = rank
    
    def __repr__(self):
        return (
            f"RetrieverResult(rank={self.rank}, distance={self.distance:.3f}, "
            f"source={self.source}, chunk_id={self.chunk_id})"
        )


class Retriever:
    """Retrieves chunks from vector store."""
    
    # From planning.md spec
    DEFAULT_TOP_K = 8
    
    def __init__(self, embedding_manager: EmbeddingManager):
        """
        Initialize retriever.
        
        Args:
            embedding_manager: EmbeddingManager instance with loaded collection
        """
        self.embedding_manager = embedding_manager
        self.model = embedding_manager.model
    
    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        distance_threshold: float = None
    ) -> List[Dict]:
        """
        Retrieve top-k most similar chunks for a query.
        
        Args:
            query: Query text
            top_k: Number of chunks to retrieve
            distance_threshold: Optional threshold for filtering results (higher = less similar)
        
        Returns:
            List of retrieved chunks with scores and metadata
        """
        if not self.embedding_manager.collection:
            logger.error("No collection loaded!")
            return []
        
        # Embed the query
        query_embedding = self.model.encode(query)
        
        # Query the collection
        logger.info(f"Retrieving top-{top_k} chunks for query: '{query}'")
        
        results = self.embedding_manager.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=["embeddings", "documents", "metadatas", "distances"]
        )
        
        # Format results
        retrieved_chunks = []
        
        if results and results["documents"] and len(results["documents"]) > 0:
            for i, (doc, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ):
                # ChromaDB uses cosine distance (lower is better)
                # Convert distance to similarity score (0-1, higher is better)
                similarity = 1 - distance
                
                # Optional: filter by threshold
                if distance_threshold and distance > distance_threshold:
                    logger.warning(
                        f"Result {i+1}: distance={distance:.3f} exceeds threshold "
                        f"{distance_threshold} - skipping"
                    )
                    continue
                
                chunk = {
                    "rank": i + 1,
                    "text": doc,
                    "distance": distance,
                    "similarity": similarity,
                    "source": metadata.get("source", "unknown"),
                    "source_type": metadata.get("source_type", "unknown"),
                    "chunk_id": metadata.get("chunk_id", "unknown"),
                    "metadata": metadata,
                }
                retrieved_chunks.append(chunk)
        
        return retrieved_chunks
    
    def retrieve_with_details(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K
    ) -> tuple:
        """
        Retrieve chunks with formatted details for display.
        
        Returns:
            (query, chunks, query_embedding)
        """
        query_embedding = self.model.encode(query)
        chunks = self.retrieve(query, top_k)
        
        return query, chunks, query_embedding
